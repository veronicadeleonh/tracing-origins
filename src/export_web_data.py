"""
Junta las 3 capas del modelo de datos (igual que make_map.py) y las escribe
como un único JSON para que la app en web/ lo consuma. No depende de folium
a propósito — esto es solo transporte de datos, no visualización.

Uso:
    python src/export_web_data.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONTEXT_PATH = DATA_DIR / "enrichment" / "context.csv"
EVENTS_PATH = DATA_DIR / "enrichment" / "provenance_events.csv"

# Un (objects_csv, geography_csv) por museo — cada builder de layer 1/2 vive
# en su propio par de scripts (build_dataset.py/build_geography.py para el
# Met, build_dataset_louvre.py/build_geography_louvre.py para el Louvre,
# etc.), pero acá se juntan todos antes de cruzar con layer 3. Si un par de
# archivos no existe todavía (museo sin pipeline corrido aún) se lo salta.
MUSEUM_SOURCES = [
    (DATA_DIR / "processed" / "met_objects.csv", DATA_DIR / "processed" / "geography.csv"),
    (DATA_DIR / "processed" / "louvre_objects.csv", DATA_DIR / "processed" / "geography_louvre.csv"),
    (DATA_DIR / "processed" / "bm_objects.csv", DATA_DIR / "processed" / "geography_bm.csv"),
]

OUT_PATH = Path(__file__).resolve().parent.parent / "web" / "src" / "data" / "objects.json"

# Metadata de despliegue por museo (nombre/ciudad para mostrar). Las
# coordenadas se toman de geography.csv (museum_lat/museum_lon), no de acá —
# esto es solo lo que no viene en el CSV por fila.
MUSEUM_META = {
    "met": {"name": "The Metropolitan Museum of Art", "city": "New York"},
    "louvre": {"name": "Musée du Louvre", "city": "Paris"},
    "bm": {"name": "British Museum", "city": "London"},
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_rows() -> list[dict]:
    """Layer 1 + layer 2, joined por objectID, para todos los museos en
    MUSEUM_SOURCES. Solo devuelve piezas con coordenadas de origen resueltas
    — igual criterio que make_map.py."""
    rows = []
    for objects_path, geography_path in MUSEUM_SOURCES:
        objects_by_id = {r["objectID"]: r for r in read_csv(objects_path)}
        geography = {r["objectID"]: r for r in read_csv(geography_path)}
        for object_id, geo in geography.items():
            if not (geo.get("origin_lat") and geo.get("origin_lon")):
                continue
            obj = objects_by_id.get(object_id, {})
            rows.append({**obj, **geo})
    return rows


def load_context() -> dict[str, dict]:
    return {r["objectID"]: r for r in read_csv(CONTEXT_PATH)}


def load_events() -> dict[str, list[dict]]:
    events_by_object = defaultdict(list)
    for r in read_csv(EVENTS_PATH):
        events_by_object[r["objectID"]].append(r)
    for object_id, events in events_by_object.items():
        events.sort(key=lambda e: int(e.get("event_order") or 0))
    return events_by_object


def build_object(row: dict, context: dict, events: dict) -> dict:
    object_id = row["objectID"]
    ctx = context.get(object_id)
    context_out = None
    if ctx:
        flags = [f.strip() for f in (ctx.get("context_flags") or "").split(";") if f.strip()]
        context_out = {
            "research_status": ctx.get("research_status") or "not_started",
            "context_flags": flags,
            "associated_communities_or_states": ctx.get("associated_communities_or_states") or None,
            "notes": ctx.get("notes") or None,
            "notesEn": ctx.get("notes_en") or None,
        }

    obj_events = [
        {
            "event_order": int(e["event_order"]) if e.get("event_order") else None,
            "event_type": e.get("event_type") or None,
            "event_date": e.get("event_date") or None,
            "actor_or_institution": e.get("actor_or_institution") or None,
            "location": e.get("location") or None,
            "description": e.get("description") or None,
            "descriptionEs": e.get("description_es") or e.get("description") or None,
            "descriptionEn": e.get("description_en") or None,
            "source_url": e.get("source_url") or None,
            "source_type": e.get("source_type") or None,
            "confidence_level": e.get("confidence_level") or None,
        }
        for e in events.get(object_id, [])
    ]

    return {
        "objectID": object_id,
        "sourceMuseum": row.get("sourceMuseum") or None,
        "title": row.get("title") or None,
        "objectName": row.get("objectName") or None,
        "department": row.get("department") or None,
        "culture": row.get("culture") or None,
        "period": row.get("period") or None,
        "dynasty": row.get("dynasty") or None,
        "objectDate": row.get("objectDate") or None,
        "medium": row.get("medium") or None,
        "creditLine": row.get("creditLine") or None,
        "accessionYear": row.get("accessionYear") or None,
        "excavation": row.get("excavation") or None,
        "country": row.get("country") or None,
        "region": row.get("region") or None,
        "subregion": row.get("subregion") or None,
        "primaryImage": row.get("primaryImage") or None,
        "objectURL": row.get("objectURL") or None,
        "originLabel": row.get("origin_label") or None,
        "originLabelEn": row.get("origin_label_en") or row.get("origin_label") or None,
        "originPrecision": row.get("origin_precision") or None,
        "originLat": float(row["origin_lat"]),
        "originLon": float(row["origin_lon"]),
        "context": context_out,
        "events": obj_events,
    }


def main() -> None:
    rows = load_rows()
    if not rows:
        raise SystemExit("No hay filas geocodificadas todavía. Corré build_dataset.py y build_geography.py primero.")

    context = load_context()
    events = load_events()

    objects = [build_object(r, context, events) for r in rows]

    # Un museo (destino) por sourceMuseum, tomando lat/lon de la primera fila
    # que aparece de cada uno — todas las filas de un mismo museo comparten
    # el mismo museum_lat/museum_lon.
    museums = {}
    for r in rows:
        source = r.get("sourceMuseum")
        if source and source not in museums:
            meta = MUSEUM_META.get(source, {"name": source, "city": ""})
            museums[source] = {
                "lat": float(r["museum_lat"]),
                "lon": float(r["museum_lon"]),
                "name": meta["name"],
                "city": meta["city"],
            }

    bundle = {"museums": museums, "objects": objects}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
    print(f"{len(objects)} piezas exportadas a {OUT_PATH}")


if __name__ == "__main__":
    main()
