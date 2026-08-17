"""
Descarga y filtra CLIWOC (Climatological Database for the World's Oceans,
release 2.1, archivada en PANGAEA) para extraer rutas navegadas por barcos
UK/Francia entre --min-year y --max-year, como capa de contexto visual
adicional en el mapa — mismo patrón que fetch_colonial_overlay.py: bajar/
cachear localmente sin commitear, exportar un GeoJSON chico y curado a
web/public/.

Esto NO es parte del modelo de datos de 3 capas (layer 1/2/3): es contexto
histórico general, no ligado a ninguna pieza puntual — vive aparte en
web/public/navigator_routes.geojson igual que colonial_overlay.geojson.

Fuente: Jones, PD; Wheeler, DA; Können, GP; Koek, FB; Prieto, MR;
García-Herrera, R (2007): Climatological observations from ship logbooks
between 1750 and 1854 (release 2.1). PANGAEA, https://doi.org/10.1594/PANGAEA.611088
Licencia: CC-BY 3.0 (verificada 16/08, meta-DCTERMS.license del registro
PANGAEA). Atribuir con la cita de arriba en README/CLAUDE.md y en un crédito
visible en la app, mismo criterio que Cliopatria.

Por qué EEUU/Países Bajos/España quedan afuera: alcance confirmado con el
usuario el 16/08 — la app solo tiene museos de Nueva York/París/Londres, así
que las capas de contexto se limitan a UK+Francia, aunque CLIWOC trae las 4
potencias. Agregar rutas neerlandesas/españolas solo tendría sentido si se
suma un museo de Madrid o Ámsterdam.

Por qué NO son "viajes famosos" (Cook, Bougainville, La Pérouse): se buscaron
a mano y ninguno aparece en el dataset — CLIWOC se armó a partir de archivos
de bitácoras de rutina (Marina Real, VOC holandesa, mercantes coloniales), no
de expediciones científicas de exploración. El criterio de curación acá es
nación + bitácora más completa (más datapoints), no fama del viaje puntual.

CÓMO SE IDENTIFICA LA NACIÓN (revisado 16/08 contra archivos reales — el
enfoque original vía el campo "Company:" del Event NO funciona para
Francia/España): el campo "Company:" (ej. "Royal Navy", "VOC", "EIC") solo
está poblado para barcos británicos y holandeses — las bitácoras francesas y
españolas de este dataset vienen de archivos navales que no registraban una
"compañía" (tiene sentido: EIC/VOC eran compañías comerciales con estructura
corporativa propia, Francia/España operaban vía la Marina Real directamente).
La señal confiable para las 4 naciones está en la línea "Citation:", que
siempre termina con la institución de archivo + país antes de ", PANGAEA,"
(ej. "Archivo Museo Naval Madrid, Spain", "Centre d'Accueil et de Recherche
des Archives Nationales, Paris, France", "National Maritime Museum,
Greenwich, United Kingdom") — clasificamos por ahí, no por Company.

LIMITACIÓN CONOCIDA: no todas las bitácoras tienen columnas Latitude/Longitude
en la tabla de datos — algunas (sobre todo patrullas costeras francesas de la
serie de archivo "COTE_4_JJ") no registraron posición geográfica en
absoluto, solo clima, y quedan afuera de cualquier capa de mapa sin importar
la nación. Correr --explore-countries para ver cuántas bitácoras por país
tienen geometría utilizable antes de fijar --max-routes.

RUTA = TRAZA REAL, NO LÍNEA RECTA (revisado 16/08 tras probar en el mapa): el
primer intento usaba solo lat/lon de inicio y fin del resumen del header —
se ve como una línea recta que corta por tierra sin ningún respeto por la
costa (una ruta UK->Indonesia cruzando derecho por Medio Oriente, por
ejemplo). Se cambió a leer la TABLA de datos real de cada archivo (columnas
"Latitude"/"Longitude", una fila por observación) y usar la secuencia
completa como traza — ver extract_track(). Se subsamplea a un máximo de
MAX_TRACK_POINTS por ruta para no inflar el archivo con densidad diaria
innecesaria a escala de mapa mundial.

Granularidad real del dato: PANGAEA no expone un CSV único de ~287k puntos —
son 5468 datasets, uno por crucero, cada uno con su propio archivo
tab-delimited (extensión .tab, confirmado 16/08 — no .txt como se asumió al
principio). El bloque de metadata al inicio de cada archivo (encabezado
"/* ... */") trae un Event(s) con Ship/fecha/lat-lon de inicio y fin.

Uso:
    # 1. Bajar el ZIP completo (5468 archivos, pesado — una sola vez, no se
    #    commitea) y ver, por país, cuántas bitácoras hay y cuántas tienen
    #    geometría completa (lat/lon inicio+fin):
    python src/fetch_navigator_routes.py --explore-countries

    # 2. Exportar el geojson filtrado UK+Francia:
    python src/fetch_navigator_routes.py --export --min-year 1700 --max-year 1900 --max-routes 50
"""

import argparse
import json
import re
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

ZIP_URL = "https://doi.pangaea.de/10.1594/PANGAEA.611088?format=zip"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
ZIP_PATH = CACHE_DIR / "cliwoc_pangaea.zip"
EXTRACT_DIR = CACHE_DIR / "cliwoc_pangaea"
OUT_PATH = Path(__file__).resolve().parent.parent / "web" / "public" / "navigator_routes.geojson"

# Nombres de país tal como aparecen, literal, en la línea Citation de PANGAEA
# (confirmado 16/08 contra ejemplos reales de los 4 países). "Netherland" es
# así, singular, no es un typo nuestro.
UK_CITATION_MARKERS = ["United Kingdom"]
FR_CITATION_MARKERS = ["France"]
NL_CITATION_MARKERS = ["Netherland"]
ES_CITATION_MARKERS = ["Spain"]

# El header real de PANGAEA usa las etiquetas del bloque Event(s) en
# MAYÚSCULAS ("LATITUDE START:", "DATE/TIME START:", etc.) — confirmado a
# mano el 16/08 contra archivos reales. Ship: sí va en minúsculas porque es
# texto libre dentro del campo COMMENT del Event, no una etiqueta estructural.
CITATION_RE = re.compile(r"\[dataset\]\.\s*(.+?),\s*PANGAEA,", re.DOTALL)
EVENT_BLOCK_RE = re.compile(r"Event\(s\):(.*?)(?:\nParameter\(s\):|\nLicense:|\*/)", re.DOTALL | re.IGNORECASE)
SHIP_RE = re.compile(r"Ship:\s*([^,(]+)", re.IGNORECASE)
COMPANY_RE = re.compile(r"Company:\s*([^,\n]+)", re.IGNORECASE)
DATE_START_RE = re.compile(r"DATE/TIME START:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", re.IGNORECASE)
DATE_END_RE = re.compile(r"DATE/TIME END:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", re.IGNORECASE)
LAT_START_RE = re.compile(r"LATITUDE START:\s*(-?[0-9.]+)", re.IGNORECASE)
LON_START_RE = re.compile(r"LONGITUDE START:\s*(-?[0-9.]+)", re.IGNORECASE)
LAT_END_RE = re.compile(r"LATITUDE END:\s*(-?[0-9.]+)", re.IGNORECASE)
LON_END_RE = re.compile(r"LONGITUDE END:\s*(-?[0-9.]+)", re.IGNORECASE)
SIZE_RE = re.compile(r"Size:\s*[^0-9]*([0-9]+)\s*data points", re.IGNORECASE)


def download_and_unzip() -> Path:
    """Baja el ZIP de PANGAEA si todavía no está cacheado. Es pesado (5468
    archivos) — se guarda en data/raw/, gitignoreado, igual que
    cliopatria.geojson.zip. Con red restringida (ver nota de sandbox en
    CLAUDE.md) esto puede fallar acá — correrlo en la máquina real."""
    if EXTRACT_DIR.exists() and any(EXTRACT_DIR.iterdir()):
        print(f"Ya existe {EXTRACT_DIR}, no vuelvo a bajar (borrala si querés forzar la descarga de nuevo)")
        return EXTRACT_DIR
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Bajando {ZIP_URL} ... (puede tardar varios minutos, son 5468 archivos)")
    urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)
    print(f"Descomprimiendo en {EXTRACT_DIR} ...")
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(EXTRACT_DIR)
    print(f"Listo: {EXTRACT_DIR}")
    return EXTRACT_DIR


def classify_citation_country(header: str) -> str | None:
    """Clasifica la nación a partir de la línea Citation (ver docstring del
    módulo — es más confiable que el campo Company, que no existe para
    Francia/España en este dataset)."""
    m = CITATION_RE.search(header)
    if not m:
        return None
    snippet = m.group(1)
    if any(marker in snippet for marker in UK_CITATION_MARKERS):
        return "uk"
    if any(marker in snippet for marker in FR_CITATION_MARKERS):
        return "fr"
    if any(marker in snippet for marker in NL_CITATION_MARKERS):
        return "nl"
    if any(marker in snippet for marker in ES_CITATION_MARKERS):
        return "es"
    return None


MAX_TRACK_POINTS = 150  # tope por ruta — subsamplear en vez de mandar cada entrada diaria cruda


def extract_track(text: str, header_end: int) -> list[tuple[float, float]]:
    """Lee la TABLA de datos real (después del bloque /* ... */), no el
    resumen del header — el header solo trae lat/lon de inicio y fin, que en
    un mapa se dibuja como línea recta y cruza tierra sin ningún respeto por
    la costa real (confirmado a mano el 16/08: una línea UK->Indonesia corta
    derecho por Medio Oriente). La tabla en cambio tiene una fila por
    observación con columnas "Latitude"/"Longitude" (nombre exacto, sin
    corchetes de unidad) — usamos esa secuencia completa como la traza real
    de la ruta. Devuelve [] si el dataset no tiene esas columnas (algunas
    bitácoras, sobre todo patrullas costeras francesas, solo registraron
    clima)."""
    body = text[header_end:].lstrip("\n")
    lines = body.split("\n")
    if not lines or not lines[0].strip():
        return []
    columns = [c.strip() for c in lines[0].split("\t")]
    try:
        lat_idx = columns.index("Latitude")
        lon_idx = columns.index("Longitude")
    except ValueError:
        return []

    points: list[tuple[float, float]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) <= max(lat_idx, lon_idx):
            continue
        lat_raw, lon_raw = cells[lat_idx].strip(), cells[lon_idx].strip()
        if not lat_raw or not lon_raw:
            continue
        try:
            points.append((float(lon_raw), float(lat_raw)))
        except ValueError:
            continue

    if len(points) > MAX_TRACK_POINTS:
        # Subsamplear parejo, conservando siempre el primer y el último punto
        # (índices 0 y len-1 caen exactos con este cálculo) — no perdemos la
        # forma general de la ruta, solo la densidad diaria.
        stride = (len(points) - 1) / (MAX_TRACK_POINTS - 1)
        indices = sorted({round(i * stride) for i in range(MAX_TRACK_POINTS)})
        points = [points[i] for i in indices]

    return points


def parse_cruise_file(path: Path) -> dict | None:
    """Parsea un archivo tab-delimited de PANGAEA: metadata del header
    (ship/company/país/fechas) + la traza real de lat/lon de la tabla de
    datos (ver extract_track). Devuelve None solo si falta el campo más
    básico (ship o fecha de inicio) — la geometría es opcional a propósito:
    algunas bitácoras (sobre todo patrullas costeras francesas) no la tienen,
    y queremos poder CONTARLAS igual en --explore-countries en vez de que
    desaparezcan silenciosamente. `has_geometry` indica si el registro sirve
    para trazar una ruta real en el mapa (traza con recorrido, no solo 2
    puntos idénticos)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    header_match = re.search(r"/\*(.*?)\*/", text, re.DOTALL)
    header = header_match.group(1) if header_match else text

    country = classify_citation_country(header)

    # El header tiene un bloque "Coverage:" ANTES del "Event(s):" que repite
    # los mismos nombres de campo (DATE/TIME START, etc.) pero con el
    # timestamp del primer/último dato registrado, no el nominal del viaje.
    # Aislar el bloque Event(s) evita levantar por accidente el valor de
    # Coverage con un simple re.search sobre el header entero.
    event_block_m = EVENT_BLOCK_RE.search(header)
    event_text = event_block_m.group(1) if event_block_m else header

    ship_m = SHIP_RE.search(event_text)
    company_m = COMPANY_RE.search(event_text)
    date_start_m = DATE_START_RE.search(event_text)
    date_end_m = DATE_END_RE.search(event_text)
    size_m = SIZE_RE.search(header)

    if not (ship_m and date_start_m):
        return None

    year_start = int(date_start_m.group(1)[:4])
    year_end = int(date_end_m.group(1)[:4]) if date_end_m else year_start

    track = extract_track(text, header_match.end() if header_match else 0)
    # "Geometría completa" ahora significa una traza real con algo de
    # extensión geográfica, no solo 2 puntos idénticos (patrullas que salen y
    # vuelven al mismo punto quedan afuera igual que antes, pero detectado
    # sobre la traza completa en vez de sobre el resumen del header).
    has_geometry = len(track) >= 2 and (
        max(p[0] for p in track) - min(p[0] for p in track) > 0.01
        or max(p[1] for p in track) - min(p[1] for p in track) > 0.01
    )

    return {
        "ship": ship_m.group(1).strip(),
        "company": company_m.group(1).strip() if company_m else None,
        "country": country,
        "date_start": date_start_m.group(1),
        "date_end": date_end_m.group(1) if date_end_m else date_start_m.group(1),
        "year": year_start,
        "year_end": year_end,
        "has_geometry": has_geometry,
        "track": track if has_geometry else None,
        "size": int(size_m.group(1)) if size_m else 0,
    }


def iter_cruises(extract_dir: Path):
    # PANGAEA exporta como .tab (confirmado 16/08) — se deja .txt como
    # fallback por si algún dataset viejo usa otra extensión.
    seen = set()
    for pattern in ("*.tab", "*.txt"):
        for path in extract_dir.rglob(pattern):
            if path in seen:
                continue
            seen.add(path)
            parsed = parse_cruise_file(path)
            if parsed:
                yield parsed


def explore_countries(extract_dir: Path) -> None:
    totals: Counter[str] = Counter()
    with_geometry: Counter[str] = Counter()
    for cruise in iter_cruises(extract_dir):
        key = cruise["country"] or "(sin identificar)"
        totals[key] += 1
        if cruise["has_geometry"]:
            with_geometry[key] += 1

    if not totals:
        print("No pude parsear ningún archivo — revisá el formato real a mano.")
        return

    print(f"{sum(totals.values())} cruceros parseados en total:\n")
    for country, total in totals.most_common():
        geo = with_geometry.get(country, 0)
        print(f"  {country}: {total} bitácoras, {geo} con geometría completa (lat/lon inicio+fin)")


def explore_companies(extract_dir: Path) -> None:
    """Se mantiene como diagnóstico secundario — Company solo está poblado
    para UK/Países Bajos en este dataset (ver docstring del módulo), no sirve
    como clasificador principal, pero es útil para ver qué tan seguido
    aparece 'Royal Navy' puro vs. variantes."""
    counter: Counter[str] = Counter()
    for cruise in iter_cruises(extract_dir):
        counter[cruise["company"] or "(sin Company)"] += 1
    print(f"{sum(counter.values())} cruceros parseados, {len(counter)} valores distintos de 'Company':")
    for company, count in counter.most_common():
        print(f"  {company!r}: {count}")


MIN_TRACK_POINTS = 6  # menos que esto y la traza se ve casi como línea recta igual — descartar


def export(extract_dir: Path, min_year: int, max_year: int, max_routes: int, precision: int) -> None:
    candidates = []
    for cruise in iter_cruises(extract_dir):
        if not cruise["has_geometry"]:
            continue
        if cruise["country"] not in ("uk", "fr"):
            continue
        if not (min_year <= cruise["year"] <= max_year):
            continue
        # Cruceros cuya traza no tiene extensión geográfica real (patrullas
        # que salen y vuelven casi al mismo punto) ya quedan afuera acá — el
        # chequeo vive en has_geometry (ver parse_cruise_file), calculado
        # sobre la traza completa, no solo sobre el resumen del header.
        # Además: algunas bitácoras registran clima casi todos los días pero
        # posición solo un par de veces — technically "tienen geometría" (2+
        # puntos con extensión) pero la traza sigue viéndose como línea recta
        # (visto a mano el 16/08: una ruta francesa cerca de Mauricio). Exigir
        # un mínimo de puntos de posición reales, no solo de datapoints
        # climáticos totales.
        if len(cruise["track"]) < MIN_TRACK_POINTS:
            continue
        candidates.append(cruise)

    if not candidates:
        raise SystemExit(
            "No encontré cruceros UK/Francia con geometría completa en ese rango — "
            "corré --explore-countries primero para ver cuántos hay disponibles."
        )

    # Priorizar bitácoras con la traza más rica (más puntos de posición
    # reales, no el total de datapoints climáticos de "size" — una bitácora
    # puede tener miles de lecturas de viento/presión y aun así solo 2-3
    # posiciones registradas) dentro de cada nación, repartiendo el cupo
    # entre las dos en vez de dejar que una domine — mismo espíritu que el
    # orderby wikibase:sitelinks del bridge de Wikidata para el Louvre.
    uk = sorted([c for c in candidates if c["country"] == "uk"], key=lambda c: -len(c["track"]))
    fr = sorted([c for c in candidates if c["country"] == "fr"], key=lambda c: -len(c["track"]))
    if not fr:
        print(
            "ADVERTENCIA: no encontré ningún crucero francés con geometría completa — "
            "corré --explore-countries para confirmar cuántos hay disponibles en ese rango."
        )

    half = max_routes // 2
    selected_uk = uk[:half]
    selected_fr = fr[: max_routes - len(selected_uk)]
    selected = selected_uk + selected_fr

    features = []
    for c in selected:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "ship": c["ship"],
                    "company": c["company"],
                    "power": c["country"],
                    "date_start": c["date_start"],
                    "date_end": c["date_end"],
                    # FromYear/ToYear con el mismo nombre que usa
                    # colonial_overlay.geojson — así el front puede aplicar
                    # el mismo Layer.filter por año del timeline a las dos
                    # fuentes sin duplicar lógica.
                    "FromYear": c["year"],
                    "ToYear": c["year_end"],
                    "size": c["size"],
                },
                "geometry": {
                    "type": "LineString",
                    # Traza real (todas las posiciones registradas, ver
                    # extract_track), no una línea recta inicio->fin — una
                    # línea recta corta por tierra sin respetar la costa
                    # (confirmado a mano el 16/08 con una ruta UK->Indonesia
                    # que cruzaba Medio Oriente derecho).
                    "coordinates": [[round(lon, precision), round(lat, precision)] for lon, lat in c["track"]],
                },
            }
        )

    bundle = {"type": "FeatureCollection", "features": features}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(bundle, ensure_ascii=False))
    print(f"{len(features)} ruta(s) exportadas a {OUT_PATH} ({len(selected_uk)} UK, {len(selected_fr)} Francia)")
    print("Fuente: Jones, PD et al. (2007), CLIWOC release 2.1, PANGAEA — CC-BY 3.0")
    print("https://doi.org/10.1594/PANGAEA.611088")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--explore-countries",
        action="store_true",
        help="Cuenta bitácoras por país (vía Citation) y cuántas tienen geometría completa",
    )
    parser.add_argument(
        "--explore-companies",
        action="store_true",
        help="Diagnóstico secundario: lista valores de 'Company' (solo poblado para UK/Países Bajos)",
    )
    parser.add_argument("--export", action="store_true", help="Exporta el geojson filtrado de rutas UK/Francia")
    parser.add_argument("--min-year", type=int, default=1700)
    parser.add_argument("--max-year", type=int, default=1900)
    parser.add_argument(
        "--max-routes",
        type=int,
        default=50,
        help="Tope total de rutas a exportar (repartidas UK/Francia, priorizando bitácoras más completas)",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimales de coordenadas a conservar (~11m de resolución, de sobra a escala mundial)",
    )
    args = parser.parse_args()

    extract_dir = download_and_unzip()

    if args.explore_countries:
        explore_countries(extract_dir)
    elif args.explore_companies:
        explore_companies(extract_dir)
    elif args.export:
        export(extract_dir, args.min_year, args.max_year, args.max_routes, args.precision)
    else:
        parser.print_help()
