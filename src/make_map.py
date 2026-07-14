"""
Genera un mapa interactivo (Leaflet, via folium) con una línea desde el Met
hasta el lugar de origen de cada pieza geocodificada en data/processed/objects.csv.

Cada punto de origen agrupa las piezas que salieron de ahí; al hacer click se
abre una ficha por pieza con nombre, imagen (si hay), cultura/período, medio,
excavación/procedencia y link a la página del objeto en el Met.

Uso:
    python src/make_map.py
"""

import csv
import html
from collections import defaultdict
from pathlib import Path

import folium

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "objects.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "maps" / "map_pilot.html"

MET_COLOR = "#b23a48"
LINE_COLOR = "#c9a227"

MAX_CARDS_WITH_IMAGE = 6  # a partir de ahí, las piezas se listan sin thumbnail para no inflar el popup


def load_rows() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def piece_card(item: dict, with_image: bool) -> str:
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

    return f"""
    <div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #eee;">
      {thumb_html}
      <div style="min-width:0;">
        <a href="{url}" target="_blank" style="font-weight:600;color:#1a1a1a;text-decoration:none;">{title}</a><br>
        <span style="font-size:11px;color:#555;">{subtitle}</span><br>
        <span style="font-size:11px;color:#777;">{medium}</span><br>
        <span style="font-size:11px;color:#999;font-style:italic;">{provenance}</span>
      </div>
    </div>
    """


def build_popup_html(label: str, items: list[dict]) -> str:
    header = f'<div style="font-weight:700;font-size:13px;margin-bottom:4px;">{esc(label)} — {len(items)} pieza(s)</div>'
    cards = "".join(
        piece_card(it, with_image=(i < MAX_CARDS_WITH_IMAGE)) for i, it in enumerate(items)
    )
    body = f'<div style="max-height:320px;overflow-y:auto;padding-right:4px;">{cards}</div>'
    return f'<div style="font-family:system-ui,sans-serif;width:300px;">{header}{body}</div>'


def main() -> None:
    rows = [r for r in load_rows() if r["origin_lat"] and r["origin_lon"]]
    if not rows:
        raise SystemExit("No hay filas geocodificadas todavía. Corré build_dataset.py primero.")

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
            popup=folium.Popup(build_popup_html(label, items), max_width=320),
        ).add_to(m)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT_PATH))
    print(f"Mapa guardado en {OUT_PATH} ({len(rows)} piezas, {len(grouped)} puntos de origen)")


if __name__ == "__main__":
    main()
