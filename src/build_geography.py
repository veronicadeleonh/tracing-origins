"""
Layer 2 — interpretación geográfica (nuestra, no del Met).

Lee data/raw/met_objects_raw.json y corre cada objeto por geocode.py para
resolver un punto de origen (subregion > region > country > culture >
sin resolver). Escribe data/processed/geography.csv, separado de
met_objects.csv a propósito: esto es una inferencia nuestra, no un dato que
haya provisto el museo, y queremos que esa distinción sea visible en el
modelo de datos, no solo en el nombre de las columnas.

Uso:
    python src/build_geography.py
"""

import csv
import json
from pathlib import Path

from geocode import MET_COORDS, resolve_origin
from museum_id import MET, namespaced_id

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "met_objects_raw.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "geography.csv"

# museum_lat/museum_lon son las coordenadas del museo actual (destino de la
# línea) — se llamaban met_lat/met_lon, renombradas porque geography.csv ya
# no es Met-específico: cuando sumemos Louvre/British Museum sus filas van
# acá también, con sus propias coordenadas de destino.
FIELDS = ["objectID", "origin_label", "origin_label_en", "origin_precision", "origin_lat", "origin_lon", "museum_lat", "museum_lon"]


def load_objects() -> list[dict]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH} — corré fetch_met.py primero")
    return json.loads(RAW_PATH.read_text())


def build_row(obj: dict) -> dict:
    origin = resolve_origin(obj)
    museum_lat, museum_lon = MET_COORDS
    return {
        "objectID": namespaced_id(MET, obj.get("objectID")),
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
    print(f"Con origen geocodificado: {len(resolved)} ({len(resolved) / len(rows):.0%})")
    unresolved_labels = sorted({r["origin_label"] for r in rows if r["origin_precision"] == "unresolved" and r["origin_label"]})
    if unresolved_labels:
        print("Sin resolver (agregar a geocode.py si se repiten):")
        for label in unresolved_labels:
            print(f"  - {label}")
    print(f"CSV guardado en {OUT_PATH}")


if __name__ == "__main__":
    main()
