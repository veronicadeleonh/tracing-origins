"""
Layer 2 — interpretación geográfica del British Museum (nuestra, no del
museo). Mismo principio que build_geography_louvre.py: separado de
bm_objects.csv porque resolver un punto de origen es una inferencia
nuestra. Ver resolve_origin_bm() en geocode.py (findspot > productionPlace).

Uso:
    python src/build_geography_bm.py
"""

import csv
import json
from pathlib import Path

from geocode import BM_COORDS, resolve_origin_bm
from museum_id import BRITISH_MUSEUM, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "bm_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "geography_bm.csv"

FIELDS = ["objectID", "origin_label", "origin_precision", "origin_lat", "origin_lon", "museum_lat", "museum_lon"]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_bm.py primero")
    return json.loads(RAW_PATH.read_text())


def build_row(obj: dict) -> dict:
    origin = resolve_origin_bm(obj)
    museum_lat, museum_lon = BM_COORDS
    return {
        "objectID": namespaced_id(BRITISH_MUSEUM, obj.get("objectID")),
        "origin_label": origin["label"],
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
        print("Sin resolver (agregar a BM_SITE_COORDS/BM_COUNTRY_KEYWORDS en geocode.py si se repiten):")
        for label in unresolved_labels:
            print(f"  - {label}")
    print(f"CSV guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
