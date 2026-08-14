"""
Descarga fichas del British Museum (collection online). No hay API pública:
raspamos /collection/object/<id> directamente, que sí está permitido por
robots.txt (solo bloquea /search*, /admin/, etc. — la ficha de objeto no).

El propio robots.txt pide "Crawl-delay: 20" (20 segundos entre requests) y
lo respetamos a rajatabla acá: bajar incluso un piloto chico lleva varios
minutos.

Descubrimiento de IDs: a diferencia del Louvre, el puente por Wikidata
(P8565, "British Museum object ID") resultó poco confiable acá — casi
ningún objeto tiene cargado el departamento curatorial (P195), y varios
valores de P8565 vienen sin el prefijo de letra que el sitio necesita en la
URL real (ej. el valor crudo "Oc1869,1005.1" tira 404; hace falta un
prefijo como "E_" o "EA_" delante, inconsistente entre objetos). Así que en
vez de automatizar el descubrimiento, esta primera versión usa una lista
curada a mano de museum numbers ya verificados (ver SEED_OBJECT_IDS),
tomados de la página oficial de "piezas disputadas" del propio Museo
(britishmuseum.org/about-us/british-museum-story/contested-objects-collection)
y de búsquedas puntuales en /collection/search. Ampliar esa lista a mano es
el camino más confiable por ahora — no hay atajo automatizado limpio como
con el Louvre.

Requiere beautifulsoup4 (ver requirements.txt).

Uso:
    python src/fetch_bm.py
    python src/fetch_bm.py --delay 20
"""

import argparse
import json
import time
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "bm_objects_raw.json"
OBJECT_URL_TMPL = "https://www.britishmuseum.org/collection/object/{object_id}"
USER_AGENT = "colonial-museum-routes/0.1 (proyecto personal de portfolio; contacto: v.dleon@gmail.com)"
CRAWL_DELAY_DEFAULT = 20  # segundos — pedido explícito del robots.txt del sitio, no negociable

# Piezas semilla, verificadas a mano navegando el sitio (ver nota arriba
# sobre por qué no hay descubrimiento automatizado todavía). Cubre Egipto y
# Sudán, Oriente Medio, Asia y África — varias directamente vinculadas a la
# página de "contested objects" del propio Museo. A expandir a mano con más
# piezas de las mismas 5-6 historias curadas ahí (Benin, Asante, Maqdala,
# Partenón, moái de Rapa Nui) antes de escalar a un piloto más grande.
SEED_OBJECT_IDS = [
    "Y_EA24",  # Rosetta Stone — Egipto y Sudán
    "Y_EA1770",  # Sphinx of Taharqo — Egipto y Sudán
    "W_1848-1104-1",  # Black Obelisk of Shalmaneser III — Oriente Medio
    "A_1830-0612-4",  # Statue of Tara — Asia (Sri Lanka)
    "E_Af1898-0115-27",  # Benin plaque, Punitive Expedition 1897 — África
    "E_Af1898-0115-28",
    "E_Af1898-0115-29",
    "E_Af1898-0115-30",
    "E_Af1898-0115-32",
]


def fetch_object_html(object_id: str) -> str:
    url = OBJECT_URL_TMPL.format(object_id=object_id)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_object(object_id: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one("h1")

    fields: dict[str, list[str]] = {}
    for item in soup.select(".object-detail__data-item"):
        term = item.select_one(".object-detail__data-term")
        desc = item.select_one(".object-detail__data-description")
        if not term or not desc:
            continue
        label = term.get_text(strip=True)
        value = desc.get_text(" ", strip=True)
        fields.setdefault(label, []).append(value)

    def first(label: str) -> str | None:
        values = fields.get(label)
        return values[0] if values else None

    image_el = soup.select_one("meta[property='og:image']")

    return {
        "objectID": object_id,
        "pageTitle": title_el.get_text(strip=True) if title_el else None,
        "url": OBJECT_URL_TMPL.format(object_id=object_id),
        "objectType": first("Object Type"),
        "museumNumber": first("Museum number"),
        "title": first("Title"),
        "description": first("Description"),
        "culturesPeriods": first("Cultures/periods"),
        "productionDate": first("Production date"),
        "productionPlace": first("Production place"),
        "excavator": first("Excavator/field collector"),
        "findspot": first("Findspot"),
        "materials": first("Materials"),
        "curatorComments": first("Curator's comments"),
        "associatedNames": first("Associated names"),
        "acquisitionName": first("Acquisition name"),
        "acquisitionDate": first("Acquisition date"),
        "department": first("Department"),
        "image": image_el["content"] if image_el and image_el.has_attr("content") else None,
    }


def load_existing() -> dict[str, dict]:
    if not RAW_PATH.exists():
        return {}
    data = json.loads(RAW_PATH.read_text())
    return {obj["objectID"]: obj for obj in data}


def save(objects_by_id: dict[str, dict]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = [objects_by_id[k] for k in sorted(objects_by_id)]
    RAW_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2))


def main(object_ids: list[str], delay: float) -> None:
    objects_by_id = load_existing()
    pending = [oid for oid in object_ids if oid not in objects_by_id]
    print(f"{len(object_ids)} IDs pedidos, {len(pending)} nuevos a bajar (crawl-delay {delay}s entre requests)")

    for i, object_id in enumerate(pending):
        try:
            html = fetch_object_html(object_id)
            obj = parse_object(object_id, html)
            objects_by_id[object_id] = obj
            print(f"  {object_id}: {obj.get('title') or obj.get('pageTitle')}")
        except Exception as exc:
            print(f"  error en {object_id}: {exc}")
        save(objects_by_id)  # checkpoint tras cada objeto, dado lo lento del crawl-delay
        if i < len(pending) - 1:
            time.sleep(delay)

    print(f"Guardado en {RAW_PATH} ({len(objects_by_id)} objetos totales)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=CRAWL_DELAY_DEFAULT, help="Segundos entre requests (robots.txt pide 20)")
    args = parser.parse_args()

    main(SEED_OBJECT_IDS, delay=args.delay)
