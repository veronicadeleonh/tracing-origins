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


def _title(obj: dict) -> str | None:
    # El campo "Title" del BM no siempre está (muchas piezas solo tienen
    # "Object Type" + "Description", sin título propio) — en ese caso usamos
    # el tipo de objeto como título de fallback.
    return obj.get("title") or obj.get("objectType") or obj.get("pageTitle")


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
