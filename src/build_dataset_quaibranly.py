"""
Layer 1 — metadata de Quai Branly, tal cual la da ccProxy.ashx.

Lee data/raw/quaibranly_objects_raw.json (snapshot crudo, ver
fetch_quaibranly.py) y escribe data/processed/quaibranly_objects.csv. Mismo
principio que build_dataset_louvre.py/build_dataset.py: no interpreta ni
geocodifica nada, solo aplana los campos del registro a un CSV con las mismas
columnas que usan los otros 3 museos. La interpretación geográfica vive en
build_geography_quaibranly.py (layer 2).

Shape de datos particular de Quai Branly (ver fetch_quaibranly.py y
CLAUDE.md para más detalle): el registro es mucho más estructurado que el
texto libre del Louvre/BM -- `Country`/`Toponyme`/`Ethnonyme` son términos de
un thesaurus controlado (a veces dict, a veces list si el objeto tiene más
de un valor asociado; se usa siempre el primero). `ConXother` es un campo de
procedencia/adquisición ya estructurado (actor + tipo de rol + fecha) que
ningún otro de los 3 museos expone tan directamente -- se usa acá para
reconstruir un `creditLine` aproximado cuando el campo `Creditline` en texto
libre no está poblado (la mayoría de los casos).

Imagen (corregido 31/08, segunda vuelta): el campo `Image`/`ImagesMoreObj`
trae `Cheminmedia` (un path UNC de Windows interno, no servible) pero
también `image2`, una ruta relativa con backslashes (ej.
`Objets\Images\001\1624.jpg`) que SÍ resulta ser el parámetro `filename` real
del proxy de imágenes público del sitio, encontrado inspeccionando el
tráfico de red de `collections.quaibranly.fr` en el navegador conectado:
`https://collections.quaibranly.fr/cc/imageproxy.ashx?server=localhost&port=15012&filename=<image2 con / en vez de \>&cache=yes`.
Sin `width`/`height` devuelve la imagen a resolución completa (confirmado
contra dos piezas reales, 2240x1488 y 1488x2240) -- con esos parámetros el
proxy recorta/letterboxea a un thumbnail, así que se omiten a propósito.
`_primary_image()` usa `Image.image2` si está poblado, si no el primer
`ImagesMoreObj` (ordenado por `rank`) como fallback. De las 200 piezas de
esta corrida, 195 tienen `Image` y quedan con URL; las 5 restantes no tienen
ningún campo de imagen en absoluto en el registro crudo (ni `Image` ni
`ImagesMoreObj`) -- mismo tratamiento que "sin imagen" ya usado para Met/BM,
`primaryImage` queda `None` para esas, no inventado. `objectURL` sí era real
desde el principio: la SPA usa rutas hash (`#/objet/<id>`).

Uso:
    python src/build_dataset_quaibranly.py
"""

import csv
import json
from pathlib import Path
from urllib.parse import quote

from museum_id import QUAI_BRANLY, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "quaibranly_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "quaibranly_objects.csv"

FIELDS = [
    "objectID", "sourceMuseum", "sourceObjectID", "title", "objectName", "department",
    "culture", "period", "objectDate", "medium", "creditLine", "accessionYear",
    "excavation", "placeOfCreation", "placeOfDiscovery", "provenance",
    "primaryImage", "objectURL",
]

OBJECT_URL_TMPL = "https://collections.quaibranly.fr/#/objet/{cc_id}"

IMAGE_PROXY_TMPL = (
    "https://collections.quaibranly.fr/cc/imageproxy.ashx"
    "?server=localhost&port=15012&filename={filename}&cache=yes"
)


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_quaibranly.py primero")
    return json.loads(RAW_PATH.read_text())


def _first(value):
    """Country/Toponyme/Ethnonyme pueden venir como dict (un valor) o list
    (varios) -- se usa siempre el primero, mismo criterio que el resto del
    pipeline ante campos multivaluados sin prioridad documentada."""
    if isinstance(value, list):
        return value[0] if value else None
    return value if isinstance(value, dict) else None


def _title(obj: dict) -> str | None:
    title_field = obj.get("Title")
    if isinstance(title_field, list) and title_field:
        for entry in title_field:
            if entry.get("TitleType") == "Titre":
                return entry.get("Title")
        return title_field[0].get("Title")
    if isinstance(title_field, dict):
        return title_field.get("Title")
    return obj.get("SortTitle")


def _culture(obj: dict) -> str | None:
    eth = _first(obj.get("Ethnonyme"))
    return eth.get("Term") if eth else None


def _provenance_text(obj: dict) -> str | None:
    """TermPath jerárquico del Toponyme (ej. "Muri Muri (village) < Matuku
    (île) < ... < Fidji < Mélanésie < Océanie") -- guardado tal cual como
    referencia de trazabilidad, la interpretación geográfica real vive en
    layer 2 (resolve_origin_quaibranly() en geocode.py)."""
    top = _first(obj.get("Toponyme"))
    return top.get("TermPath") if top else None


def _accession_year(obj: dict) -> str | None:
    acc = obj.get("ObjAccession") or {}
    init_date = acc.get("InitDate") or ""
    parts = init_date.split("/")
    if len(parts) == 3 and parts[-1].isdigit():
        return parts[-1]
    return None


def _credit_line(obj: dict) -> str | None:
    """El campo `Creditline` en texto libre casi nunca está poblado -- cuando
    no está, se arma una aproximación desde `ConXother` (actor + tipo de rol
    de la entrada de adquisición) + el año de `ObjAccession`, que es la forma
    más cercana a un creditLine que da el registro crudo de Quai Branly."""
    if obj.get("Creditline"):
        return obj["Creditline"]

    acquisition_entries = [
        e for e in (obj.get("ConXother") or [])
        if e.get("RoleType") == "En rapport avec l'acquisition"
    ]
    if not acquisition_entries:
        return None

    entry = acquisition_entries[0]
    role = entry.get("Role") or ""
    name = entry.get("DisplayName") or ""
    parts = [p for p in (role, name) if p]
    credit = ", ".join(parts)
    year = _accession_year(obj)
    if year:
        credit = f"{credit} ({year})" if credit else year
    return credit or None


def _image_url(image2: str | None) -> str | None:
    if not image2:
        return None
    filename = image2.replace("\\", "/")
    return IMAGE_PROXY_TMPL.format(filename=quote(filename, safe="/"))


def _primary_image(obj: dict) -> str | None:
    """`Image` (la foto principal) tiene prioridad; si no está poblada, se
    usa la de menor `rank` de `ImagesMoreObj` como fallback -- ver docstring
    del módulo para el hallazgo del patrón de URL."""
    image = obj.get("Image")
    if isinstance(image, dict) and image.get("image2"):
        return _image_url(image["image2"])

    more = obj.get("ImagesMoreObj")
    if isinstance(more, list) and more:
        best = min(more, key=lambda e: int(e.get("rank") or 0))
        return _image_url(best.get("image2"))

    return None


def build_row(obj: dict) -> dict:
    cc_id = obj.get("ccObjectID")
    title = _title(obj)
    return {
        "objectID": namespaced_id(QUAI_BRANLY, cc_id),
        "sourceMuseum": QUAI_BRANLY,
        "sourceObjectID": cc_id,
        "title": title,
        "objectName": title,
        "department": obj.get("Department"),
        "culture": _culture(obj),
        "period": obj.get("Dated"),
        "objectDate": obj.get("Dated"),
        "medium": obj.get("Medium"),
        "creditLine": _credit_line(obj),
        "accessionYear": _accession_year(obj),
        "excavation": None,  # museo etnográfico, no de excavación -- no hay campo equivalente
        "placeOfCreation": None,  # Quai Branly no distingue creación/hallazgo como el Louvre
        "placeOfDiscovery": None,
        "provenance": _provenance_text(obj),
        "primaryImage": _primary_image(obj),
        "objectURL": OBJECT_URL_TMPL.format(cc_id=cc_id),
    }


def main() -> None:
    objects = load_objects()
    rows = [build_row(o) for o in objects]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Total objetos: {len(rows)}")
    print(f"CSV guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
