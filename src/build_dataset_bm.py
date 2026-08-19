"""
Layer 1 — metadata del British Museum, tal cual la da la página de objeto
(collection online). Lee data/raw/bm_objects_raw.json (ver fetch_bm.py) y
escribe data/processed/bm_objects.csv. Mismo principio que build_dataset.py
y build_dataset_louvre.py: no interpreta ni geocodifica nada.

Uso:
    python src/build_dataset_bm.py
"""

import csv
import json
import re
from pathlib import Path

from museum_id import BRITISH_MUSEUM, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "bm_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "bm_objects.csv"

FIELDS = [
    "objectID", "sourceMuseum", "sourceObjectID", "title", "objectName", "department",
    "culture", "period", "objectDate", "medium", "creditLine", "accessionYear",
    "excavation", "productionPlace", "findspot", "primaryImage", "objectURL",
]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_bm.py primero")
    return json.loads(RAW_PATH.read_text())


def _title_case_object_type(text: str) -> str:
    """Capitaliza la palabra/frase de fallback (ej. "signet-ring" ->
    "Signet-Ring", "animal remains" -> "Animal Remains") — encontrado el
    19/08: 75 de 90 piezas del BM no tienen "title" propio y caían en el
    fallback de `objectType`, que en la fuente cruda viene todo en
    minúscula, se veía desprolijo en la lista/ficha de la pieza. Es
    formateo de presentación, no interpretación de contenido (no cambia
    ninguna palabra, layer 1 sigue "tal cual la da la fuente" en el fondo).

    No toca lo que va entre paréntesis — hay casos con notas técnicas o
    texto en otro alfabeto ahí (ej. "bottle (백자반구병...)", coreano) que no
    tiene sentido ni conviene tocar; los caracteres CJK no tienen mayúscula/
    minúscula, así que da igual, pero paréntesis anidados ("jacket
    (sheepskin jacket (farwah/farweh))") sí podrían quedar raros si se les
    aplica el mismo capitalizado."""
    if not text:
        return text
    paren_idx = text.find("(")
    main = text if paren_idx == -1 else text[:paren_idx]
    suffix = "" if paren_idx == -1 else text[paren_idx:]
    parts = re.split(r"([ -])", main)
    capitalized_main = "".join(
        p[:1].upper() + p[1:] if p not in (" ", "-") else p for p in parts
    )
    return capitalized_main + suffix


def _title(obj: dict) -> str | None:
    # El campo "Title" del BM no siempre está (muchas piezas solo tienen
    # "Object Type" + "Description", sin título propio) — en ese caso usamos
    # el tipo de objeto como título de fallback. Cuando cae en ese fallback,
    # se le aplica _title_case_object_type() (ver arriba) porque el dato
    # crudo viene todo en minúscula; un "title" real del BM (15/90 piezas,
    # ej. "Object: The Rosetta Stone") ya viene bien formateado y se deja
    # intacto.
    title = obj.get("title")
    if title:
        return title
    fallback = obj.get("objectType") or obj.get("pageTitle")
    return _title_case_object_type(fallback) if fallback else fallback


def _excavation(obj: dict) -> str | None:
    excavator = (obj.get("excavator") or "").strip()
    findspot = (obj.get("findspot") or "").strip()
    if not excavator and not findspot:
        return None
    if excavator and findspot:
        return f"{excavator} — {findspot}"
    return excavator or findspot


def build_row(obj: dict) -> dict:
    object_id = obj.get("objectID")
    return {
        "objectID": namespaced_id(BRITISH_MUSEUM, object_id),
        "sourceMuseum": BRITISH_MUSEUM,
        "sourceObjectID": object_id,
        "title": _title(obj),
        "objectName": obj.get("objectType"),
        "department": obj.get("department"),
        "culture": obj.get("culturesPeriods"),
        "period": obj.get("culturesPeriods"),
        "objectDate": obj.get("productionDate"),
        "medium": obj.get("materials"),
        "creditLine": obj.get("acquisitionName"),
        "accessionYear": obj.get("acquisitionDate"),
        "excavation": _excavation(obj),
        "productionPlace": obj.get("productionPlace"),
        "findspot": obj.get("findspot"),
        "primaryImage": obj.get("image"),
        "objectURL": obj.get("url") or (
            f"https://www.britishmuseum.org/collection/object/{object_id}" if object_id else None
        ),
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
