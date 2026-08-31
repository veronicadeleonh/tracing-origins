"""
Layer 2 — interpretación geográfica de Quai Branly (nuestra, no del museo).

Mismo principio que build_geography_louvre.py/build_geography_bm.py: separado
de quaibranly_objects.csv a propósito, porque asignar coordenadas es una
inferencia nuestra. A diferencia de esos dos, acá el "matching" es un lookup
exacto contra un thesaurus controlado, no keywords contra texto libre -- ver
resolve_origin_quaibranly() en geocode.py para el detalle.

Uso:
    python src/build_geography_quaibranly.py
"""

import csv
import json
from pathlib import Path

from geocode import QUAI_BRANLY_COORDS, resolve_origin_quaibranly
from museum_id import QUAI_BRANLY, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "quaibranly_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "geography_quaibranly.csv"

FIELDS = ["objectID", "origin_label", "origin_label_en", "origin_precision", "origin_lat", "origin_lon", "origin_country", "origin_country_en", "museum_lat", "museum_lon"]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_quaibranly.py primero")
    return json.loads(RAW_PATH.read_text())


def build_row(obj: dict) -> dict:
    object_id = namespaced_id(QUAI_BRANLY, obj.get("ccObjectID"))
    origin = resolve_origin_quaibranly(obj)
    museum_lat, museum_lon = QUAI_BRANLY_COORDS
    return {
        "objectID": object_id,
        "origin_label": origin["label"],
        "origin_label_en": origin.get("label_en") or origin["label"],
        "origin_precision": origin["precision"],
        "origin_lat": origin["lat"],
        "origin_lon": origin["lon"],
        "origin_country": origin.get("country"),
        "origin_country_en": origin.get("country_en"),
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
        print("Sin resolver (agregar a QUAI_BRANLY_COUNTRY_COORDS en geocode.py si se repiten):")
        for label in unresolved_labels:
            print(f"  - {label}")
    print(f"CSV guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
