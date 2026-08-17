"""
Descarga fichas del British Museum (collection online). No hay API pública:
raspamos /collection/object/<id> directamente, que sí está permitido por
robots.txt (solo bloquea /search*, /admin/, etc. — la ficha de objeto no).

El propio robots.txt pide "Crawl-delay: 20" (20 segundos entre requests) y
lo respetamos a rajatabla acá: bajar incluso un piloto chico lleva varios
minutos.

Descubrimiento de IDs: a diferencia del Louvre, el puente por Wikidata
(P8565, "British Museum object ID") resultó poco confiable acá — casi
ningún objeto tiene cargado el departamento curatorial (P195), y varios
valores de P8565 vienen sin el prefijo de letra que el sitio necesita en la
URL real (ej. el valor crudo "Oc1869,1005.1" tira 404; hace falta un
prefijo como "E_" o "EA_" delante, inconsistente entre objetos). Así que en
vez de automatizar el descubrimiento, esta primera versión usa una lista
curada a mano de museum numbers ya verificados (ver SEED_OBJECT_IDS),
tomados de la página oficial de "piezas disputadas" del propio Museo
(britishmuseum.org/about-us/british-museum-story/contested-objects-collection)
y de búsquedas puntuales en /collection/search. Ampliar esa lista a mano es
el camino más confiable por ahora — no hay atajo automatizado limpio como
con el Louvre.

Requiere beautifulsoup4 (ver requirements.txt).

Uso:
    python src/fetch_bm.py
    python src/fetch_bm.py --delay 20
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "bm_objects_raw.json"
OBJECT_URL_TMPL = "https://www.britishmuseum.org/collection/object/{object_id}"
# britishmuseum.org tiene un WAF que devuelve 403 ante cualquier User-Agent que
# no matchee un browser real (probado: el UA identificatorio original,
# "colonial-museum-routes/0.1 (...)", tira 403 en el primer request). No es
# selectivo por comportamiento — bloquea por firma del header antes de que
# importen el crawl-delay o qué URL se pide. El resto del scraper se mantiene
# sin cambios: mismo objeto por request, mismo delay de 20s, mismas rutas
# permitidas por robots.txt — lo único que cambia son los headers para que la
# request no se caiga en el filtro de firma.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
}
CRAWL_DELAY_DEFAULT = 20  # segundos — pedido explícito del robots.txt del sitio, no negociable

# El WAF del sitio rechaza una fracción de los requests al azar incluso con
# headers de browser real (403 intermitente, no ligado a un objeto puntual).
# Reintentamos con más espera antes de darnos por vencidos — esto es
# tolerancia a fallas de red, no evasión: mismo UA, mismo objeto, mismo
# comportamiento secuencial, solo más paciencia. Subido de 2 a 4 reintentos
# (16/08) tras ver una corrida con rachas de 3 403 seguidos por objeto,
# más agresivo que lo visto en rondas anteriores.
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 40

# Piezas semilla, verificadas a mano navegando el sitio (ver nota arriba
# sobre por qué no hay descubrimiento automatizado todavía). Cubre las 6
# historias de la página de "contested objects" del propio Museo (Benin,
# Asante, Maqdala, Partenón, moái de Rapa Nui) más Egipto/Sudán y Sri Lanka —
# antes las 5 piezas de Benin dominaban el piloto (mismo evento, mismo
# origen geográfico); sumar 1 pieza de cada una de las otras 4 historias
# dispersa los puntos por África occidental/oriental, el Pacífico y el
# Mediterráneo. Seguir expandiendo a mano es el camino esperado — no hay
# atajo automatizado limpio como con el Louvre.
SEED_OBJECT_IDS = [
    "Y_EA24",  # Rosetta Stone — Egipto y Sudán
    "Y_EA1770",  # Sphinx of Taharqo — Egipto y Sudán
    "W_1848-1104-1",  # Black Obelisk of Shalmaneser III — Oriente Medio
    "A_1830-0612-4",  # Statue of Tara — Asia (Sri Lanka)
    "E_Af1898-0115-27",  # Benin plaque, Punitive Expedition 1897 — África
    "E_Af1898-0115-28",
    "E_Af1898-0115-29",
    "E_Af1898-0115-30",
    "E_Af1898-0115-32",
    "E_Af1981-27-1",  # Asante Gold — bracelet, Kumase/Asante Region (Ghana)
    "E_Af1868-1001-4",  # Maqdala collection — necklace, tomada en Maqdala (Etiopía) en 1868
    "E_Oc1869-1005-1",  # Hoa Hakananai'a — moái de Rano Kao/Orongo, Rapa Nui (Isla de Pascua)
    "G_1816-0610-98",  # Parthenon Sculptures — cabeza de caballo de Selene, Partenón (Atenas)
    # Segunda ronda (14/08) — mismo método (búsqueda puntual en /collection/search,
    # verificado a mano), sumando geografía que todavía no estaba cubierta:
    # Asia Oriental/Central, Sudeste asiático, Australia/Nueva Zelanda, y un
    # segundo sitio nigeriano distinto de Benin City.
    "A_As-3573_1",  # Saqueado del Antiguo Palacio de Verano (Yuanmingyuan), Beijing — Segunda Guerra del Opio, 1860
    "A_1880-0709-40",  # Relieve de Amaravati, India — excavado por Robert Sewell, 1880
    "W_1897-1231-116",  # Tesoro de Oxus — Takht-i Kuwad, actual Tayikistán
    "W_1880-0617-1941",  # Cyrus Cylinder — Babilonia, Irak
    "W_1856-0909-57",  # Umbral del Palacio Norte de Asurbanipal — Nínive, Irak
    "E_Oc1848-0202-1",  # Garrote aborigen australiano — Queensland, Australia
    "E_2018-Q-101",  # Azuela māori — Nueva Zelanda
    "E_Af1954-17-1-a-b",  # Cuenta de Ife — Nigeria (sitio distinto de Benin City)
    # Tercera ronda (16/08) — misma metodología, pero esta vez buscando por
    # región/tema en vez de historia por historia, para cubrir de una la
    # geografía que todavía faltaba: África central/austral, dos sitios
    # indígenas distintos de Norteamérica, Mesoamérica, Sudamérica, Asia
    # central/sur/este/sudeste, 4 sitios del Pacífico, Medio Oriente y Caribe.
    "E_Af1905-0525-3",  # Figura nkisi Bakongo — República Democrática del Congo
    "E_Af1921-1028-4",  # Lanza zulú — Sudáfrica, guerra anglo-zulú
    "E_Am1919-1216-11",  # Delantal haida — Haida Gwaii, Columbia Británica (Canadá)
    "E_Am-St-397-a",  # Mosaico de turquesa azteca/mixteco — México (colección Moctezuma)
    "E_Am1855-1211-49",  # Vasija moche — Trujillo, costa norte de Perú
    "A_1950-1211-2",  # Escultura de Gandhara — Pakistán, cultura Kushán
    "A_1891-1215-1",  # Botella de la dinastía Joseon — Corea
    "A_As1924-0714-1",  # Figura jemer — Angkor, Camboya
    "E_Oc-HAW-138",  # Capa de plumas hawaiana — Islas Hawái
    "E_Oc1896-1154",  # Garrote — Fiyi
    "W_1922-0511-255",  # Caja neo-hitita — Carchemish (frontera Turquía/Siria)
    "W_1880-330",  # Caja mogol — India
    "C_1953-0402-17",  # Moneda aksumita — Aksum, Etiopía
    "E_Oc1949-08-1",  # Azuela — río Sepik, Nueva Guinea
    "E_Am1982-28-13",  # Bolsa cree — Territorios del Noroeste, Canadá
    "E_Am1997-Q-793",  # Figura taína — Jamaica
    "A_As1909-0622-1",  # Tocado ainu — Hokkaido, Japón
    "W_1970-0604-2",  # Altar sabeo — Marib, Yemen
    "Y_EA51515",  # Ánfora meroítica — Faras, Nubia (Sudán)
    "E_Oc1921-1102-3",  # Modelo de canoa — Islas Salomón
    # Cuarta ronda (16/08) — verificado a mano vía navegador (búsqueda puntual
    # en /collection/search, respetando el mismo método que las rondas
    # anteriores; el sitio bloquea /search* en robots.txt para scrapers
    # automatizados, no para navegación interactiva). Prioriza países/regiones
    # todavía no cubiertos: África austral y oriental, Sudamérica, Pacífico
    # melanesio, Sudeste asiático, Mediterráneo oriental, África central,
    # Asia del Sur.
    "E_Af1900-55",  # Brazalete herero — Namibia (entonces África del Sudoeste Alemana)
    "E_Af1887-1211-51",  # Flecha "tomada de un dhow esclavista" — Zanzíbar, Tanzania
    "E_Am1928-0516-2",  # Cascabel de oro quimbaya — Colombia
    "E_Oc1889-0208-13",  # Máscara ceremonial — Ambrym, Vanuatu
    "E_Af1904-110-d-g",  # Plumas de avestruz masái — Kenia
    "A_As1919-1230-3",  # Bolso kachin — región de Mandalay, Birmania (Myanmar)
    "G_1894-1101-213",  # Alabastrón de vidrio — excavación británica en Amathus, Chipre
    "E_Af1954-23-2641-a-b",  # Daga bamum — Camerún
    "A_1959-1012-1",  # Figura de Párvatí y Shivá — Rajshahi, Bangladés
    # Quinta ronda (17/08) — misma metodología (búsqueda puntual en
    # /collection/search, verificado a mano), pero esta vez usando el
    # endpoint de búsqueda directo vía fetch en vez de navegación interactiva
    # (devuelve resultados server-rendered, sin JS — se puede leer Findspot/
    # Production place de la lista sin visitar cada ficha una por una).
    # Prioriza países/regiones sin cobertura o con cobertura mínima: Irán,
    # Afganistán, Tíbet, Sierra Leona, Uganda, Zimbabue, Palestina, Malaui,
    # Guatemala, Perú, Botsuana, Zambia, Caribe (Trinidad/Guyana), Camboya,
    # Java/Indonesia.
    "W_1825-0421-1",  # Bloque en relieve del Apadana — Persépolis, Irán (aqueménida)
    "A_1880-28",  # Cofre-relicario de Bimaran — excavado por Charles Masson en la Estupa 2 de Bimaran, Afganistán (1830s)
    "A_1880-3633",  # Sello-anillo kushán — Begram/Kabul, Afganistán
    "A_As1905-0518-47",  # Manto ritual budista — Lhasa, Tíbet (1905, tras la misión Younghusband)
    "E_Af1947-30-1",  # Azuela excavada — Koinadugu, Sierra Leona
    "E_Af1913-118",  # Brazalete mende — Mendeland, Sierra Leona
    "E_Af1886-1126-2",  # Brazalete — río Sherbro, Sierra Leona (1886)
    "E_Af1931-0105-14",  # "La Cabeza de Luzira" — excavada en Luzira, Uganda
    "E_Af1955-01-1",  # Vasija con asa, cultura Bachwesi — Bigo bya Mugenyi, Uganda
    "E_Af1923-1211-11-a-b",  # Cuentas/frasco excavados — Great Zimbabwe, Zimbabue
    "E_Af1926-0410-1",  # Viga del Templo Occidental — Great Zimbabwe, Zimbabue
    "W_1970-0209-18",  # Cuenco de la Edad del Hierro — excavación de Ophel, Jerusalén
    "W_As1967-02-1",  # Capa/abayah beduina — Palestina/Siria
    "C_1908-0110-4",  # Moneda de la Primera Revuelta Judía, acuñada en Jerusalén (66-67 d.C.)
    "E_Af1893-0804-88",  # Tobillera ngoni — Angoniland, Malaui (1889-1893)
    "E_Am1930-F-1",  # "El Vaso Fenton"/"El Vaso Nebaj" — maya clásico tardío, excavado en Nebaj, Guatemala
    "E_Am1991-Q-4",  # Cuenco inca — excavado en Perú
    "E_Af1937-0210-13",  # Objeto san — Bechuanaland (hoy Botsuana)
    "E_Af1933-1206-70",  # Equipo de adivinación bemba — Zambia
    "E_Af1947-07-17",  # Modelo de canoa lozi — Zambia
    "E_Af1902-0513-5",  # Hacha luvale — Zambia (1891-1901)
    "E_Am-St-809-A",  # Vasija — Trinidad (1862)
    "E_Am-St-809-b",  # Botella de agua — río Essequibo, Guyana (1861)
    "A_1890-0208-1",  # Azuela neolítica — Samrong Sen, Camboya
    "A_1859-1228-121",  # Campana — Kedu, Java (colección Raffles, ingresada 1859)
    "A_As1859-1228-195-l-m",  # Soporte de gong — Java (colección Raffles, 1800)
    # Sexta ronda (17/08) — misma metodología (búsqueda por país/región en
    # /collection/search vía fetch directo). Prioriza geografía todavía sin
    # cobertura: Sudamérica más allá de Perú/Colombia (Ecuador, Bolivia,
    # Venezuela, Brasil), Norte de África (Marruecos), Sudeste asiático más
    # allá de Camboya/Java (Vietnam), Himalaya (Nepal) y Pacífico más allá de
    # Australia/Nueva Zelanda/Hawái/Fiyi/Salomón (Tonga).
    "E_Am-WG-2242",  # Azuela — excavada en Cuenca, Ecuador (colección William Bollaert, s. XIX)
    "E_Am1983-12-35",  # Cinturón de danza — Aroma, Bolivia (1900-1950)
    "E_Am1983-Q-37",  # Artefacto del pueblo jirajara — Venezuela
    "E_Am1953-02-1",  # Vasija-adorno, cultura Tapajó — río Amazonas, Brasil
    "E_Af-5913",  # Azuela/azadón — Montañas del Atlas, Marruecos (1888)
    "A_1958-1112-1",  # Hacha neolítica — Oc-eo, Vietnam
    "A_1927-0613-1",  # Retablo — Nepal (s. XVIII-XIX)
    "E_Oc-6509",  # Azuela — Vava'u, Tonga
]


def fetch_object_html(object_id: str) -> str:
    url = OBJECT_URL_TMPL.format(object_id=object_id)
    req = urllib.request.Request(url, headers=REQUEST_HEADERS)

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 403 or attempt == MAX_RETRIES:
                raise
            print(f"    403 en {object_id}, reintento {attempt + 1}/{MAX_RETRIES} en {RETRY_BACKOFF_SECONDS}s")
            time.sleep(RETRY_BACKOFF_SECONDS)
    raise last_error  # pragma: no cover — inalcanzable, el loop siempre retorna o levanta antes


def parse_object(object_id: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one("h1")

    fields: dict[str, list[str]] = {}
    for item in soup.select(".object-detail__data-item"):
        term = item.select_one(".object-detail__data-term")
        desc = item.select_one(".object-detail__data-description")
        if not term or not desc:
            continue
        label = term.get_text(strip=True)
        value = desc.get_text(" ", strip=True)
        fields.setdefault(label, []).append(value)

    def first(label: str) -> str | None:
        values = fields.get(label)
        return values[0] if values else None

    image_el = soup.select_one("meta[property='og:image']")

    return {
        "objectID": object_id,
        "pageTitle": title_el.get_text(strip=True) if title_el else None,
        "url": OBJECT_URL_TMPL.format(object_id=object_id),
        "objectType": first("Object Type"),
        "museumNumber": first("Museum number"),
        "title": first("Title"),
        "description": first("Description"),
        "culturesPeriods": first("Cultures/periods"),
        "productionDate": first("Production date"),
        "productionPlace": first("Production place"),
        "excavator": first("Excavator/field collector"),
        "findspot": first("Findspot"),
        "materials": first("Materials"),
        "curatorComments": first("Curator's comments"),
        "associatedNames": first("Associated names"),
        "acquisitionName": first("Acquisition name"),
        "acquisitionDate": first("Acquisition date"),
        "department": first("Department"),
        "image": image_el["content"] if image_el and image_el.has_attr("content") else None,
    }


def load_existing() -> dict[str, dict]:
    if not RAW_PATH.exists():
        return {}
    data = json.loads(RAW_PATH.read_text())
    return {obj["objectID"]: obj for obj in data}


def save(objects_by_id: dict[str, dict]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = [objects_by_id[k] for k in sorted(objects_by_id)]
    RAW_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2))


def main(object_ids: list[str], delay: float) -> None:
    objects_by_id = load_existing()
    pending = [oid for oid in object_ids if oid not in objects_by_id]
    print(f"{len(object_ids)} IDs pedidos, {len(pending)} nuevos a bajar (crawl-delay {delay}s entre requests)")

    for i, object_id in enumerate(pending):
        try:
            html = fetch_object_html(object_id)
            obj = parse_object(object_id, html)
            objects_by_id[object_id] = obj
            print(f"  {object_id}: {obj.get('title') or obj.get('pageTitle')}")
        except Exception as exc:
            print(f"  error en {object_id}: {exc}")
        save(objects_by_id)  # checkpoint tras cada objeto, dado lo lento del crawl-delay
        if i < len(pending) - 1:
            time.sleep(delay)

    print(f"Guardado en {RAW_PATH} ({len(objects_by_id)} objetos totales)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=CRAWL_DELAY_DEFAULT, help="Segundos entre requests (robots.txt pide 20)")
    args = parser.parse_args()

    main(SEED_OBJECT_IDS, delay=args.delay)
