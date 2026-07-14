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
MET_OBJECTS_PATH = DATA_DIR / "processed" / "met_objects.csv"
GEOGRAPHY_PATH = DATA_DIR / "processed" / "geography.csv"
CONTEXT_PATH = DATA_DIR / "enrichment" / "context.csv"
EVENTS_PATH = DATA_DIR / "enrichment" / "provenance_events.csv"

OUT_PATH = Path(__file__).resolve().parent.parent / "web" / "src" / "data" / "objects.json"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_rows() -> list[dict]:
    """Layer 1 + layer 2, joined por objectID. Solo devuelve piezas con
    coordenadas de origen resueltas — igual criterio que make_map.py."""
    met_objects = {r["objectID"]: r for r in read_csv(MET_OBJECTS_PATH)}
    geography = {r["objectID"]: r for r in read_csv(GEOGRAPHY_PATH)}

    rows = []
    for object_id, geo in geography.items():
        if not (geo.get("origin_lat") and geo.get("origin_lon")):
            continue
        met = met_objects.get(object_id, {})
        rows.append({**met, **geo})
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
        }

    obj_events = [
        {
            "event_order": int(e["event_order"]) if e.get("event_order") else None,
            "event_type": e.get("event_type") or None,
            "event_date": e.get("event_date") or None,
            "actor_or_institution": e.get("actor_or_institution") or None,
            "location": e.get("location") or None,
            "description": e.get("description") or None,
            "source_url": e.get("source_url") or None,
            "source_type": e.get("source_type") or None,
            "confidence_level": e.get("confidence_level") or None,
        }
        for e in events.get(object_id, [])
    ]

    return {
        "objectID": object_id,
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

    met_lat, met_lon = float(rows[0]["met_lat"]), float(rows[0]["met_lon"])
    objects = [build_object(r, context, events) for r in rows]

    bundle = {
        "met": {"lat": met_lat, "lon": met_lon, "name": "The Metropolitan Museum of Art", "city": "New York"},
        "objects": objects,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(bundle, ensure_ascii=False, indent=2))
    print(f"{len(objects)} piezas exportadas a {OUT_PATH}")


if __name__ == "__main__":
    main()
