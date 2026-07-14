"""
Lee todo lo que haya en data/raw/ (tanto archivos de un objeto como bundles
tipo lista, ej. el piloto de Egyptian Art) y arma un CSV limpio con el origen
geocodificado de cada pieza.

Uso:
    python src/build_dataset.py
"""

import csv
import json
from pathlib import Path

from geocode import MET_COORDS, resolve_origin

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "objects.csv"

FIELDS = [
    "objectID", "title", "objectName", "department", "culture", "period", "dynasty",
    "objectDate", "medium", "creditLine", "accessionYear", "excavation",
    "geographyType", "origin_label", "origin_precision", "origin_lat", "origin_lon",
    "met_lat", "met_lon", "primaryImage", "objectURL", "objectWikidata_URL",
]


def load_objects() -> list[dict]:
    objects = []
    for path in sorted(RAW_DIR.glob("*.json")):
        raw = json.loads(path.read_text())
        if isinstance(raw, list):
            objects.extend(raw)
        else:
            objects.append(raw)
    return objects


def build_row(obj: dict) -> dict:
    origin = resolve_origin(obj)
    met_lat, met_lon = MET_COORDS
    return {
        "objectID": obj.get("objectID"),
        "title": obj.get("title"),
        "objectName": obj.get("objectName"),
        "department": obj.get("department"),
        "culture": obj.get("culture"),
        "period": obj.get("period"),
        "dynasty": obj.get("dynasty"),
        "objectDate": obj.get("objectDate"),
        "medium": obj.get("medium"),
        "creditLine": obj.get("creditLine"),
        "accessionYear": obj.get("accessionYear"),
        "excavation": obj.get("excavation"),
        "geographyType": obj.get("geographyType"),
        "origin_label": origin["label"],
        "origin_precision": origin["precision"],
        "origin_lat": origin["lat"],
        "origin_lon": origin["lon"],
        "met_lat": met_lat,
        "met_lon": met_lon,
        "primaryImage": obj.get("primaryImage"),
        "objectURL": obj.get("objectURL"),
        "objectWikidata_URL": obj.get("objectWikidata_URL"),
    }


def main() -> None:
    objects = load_objects()
    rows = [build_row(o) for o in objects]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    resolved = [r for r in rows if r["origin_precision"] != "unresolved"]
    print(f"Total objetos: {len(rows)}")
    print(f"Con origen geocodificado: {len(resolved)} ({len(resolved) / len(rows):.0%})")
    unresolved_labels = sorted({r["origin_label"] for r in rows if r["origin_precision"] == "unresolved" and r["origin_label"]})
    if unresolved_labels:
        print("Sin resolver (agregar a geocode.py si se repiten):")
        for label in unresolved_labels:
            print(f"  - {label}")
    print(f"CSV guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
