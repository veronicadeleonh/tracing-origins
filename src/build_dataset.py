"""
Layer 1 — metadata del museo, tal cual la da la API del Met.

Lee data/raw/met_objects_raw.json (el snapshot crudo congelado) y escribe
data/processed/met_objects.csv con los campos de la API sin modificar. No
geocodifica ni interpreta nada — eso vive en build_geography.py (layer 2) y
en data/enrichment/ (layer 3). Este script nunca escribe ni sobrescribe
campos del Met, solo los aplana a CSV.

Uso:
    python src/build_dataset.py
"""

import csv
import json
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "met_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "met_objects.csv"

# Todos estos campos vienen directo de la respuesta de la API del Met — nada
# calculado ni interpretado por nosotros. country/region/subregion se
# preservan tal cual (aunque geocode.py los usa como insumo en layer 2) para
# que layer 1 sea trazable de forma independiente.
FIELDS = [
    "objectID", "title", "objectName", "department", "culture", "period", "dynasty",
    "objectDate", "medium", "creditLine", "accessionYear", "excavation",
    "geographyType", "country", "region", "subregion", "primaryImage",
    "objectURL", "objectWikidata_URL",
]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_met.py primero")
    return json.loads(RAW_PATH.read_text())


def build_row(obj: dict) -> dict:
    return {field: obj.get(field) for field in FIELDS}


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
