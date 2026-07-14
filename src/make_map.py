"""
Genera un mapa interactivo (Leaflet, via folium) con una línea desde el Met
hasta el lugar de origen de cada pieza geocodificada en data/processed/objects.csv.

Uso:
    python src/make_map.py
"""

import csv
from collections import defaultdict
from pathlib import Path

import folium

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "objects.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "maps" / "map_pilot.html"

MET_COLOR = "#b23a48"
LINE_COLOR = "#c9a227"


def load_rows() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
        popup="The Metropolitan Museum of Art (Nueva York)",
    ).add_to(m)

    # Agrupar piezas por punto de origen para no dibujar 40 líneas superpuestas
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

        popup_lines = [f"<b>{label}</b> — {len(items)} pieza(s)<br>"]
        for it in items[:8]:
            popup_lines.append(
                f"<a href='{it['objectURL']}' target='_blank'>{it['title']}</a> "
                f"({it['objectDate']})<br>"
            )
        if len(items) > 8:
            popup_lines.append(f"... y {len(items) - 8} más")

        folium.CircleMarker(
            location=[lat, lon],
            radius=4 + min(len(items), 10),
            color=LINE_COLOR,
            fill=True,
            fill_color=LINE_COLOR,
            fill_opacity=0.85,
            popup=folium.Popup("".join(popup_lines), max_width=320),
        ).add_to(m)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT_PATH))
    print(f"Mapa guardado en {OUT_PATH} ({len(rows)} piezas, {len(grouped)} puntos de origen)")


if __name__ == "__main__":
    main()
