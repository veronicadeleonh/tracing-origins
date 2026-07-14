"""
Genera un mapa interactivo (Leaflet, via folium) con una línea desde el Met
hasta el lugar de origen de cada pieza.

Este es el único script que junta las 3 capas del modelo de datos:
  - data/processed/met_objects.csv   (layer 1: metadata del Met, sin tocar)
  - data/processed/geography.csv     (layer 2: nuestra interpretación geográfica)
  - data/enrichment/context.csv y
    data/enrichment/provenance_events.csv (layer 3: investigación histórica,
    opcional — la mayoría de las piezas todavía no tienen nada acá, y el mapa
    tiene que verse bien igual)

El join es por objectID. Layer 2 es obligatoria para dibujar el punto (si no
hay coordenadas, la pieza no entra al mapa). Layer 3 es opcional: si no hay
fila, la ficha muestra solo lo que vino del Met.

Cada punto de origen agrupa las piezas que salieron de ahí; al hacer click se
abre una ficha por pieza con nombre, imagen (si hay), cultura/período, medio,
excavación/procedencia, contexto histórico (si está investigado) y link a la
página del objeto en el Met.

Uso:
    python src/make_map.py
"""

import csv
import html
from collections import defaultdict
from pathlib import Path

import folium

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MET_OBJECTS_PATH = DATA_DIR / "processed" / "met_objects.csv"
GEOGRAPHY_PATH = DATA_DIR / "processed" / "geography.csv"
CONTEXT_PATH = DATA_DIR / "enrichment" / "context.csv"
EVENTS_PATH = DATA_DIR / "enrichment" / "provenance_events.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "maps" / "map_pilot.html"

MET_COLOR = "#b23a48"
LINE_COLOR = "#c9a227"

MAX_CARDS_WITH_IMAGE = 6  # a partir de ahí, las piezas se listan sin thumbnail para no inflar el popup


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_rows() -> list[dict]:
    """Layer 1 + layer 2, joined por objectID. Solo devuelve piezas con
    coordenadas de origen resueltas."""
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
    """Layer 3 — estado/tags de investigación por pieza. Opcional."""
    return {r["objectID"]: r for r in read_csv(CONTEXT_PATH)}


def load_events() -> dict[str, list[dict]]:
    """Layer 3 — timeline de eventos por pieza. Opcional, puede haber 0+ por objeto."""
    events_by_object = defaultdict(list)
    for r in read_csv(EVENTS_PATH):
        events_by_object[r["objectID"]].append(r)
    for object_id, events in events_by_object.items():
        events.sort(key=lambda e: int(e.get("event_order") or 0))
    return events_by_object


def esc(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def history_html(object_id: str, context: dict, events: list[dict]) -> str:
    """Sección opcional de contexto histórico — solo se muestra si hay algo
    investigado (layer 3). Si no hay nada, devuelve string vacío y la ficha
    se ve igual que antes."""
    ctx = context.get(object_id, {})
    notes = (ctx.get("notes") or "").strip()
    flags = (ctx.get("context_flags") or "").strip()
    obj_events = events.get(object_id, [])

    if not notes and not flags and not obj_events:
        return ""

    parts = ['<div style="margin-top:6px;padding-top:6px;border-top:1px dashed #ccc;">']
    parts.append('<span style="font-size:11px;font-weight:600;color:#7a4a1a;">Contexto histórico</span><br>')

    if flags:
        tags = [esc(t.strip()) for t in flags.split(";") if t.strip()]
        parts.append(
            "".join(
                f'<span style="font-size:10px;background:#f2e6d8;color:#7a4a1a;border-radius:3px;padding:1px 5px;margin:2px 4px 2px 0;display:inline-block;">{t}</span>'
                for t in tags
            )
        )

    if notes:
        parts.append(f'<div style="font-size:11px;color:#555;margin-top:2px;">{esc(notes)}</div>')

    if obj_events:
        items_html = "".join(
            f'<li style="margin-bottom:2px;">'
            f'<span style="color:#7a4a1a;">{esc(ev.get("event_date"))}</span> — '
            f'{esc(ev.get("event_type"))}: {esc(ev.get("description"))}'
            f"</li>"
            for ev in obj_events
        )
        parts.append(f'<ul style="font-size:11px;color:#555;margin:4px 0 0 16px;padding:0;">{items_html}</ul>')

    parts.append("</div>")
    return "".join(parts)


def piece_card(item: dict, with_image: bool, context: dict, events: dict) -> str:
    title = esc(item.get("title")) or "(sin título)"
    subtitle_parts = [p for p in [item.get("culture"), item.get("period"), item.get("objectDate")] if p]
    subtitle = esc(" · ".join(subtitle_parts))
    medium = esc(item.get("medium"))
    provenance = esc(item.get("excavation")) or esc(item.get("creditLine"))
    url = esc(item.get("objectURL"))
    img = item.get("primaryImage")

    thumb_html = ""
    if with_image and img:
        thumb_html = f'<img src="{esc(img)}" loading="lazy" style="width:56px;height:56px;object-fit:cover;border-radius:4px;flex-shrink:0;">'

    history = history_html(item.get("objectID"), context, events)

    return f"""
    <div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #eee;">
      {thumb_html}
      <div style="min-width:0;">
        <a href="{url}" target="_blank" style="font-weight:600;color:#1a1a1a;text-decoration:none;">{title}</a><br>
        <span style="font-size:11px;color:#555;">{subtitle}</span><br>
        <span style="font-size:11px;color:#777;">{medium}</span><br>
        <span style="font-size:11px;color:#999;font-style:italic;">{provenance}</span>
        {history}
      </div>
    </div>
    """


def build_popup_html(label: str, items: list[dict], context: dict, events: dict) -> str:
    header = f'<div style="font-weight:700;font-size:13px;margin-bottom:4px;">{esc(label)} — {len(items)} pieza(s)</div>'
    cards = "".join(
        piece_card(it, with_image=(i < MAX_CARDS_WITH_IMAGE), context=context, events=events)
        for i, it in enumerate(items)
    )
    body = f'<div style="max-height:320px;overflow-y:auto;padding-right:4px;">{cards}</div>'
    return f'<div style="font-family:system-ui,sans-serif;width:300px;">{header}{body}</div>'


def main() -> None:
    rows = load_rows()
    if not rows:
        raise SystemExit("No hay filas geocodificadas todavía. Corré build_dataset.py y build_geography.py primero.")

    context = load_context()
    events = load_events()

    met_lat, met_lon = float(rows[0]["met_lat"]), float(rows[0]["met_lon"])

    m = folium.Map(location=[20, 10], zoom_start=2, tiles="CartoDB positron")

    folium.CircleMarker(
        location=[met_lat, met_lon],
        radius=9,
        color=MET_COLOR,
        fill=True,
        fill_color=MET_COLOR,
        fill_opacity=1,
        tooltip="The Metropolitan Museum of Art (Nueva York)",
        popup=folium.Popup(
            '<div style="font-family:system-ui,sans-serif;"><b>The Metropolitan Museum of Art</b><br>'
            'Nueva York, Estados Unidos</div>',
            max_width=250,
        ),
    ).add_to(m)

    # Agrupar piezas por punto de origen para no dibujar decenas de líneas superpuestas
    grouped = defaultdict(list)
    for r in rows:
        key = (round(float(r["origin_lat"]), 3), round(float(r["origin_lon"]), 3), r["origin_label"])
        grouped[key].append(r)

    for (lat, lon, label), items in grouped.items():
        weight = min(1 + len(items) * 0.6, 8)
        folium.PolyLine(
            locations=[[met_lat, met_lon], [lat, lon]],
            color=LINE_COLOR,
            weight=weight,
            opacity=0.7,
        ).add_to(m)

        folium.CircleMarker(
            location=[lat, lon],
            radius=4 + min(len(items), 10),
            color=LINE_COLOR,
            fill=True,
            fill_color=LINE_COLOR,
            fill_opacity=0.85,
            tooltip=f"{label} — {len(items)} pieza(s) (click para el detalle)",
            popup=folium.Popup(build_popup_html(label, items, context, events), max_width=320),
        ).add_to(m)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT_PATH))
    print(f"Mapa guardado en {OUT_PATH} ({len(rows)} piezas, {len(grouped)} puntos de origen)")


if __name__ == "__main__":
    main()
