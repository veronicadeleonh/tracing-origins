"""
Layer 2 — interpretación geográfica del Louvre (nuestra, no del museo).

Mismo principio que build_geography.py: separado de louvre_objects.csv a
propósito, porque resolver un punto de origen a partir de texto libre en
francés es una inferencia nuestra. Ver resolve_origin_louvre() en geocode.py
para el orden de prioridad (placeOfDiscovery > placeOfCreation > provenance)
y las listas de sitios/países que matchea.

Uso:
    python src/build_geography_louvre.py
"""

import csv
import json
from pathlib import Path

from geocode import LOUVRE_COORDS, resolve_origin_louvre
from museum_id import LOUVRE, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "louvre_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "geography_louvre.csv"

FIELDS = ["objectID", "origin_label", "origin_label_en", "origin_precision", "origin_lat", "origin_lon", "museum_lat", "museum_lon"]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_louvre.py primero")
    return json.loads(RAW_PATH.read_text())


def build_row(obj: dict) -> dict:
    origin = resolve_origin_louvre(obj)
    museum_lat, museum_lon = LOUVRE_COORDS
    return {
        "objectID": namespaced_id(LOUVRE, obj.get("arkId")),
        "origin_label": origin["label"],
        "origin_label_en": origin.get("label_en") or origin["label"],
        "origin_precision": origin["precision"],
        "origin_lat": origin["lat"],
        "origin_lon": origin["lon"],
        "museum_lat": museum_lat,
        "museum_lon": museum_lon,
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
    print(f"Con origen geocodificado: {len(resolved)} ({len(resolved) / len(rows):.0%})" if rows else "Sin filas")
    unresolved_labels = sorted({r["origin_label"] for r in rows if r["origin_precision"] == "unresolved" and r["origin_label"]})
    if unresolved_labels:
        print("Sin resolver (agregar a LOUVRE_SITE_COORDS/LOUVRE_COUNTRY_KEYWORDS en geocode.py si se repiten):")
        for label in unresolved_labels:
            print(f"  - {label}")
    print(f"CSV guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
