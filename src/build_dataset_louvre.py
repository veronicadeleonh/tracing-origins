"""
Layer 1 — metadata del Louvre, tal cual la da collections.louvre.fr.

Lee data/raw/louvre_objects_raw.json (snapshot crudo, ver fetch_louvre.py) y
escribe data/processed/louvre_objects.csv. Mismo principio que
build_dataset.py: no interpreta ni geocodifica nada, solo aplana los campos
del Louvre a un CSV. La interpretación geográfica vive en
build_geography_louvre.py (layer 2).

El shape de datos del Louvre es bien distinto al del Met (ver
https://collections.louvre.fr/en/page/documentationJSON): no hay
country/region/subregion estructurado, las fechas y la adquisición vienen en
listas de objetos anidados. Este script los aplana a texto simple para que
el resto del pipeline (export_web_data.py, la app) los pueda tratar igual
que los campos del Met.

Uso:
    python src/build_dataset_louvre.py
"""

import csv
import json
from pathlib import Path

from museum_id import LOUVRE, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "louvre_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "louvre_objects.csv"

FIELDS = [
    "objectID", "sourceMuseum", "sourceObjectID", "title", "objectName", "department",
    "culture", "period", "objectDate", "medium", "creditLine", "accessionYear",
    "excavation", "placeOfCreation", "placeOfDiscovery", "provenance",
    "primaryImage", "objectURL",
]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_louvre.py primero")
    return json.loads(RAW_PATH.read_text())


def _denomination(obj: dict) -> str | None:
    for entry in obj.get("denominationTitle") or []:
        if entry.get("type") == "Dénomination":
            return entry.get("value")
    return None


def _acquisition_credit(obj: dict) -> tuple[str | None, str | None]:
    """(creditLine, accessionYear) a partir de acquisitionDetails[0]."""
    details = obj.get("acquisitionDetails") or []
    if not details:
        return None, None
    entry = details[0]
    mode = entry.get("mode") or ""
    dates = entry.get("dates") or []
    year = None
    date_label = None
    if dates:
        year = dates[0].get("startYear")
        date_label = dates[0].get("value") or (str(year) if year else None)
    credit = mode
    if date_label:
        credit = f"{mode} ({date_label})" if mode else date_label
    return credit or None, str(year) if year else None


def _excavation(obj: dict) -> str | None:
    """placeOfDiscovery + dateOfDiscovery combinados, cuando hay excavación
    documentada — equivalente aproximado al campo `excavation` del Met."""
    place = (obj.get("placeOfDiscovery") or "").strip()
    date = (obj.get("dateOfDiscovery") or "").strip()
    if not place and not date:
        return None
    if place and date:
        return f"{place} ({date})"
    return place or date


def build_row(obj: dict) -> dict:
    ark = obj.get("arkId")
    credit_line, accession_year = _acquisition_credit(obj)
    image = (obj.get("image") or [{}])[0]
    return {
        "objectID": namespaced_id(LOUVRE, ark),
        "sourceMuseum": LOUVRE,
        "sourceObjectID": ark,
        "title": obj.get("title"),
        "objectName": _denomination(obj) or obj.get("title"),
        "department": obj.get("collection"),
        "culture": None,
        "period": obj.get("displayDateCreated"),
        "objectDate": obj.get("displayDateCreated"),
        "medium": obj.get("materialsAndTechniques"),
        "creditLine": credit_line,
        "accessionYear": accession_year,
        "excavation": _excavation(obj),
        "placeOfCreation": obj.get("placeOfCreation"),
        "placeOfDiscovery": obj.get("placeOfDiscovery"),
        "provenance": obj.get("provenance"),
        "primaryImage": image.get("urlImage"),
        "objectURL": obj.get("url"),
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
