"""
Descarga y filtra Cliopatria (Seshat Global History Databank) para extraer los
polígonos del Imperio Británico y el Imperio Colonial Francés en un año dado,
como capa de contexto visual en el mapa — territorios que alguna vez fueron
colonia de UK o Francia, de fondo, para que se entienda por qué las líneas del
BM y el Louvre van a donde van.

Esto NO es parte del modelo de datos de 3 capas (layer 1/2/3): es un layer de
contexto histórico general, no ligado a ninguna pieza puntual, y vive aparte
en web/src/data/colonial_overlay.geojson.

Fuente: https://github.com/Seshat-Global-History-Databank/cliopatria
Licencia: CC-BY 4.0 — atribuir "Seshat Global History Databank — Cliopatria"
con link a https://github.com/Seshat-Global-History-Databank/cliopatria en el
README/CLAUDE.md y, idealmente, en un crédito visible en la app.

Por qué EEUU queda afuera: el Met no adquirió sus piezas porque EEUU
controlara los territorios de origen (Egipto, Medio Oriente, África, Asia) —
las consiguió por mercado internacional de antigüedades, misiones de
excavación autorizadas por la potencia colonial de turno, donantes ricos. El
fenómeno relevante para el Met es otro (mercado del arte global), no
expansión territorial estadounidense — decisión tomada explícitamente con el
usuario, ver conversación del 16/08.

Uso:
    # Explorar qué nombres de entidad usa el dataset para UK/Francia y en qué
    # rangos de año aparecen (útil si Cliopatria cambia su nomenclatura):
    python src/fetch_colonial_overlay.py --explore

    # Snapshot de un solo año:
    python src/fetch_colonial_overlay.py --export --year 1920

    # Timeline completo — exporta TODOS los polígonos de las entidades
    # coloniales (no las de "régimen"/metrópoli) entre --min-year y --max-year,
    # cada uno con su FromYear/ToYear, para que el front filtre por año con un
    # slider en vez de mostrar un snapshot fijo:
    python src/fetch_colonial_overlay.py --export-timeline --min-year 1700 --max-year 2020
"""

import argparse
import json
import urllib.request
import zipfile
from pathlib import Path

ZIP_URL = "https://github.com/Seshat-Global-History-Databank/cliopatria/raw/main/cliopatria.geojson.zip"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
ZIP_PATH = CACHE_DIR / "cliopatria.geojson.zip"
GEOJSON_PATH = CACHE_DIR / "cliopatria.geojson"
OUT_PATH = Path(__file__).resolve().parent.parent / "web" / "public" / "colonial_overlay.geojson"

# Entidades "coloniales" (territorio de ultramar) en vez de las de "régimen"
# (Kingdom of France, French Third Republic, etc. — esas representan la
# metrópoli sola, no el imperio).
#
# Bug encontrado el 18/08 (reportado por la usuaria: "las excolonias
# inglesas en África no están marcadas en el mapa"): el comentario original
# acá decía que para UK alcanzaba con 2 entidades porque "British Colonial
# Empire" ya cubre casi todo el rango 1706-1999 — nunca se verificó esa
# afirmación contra África específicamente, a diferencia del lado francés,
# que sí se armó sumando cada colonia por región desde el principio.
# Resultado: "British Colonial Empire" en Cliopatria NO incluye África
# continental en absoluto (se verificó con --explore + inspección de bounding
# boxes) — el mismo patrón que "French Africa" (ya incluida abajo) tiene su
# equivalente británico en 3 entidades separadas que faltaban:
#   - "British Africa" (1885-1960): el grueso del período colonial africano.
#   - "British Cape Colony" (1796-1884): Sudáfrica antes de que "British
#     Africa" empiece a cubrirla.
#   - "British East Africa" (1961-1972): pese al nombre, no es la etapa
#     "East Africa" clásica (Kenia/Uganda/Tanganica ya independientes para
#     1964) — los polígonos corresponden a Suazilandia (hasta 1968) y
#     Seychelles (hasta 1976), los últimos territorios británicos en la
#     región tras la ola de independencias de 1960-64. Verificado por
#     bounding box antes de incluirla, no por el nombre solo.
UK_COLONIAL_NAMES = ["British Colonial Empire", "British Raj", "British Africa", "British Cape Colony", "British East Africa"]
FR_COLONIAL_NAMES = [
    "French Africa",
    "French Indochina",
    "French India",
    "French Algiers",
    "French Equatorial Africa",
    "French Mandate for Syria and Lebanon",
    "French Louisiana",
    "French Colony of Guiana",
    "New France",
    "France Antarctique",
    "First French colonial empire",
]


def download_and_unzip() -> None:
    if GEOJSON_PATH.exists():
        print(f"Ya existe {GEOJSON_PATH}, no vuelvo a bajar (borrala si querés forzar la descarga de nuevo)")
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Bajando {ZIP_URL} ...")
    urllib.request.urlretrieve(ZIP_URL, ZIP_PATH)
    print(f"Descomprimiendo en {CACHE_DIR} ...")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        # el zip trae cliopatria.geojson en la raíz
        for name in zf.namelist():
            if name.endswith(".geojson"):
                with zf.open(name) as src, GEOJSON_PATH.open("wb") as dst:
                    dst.write(src.read())
                break
    print(f"Listo: {GEOJSON_PATH}")


def load_features() -> list[dict]:
    data = json.loads(GEOJSON_PATH.read_text())
    return data["features"]


def round_coords(coords, ndigits: int):
    """Redondea recursivamente una estructura de coordenadas GeoJSON (Polygon/
    MultiPolygon anidan listas hasta 4 niveles de profundidad antes de llegar
    a [lon, lat]). Cliopatria trae precisión float64 completa (~17 dígitos
    significativos, ej. 55.63078308105469) que no aporta nada a esta escala —
    el mapa es un globo a nivel mundial, no hay zoom a nivel calle. Bajar a
    ~4 decimales (once metros de resolución) es la principal palanca para
    reducir el tamaño del geojson exportado: domina el peso del archivo mucho
    más que la cantidad de features o el rango de años pedido (ver nota en
    export_timeline)."""
    if isinstance(coords[0], (int, float)):
        return [round(c, ndigits) for c in coords]
    return [round_coords(c, ndigits) for c in coords]


def explore(keyword_filters: list[str]) -> None:
    features = load_features()
    seen: dict[str, list[tuple[int, int]]] = {}
    for f in features:
        props = f.get("properties", {})
        name = props.get("Name") or props.get("NAME") or ""
        if not any(kw.lower() in name.lower() for kw in keyword_filters):
            continue
        from_year = props.get("FromYear")
        to_year = props.get("ToYear")
        seen.setdefault(name, []).append((from_year, to_year))

    if not seen:
        print("No encontré ninguna entidad que matchee los keywords. Revisá los nombres de propiedades del geojson a mano (json.load + mirar 'properties' del primer feature).")
        return

    for name in sorted(seen):
        ranges = sorted(seen[name], key=lambda r: (r[0] is None, r[0]))
        range_str = ", ".join(f"{a}-{b}" for a, b in ranges)
        print(f"{name!r}: {len(ranges)} polígono(s) — años {range_str}")


def export(uk_names: list[str], fr_names: list[str], year: int, precision: int) -> None:
    features = load_features()
    matched = []
    for f in features:
        props = f.get("properties", {})
        name = props.get("Name") or props.get("NAME") or ""
        if name in uk_names:
            power = "uk"
        elif name in fr_names:
            power = "fr"
        else:
            continue
        from_year = props.get("FromYear")
        to_year = props.get("ToYear")
        if from_year is None or to_year is None:
            continue
        if from_year <= year <= to_year:
            f["properties"] = {"Name": name, "power": power, "FromYear": from_year, "ToYear": to_year}
            f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"], precision)
            matched.append(f)

    if not matched:
        raise SystemExit(
            f"No encontré polígonos para {uk_names!r} ni {fr_names!r} en el año {year}. "
            "Corré --explore primero para confirmar el nombre exacto y el rango de años disponible."
        )

    bundle = {"type": "FeatureCollection", "features": matched}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(bundle, ensure_ascii=False))
    print(f"{len(matched)} polígono(s) exportados a {OUT_PATH} (año {year})")
    print("Fuente: Seshat Global History Databank — Cliopatria (CC-BY 4.0)")
    print("https://github.com/Seshat-Global-History-Databank/cliopatria")


def export_timeline(min_year: int, max_year: int, precision: int) -> None:
    """
    A diferencia de export(), no filtra por un año puntual: agarra TODOS los
    polígonos de las entidades coloniales (UK_COLONIAL_NAMES/FR_COLONIAL_NAMES)
    cuyo rango [FromYear, ToYear] se solape con [min_year, max_year], y los
    junta en un único geojson. Cada feature conserva su FromYear/ToYear —
    el front filtra por año con un slider usando esos campos directamente
    (ver Layer filter en App.tsx), sin necesidad de volver a correr este
    script cada vez que se quiere ver un año distinto.

    Angostar [min_year, max_year] no reduce mucho el tamaño del archivo: casi
    todas las entidades (ej. British Colonial Empire, 90/221 features) ya
    caen dentro de cualquier rango razonable, salvo New France (18 features,
    1700-1791) si se arranca después de 1791. Lo que realmente pesa es la
    precisión de las coordenadas (~217k pares de coordenadas a precisión
    float64 completa) — por eso se redondean acá con `precision`, no
    filtrando años de más.
    """
    features = load_features()
    matched = []
    for f in features:
        props = f.get("properties", {})
        name = props.get("Name") or props.get("NAME") or ""
        if name in UK_COLONIAL_NAMES:
            power = "uk"
        elif name in FR_COLONIAL_NAMES:
            power = "fr"
        else:
            continue
        from_year = props.get("FromYear")
        to_year = props.get("ToYear")
        if from_year is None or to_year is None:
            continue
        if to_year < min_year or from_year > max_year:
            continue  # sin solapamiento con el rango pedido
        f["properties"] = {"Name": name, "power": power, "FromYear": from_year, "ToYear": to_year}
        f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"], precision)
        matched.append(f)

    if not matched:
        raise SystemExit("No encontré ningún polígono en ese rango — revisá UK_COLONIAL_NAMES/FR_COLONIAL_NAMES contra --explore.")

    bundle = {"type": "FeatureCollection", "features": matched}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(bundle, ensure_ascii=False))
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"{len(matched)} polígono(s) exportados a {OUT_PATH} ({size_kb:.0f} KB) — rango {min_year}-{max_year}")
    print("Fuente: Seshat Global History Databank — Cliopatria (CC-BY 4.0)")
    print("https://github.com/Seshat-Global-History-Databank/cliopatria")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--explore", action="store_true", help="Lista nombres de entidad UK/Francia y sus rangos de año")
    parser.add_argument("--export", action="store_true", help="Exporta el geojson filtrado para un año dado (snapshot fijo)")
    parser.add_argument("--export-timeline", action="store_true", help="Exporta todos los polígonos entre --min-year y --max-year, con FromYear/ToYear, para el slider del front")
    parser.add_argument(
        "--uk-name",
        default=",".join(UK_COLONIAL_NAMES),
        help="Nombre(s) exactos de entidad UK para --export, separados por coma si son varios (ver --explore)",
    )
    parser.add_argument(
        "--fr-name",
        default=",".join(FR_COLONIAL_NAMES),
        help="Nombre(s) exactos de entidad Francia para --export, separados por coma si son varios (ver --explore)",
    )
    parser.add_argument("--year", type=int, default=1920, help="Año del snapshot a exportar (con --export)")
    parser.add_argument("--min-year", type=int, default=1700, help="Año mínimo del timeline (con --export-timeline)")
    parser.add_argument("--max-year", type=int, default=2020, help="Año máximo del timeline (con --export-timeline)")
    parser.add_argument(
        "--keywords",
        default="british,united kingdom,france,french",
        help="Keywords para --explore, separados por coma (ej. 'mesopotamia,iraq,palestine,mandate' para buscar mandatos)",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimales de coordenadas a conservar (con --export/--export-timeline). 4 = ~11m de resolución, de sobra para un mapa mundial — Cliopatria trae float64 completo (~17 dígitos) que solo infla el archivo sin aportar nada a esta escala.",
    )
    args = parser.parse_args()

    download_and_unzip()

    if args.explore:
        explore([k.strip() for k in args.keywords.split(",")])
    elif args.export_timeline:
        export_timeline(args.min_year, args.max_year, args.precision)
    elif args.export:
        export(args.uk_name.split(","), args.fr_name.split(","), args.year, args.precision)
    else:
        parser.print_help()
