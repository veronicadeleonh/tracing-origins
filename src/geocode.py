"""
Geocodificación estática (sin llamadas a Nominatim en bulk, prohibido por su
política de uso). Tabla de coordenadas armada a mano, a expandir a medida que
aparecen nuevos países/regiones en los datos.

Prioridad de resolución: subregion > region > country.
"""

from __future__ import annotations

import re

# Coordenadas del propio museo (destino de las líneas)
MET_COORDS = (40.7794, -73.9632)
LOUVRE_COORDS = (48.8606, 2.3376)
BM_COORDS = (51.5194, -0.1270)


def _keyword_matches(keyword: str, haystack: str) -> bool:
    """
    Match de keyword contra texto libre, con límites de palabra (\\b) en vez
    de simple substring `in`. Encontrado el 17/08 al investigar el Zodiaque
    de Dendéra (louvre:cl010028871): con substring plano, la keyword "Ur"
    (Mesopotamia) matcheaba dentro de "sur" (francés, "sobre") en el texto
    crudo del placeOfDiscovery, mandando la pieza a Irak en vez de Egipto —
    y el mismo bug afectaba a cualquier pieza real de Uruk, porque "Ur"
    aparece antes que "Uruk" en LOUVRE_SITE_COORDS y "ur" es substring de
    "uruk" también. Con keywords cortas (Ur, Tyr, Mari, Ife, Java, Peru,
    Iran...) el riesgo de falso positivo dentro de otra palabra es real en
    cualquiera de las 5 listas de keywords (Met CULTURE_KEYWORDS, Louvre
    SITE/COUNTRY, BM SITE/COUNTRY) — \\b corta ese problema para todas sin
    afectar el matching legítimo de keywords multi-palabra.
    """
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, haystack, re.IGNORECASE) is not None

# ---------------------------------------------------------------------------
# Traducción al español para lo que se muestra en la ficha de cada pieza
# ("Hecho en <origin_label>" en ObjectDetail.tsx). Los tres museos matchean
# contra texto crudo en su idioma de origen (inglés para Met/BM, francés
# para Louvre) — esa palabra clave NUNCA se traduce, porque tiene que seguir
# matcheando el dato tal cual viene. Lo que se traduce es solo lo que ve el
# usuario al final: resolve_origin()/resolve_origin_louvre()/resolve_origin_bm()
# le pasan el nombre resuelto a es_label() antes de devolverlo. Si un nombre
# no está en este diccionario, se muestra tal cual (la mayoría de los sitios
# arqueológicos son nombres propios que no cambian entre idiomas — solo vale
# la pena traducir los que tienen un exónimo español distinto y establecido).
ES_NAMES: dict[str, str] = {
    # Países — formas en inglés (Met, BM)
    "Egypt": "Egipto",
    "United States": "Estados Unidos",
    "Democratic Republic of the Congo": "República Democrática del Congo",
    "Democratic Republic of Congo": "República Democrática del Congo",
    "Mexico": "México",
    "Japan": "Japón",
    "Iran": "Irán",
    "Iraq": "Irak",
    "Turkey": "Turquía",
    "Greece": "Grecia",
    "Italy": "Italia",
    "France": "Francia",
    "Sudan": "Sudán",
    "Ethiopia": "Etiopía",
    "Syria": "Siria",
    "Cyprus": "Chipre",
    "present-day Uzbekistan": "Uzbekistán",
    "probably Iran": "Irán (probable)",
    "Côte d'Ivoire": "Costa de Marfil",
    "central Côte d'Ivoire": "centro de Costa de Marfil",
    "Papua New Guinea": "Papúa Nueva Guinea",
    "Benin": "Benín",
    "Mali": "Malí",
    "Cameroon": "Camerún",
    "Easter Island": "Isla de Pascua",
    "New Zealand": "Nueva Zelanda",
    "Tajikistan": "Tayikistán",
    "South Africa": "Sudáfrica",
    "Korea": "Corea",
    "Cambodia": "Camboya",
    "Pakistan": "Pakistán",
    "New Guinea": "Nueva Guinea",
    "Fiji": "Fiyi",
    "Solomon Islands": "Islas Salomón",
    "Canada": "Canadá",
    "Kenya": "Kenia",
    "Bangladesh": "Bangladés",
    # Países/regiones — formas en francés (Louvre)
    "Chypre": "Chipre",
    "Égypte": "Egipto",
    "Egypte": "Egipto",
    "Irak": "Irak",
    "Turquie": "Turquía",
    "Grèce": "Grecia",
    "Etrurie": "Etruria",
    "Étrurie": "Etruria",
    "Italie": "Italia",
    "Syrie": "Siria",
    "Espagne": "España",
    "Maroc": "Marruecos",
    "Liban": "Líbano",
    "Ouzbékistan": "Uzbekistán",
    "Inde": "India",
    "Indonésie": "Indonesia",
    "Anatolie": "Anatolia",
    "Mésopotamie": "Mesopotamia",
    "Proche-Orient": "Cercano Oriente",
    "Levant": "Levante",
    "Perse": "Persia",
    "Babylonie": "Babilonia (región)",
    "Sumer": "Sumeria",
    "Tunisie": "Túnez",
    "Sicile": "Sicilia",
    # Regiones históricas/egipcias del Met (subregion/region, texto compuesto)
    "Memphite Region": "Región menfita",
    "Northern Upper Egypt": "Alto Egipto septentrional",
    "Southern Upper Egypt": "Alto Egipto meridional",
    "Eastern Delta": "Delta oriental",
    "Mesopotamia": "Mesopotamia",
    "Northern Syria or eastern Anatolia": "norte de Siria o este de Anatolia",
    "Iran, Luristan": "Irán, Luristán",
    "Bactria-Margiana or eastern Iran": "Bactriana-Margiana o este de Irán",
    "Iberian Peninsula": "península ibérica",
    "Mesopotamia or Iran": "Mesopotamia o Irán",
    "Mesoamerica": "Mesoamérica",
    "Middle East": "Medio Oriente",
    "Dendera area": "área de Dendera",
    "probably from Kültepe (Karum Kanesh)": "posiblemente de Kültepe (Karum Kanesh)",
    "probably from Acemhöyük": "posiblemente de Acemhöyük",
    "said to be from Ziwiye": "presuntamente de Ziwiye",
    # Sitios con exónimo español establecido (los tres museos)
    "Babylon": "Babilonia",
    "Babylone": "Babilonia",
    "Nineveh": "Nínive",
    "Ninive": "Nínive",
    "Rome": "Roma",
    "Parthenon": "Partenón",
    "Kumase": "Kumasi",
    "Asante Region": "Región Asante",
    "Sepik River": "Río Sepik",
    "Hawaiian Islands": "Islas Hawái",
    "Hawaii": "Hawái",
    "Northwest Territories": "Territorios del Noroeste",
    "Thèbes": "Tebas",
    "Dendéra": "Dendera",
    "Denderah": "Dendera",
    "Athènes": "Atenas",
    "Assur": "Asur",
    "Baalbeck": "Baalbek",
    "Assyrie": "Asiria",
    "Luristan": "Luristán",
    "Louxor": "Luxor",
    "Assiout": "Asiut",
    "Assouan": "Asuán",
    "Éléphantine": "Elefantina",
    "Kôm Ombo": "Kom Ombo",
    "Abou Roach": "Abu Roash",
    "Abou Rawach": "Abu Rawash",
    "Méroé": "Meroe",
    "Suse": "Susa",
    "Nimroud": "Nimrud",
    "Mari sur l'Euphrate": "Mari, sobre el Éufrates",
    "Ougarit": "Ugarit",
    "Byblos": "Biblos",
    "Megiddo": "Meguido",
    "Mégiddo": "Meguido",
    "Palmyre": "Palmira",
    "Kultépé": "Kültepe",
    "Bactres": "Bactra",
    "Samothrace": "Samotracia",
    "Delphes": "Delfos",
    "Olympie": "Olimpia",
    "Cnide": "Cnido",
    "Rhodes": "Rodas",
    "Herculanum": "Herculano",
    "Pompéi": "Pompeya",
    "Antioche": "Antioquía",
    "Mélos": "Melos",
    "Éleutherne": "Eleuterna",
    "Benghazi": "Bengasi",
    "Pharsale": "Farsala",
    "Tyr": "Tiro",
}


def es_label(raw: str) -> str:
    """Traduce un nombre resuelto (site/country/region ya matcheado) al
    español si tenemos un exónimo cargado en ES_NAMES; si no, lo devuelve
    tal cual. Nunca se usa para matchear texto crudo — solo para lo que se
    muestra al final en la ficha de la pieza."""
    return ES_NAMES.get(raw, raw)


# ---------------------------------------------------------------------------
# Traducción al inglés (toggle ES/EN, ampliado el 17/08 — ver CLAUDE.md,
# "Pendiente de decidir"). Mismo mecanismo que ES_NAMES: el Met usa
# subregion/region/country tal cual vienen de su API (ya en inglés), así que
# la gran mayoría de sus labels no necesitan entrada acá — el fallback (raw
# sin traducir) YA es inglés correcto. Lo que sí necesita traducción real es
# el Louvre (sus claves son texto francés) — de ahí que EN_NAMES tenga casi
# las mismas claves que el bloque francés de ES_NAMES, pero con destino
# inglés en vez de español. El BM NO usa este diccionario en absoluto desde
# el 17/08: sus tablas (BM_SITE_COORDS/BM_COUNTRY_KEYWORDS) pasaron a
# 4-tuplas con display_es/display_en explícitos, porque sus "display" ya
# venían mezclados (algunos en inglés crudo, otros ya traducidos a mano al
# español en rondas anteriores) — meterlos en un diccionario compartido
# hubiera requerido las mismas ~90 traducciones ad-hoc, así que se optó por
# la fuente explícita en vez de una capa de indirección.
EN_NAMES: dict[str, str] = {
    # Países/regiones — formas en francés (Louvre)
    "Chypre": "Cyprus",
    "Égypte": "Egypt",
    "Egypte": "Egypt",
    "Irak": "Iraq",
    "Turquie": "Turkey",
    "Grèce": "Greece",
    "Etrurie": "Etruria",
    "Étrurie": "Etruria",
    "Italie": "Italy",
    "Syrie": "Syria",
    "Espagne": "Spain",
    "Maroc": "Morocco",
    "Liban": "Lebanon",
    "Ouzbékistan": "Uzbekistan",
    "Inde": "India",
    "Indonésie": "Indonesia",
    "Anatolie": "Anatolia",
    "Mésopotamie": "Mesopotamia",
    "Proche-Orient": "Near East",
    "Perse": "Persia",
    "Babylonie": "Babylonia (region)",
    "Tunisie": "Tunisia",
    "Sicile": "Sicily",
    # Sitios del Louvre con ortografía francesa distinta de la inglesa
    "Deir el-Médineh": "Deir el-Medina",
    "Thèbes": "Thebes",
    "Dendéra": "Dendera",
    "Denderah": "Dendera",
    "Athènes": "Athens",
    "Baalbeck": "Baalbek",
    "Assyrie": "Assyria",
    "Louxor": "Luxor",
    "Assiout": "Asyut",
    "Assouan": "Aswan",
    "Éléphantine": "Elephantine",
    "Médamoud": "Medamud",
    "Tôd": "Tod",
    "Kôm Ombo": "Kom Ombo",
    "Abou Roach": "Abu Rawash",
    "Abou Rawach": "Abu Rawash",
    "Méroé": "Meroe",
    "Suse": "Susa",
    "Persépolis": "Persepolis",
    "Ninive": "Nineveh",
    "Nimroud": "Nimrud",
    "Babylone": "Babylon",
    "Mari sur l'Euphrate": "Mari, on the Euphrates",
    "Ougarit": "Ugarit",
    "Mégiddo": "Megiddo",
    "Palmyre": "Palmyra",
    "Kultépé": "Kültepe",
    "Bactres": "Bactra",
    "Délos": "Delos",
    "Delphes": "Delphi",
    "Olympie": "Olympia",
    "Cnide": "Cnidus",
    "Cervéteri": "Cerveteri",
    "Herculanum": "Herculaneum",
    "Pompéi": "Pompeii",
    "Antioche": "Antioch",
    "Mélos": "Melos",
    "Diban": "Dhiban",
    "Éleutherne": "Eleutherna",
    "Pharsale": "Pharsalus",
    "Tyr": "Tyre",
}


def en_label(raw: str) -> str:
    """Equivalente en inglés de es_label() — mismo criterio: si no hay
    traducción cargada, se devuelve el texto crudo tal cual (para el Met
    esto casi siempre ya es inglés correcto, así que el diccionario queda
    corto a propósito)."""
    return EN_NAMES.get(raw, raw)

# Países modernos (centroides aproximados, suficiente para un mapa de rutas)
COUNTRY_COORDS = {
    "Egypt": (26.8206, 30.8025),
    "United States": (39.8283, -98.5795),
    "Guatemala": (15.7835, -90.2308),
    "Peru": (-9.1900, -75.0152),
    "Colombia": (4.5709, -74.2973),
    "Democratic Republic of the Congo": (-4.0383, 21.7587),
    "Mexico": (23.6345, -102.5528),
    "China": (35.8617, 104.1954),
    "Japan": (36.2048, 138.2529),
    "India": (20.5937, 78.9629),
    "Iran": (32.4279, 53.6880),
    "Iraq": (33.2232, 43.6793),
    "Turkey": (38.9637, 35.2433),
    "Greece": (39.0742, 21.8243),
    "Italy": (41.8719, 12.5674),
    "France": (46.6034, 1.8883),
    "Nigeria": (9.0820, 8.6753),
    "Sudan": (12.8628, 30.2176),
    "Ethiopia": (9.1450, 40.4897),
    "Syria": (34.8021, 38.9968),
    "Cyprus": (35.1264, 33.4299),
    "present-day Uzbekistan": (41.3775, 64.5853),
    "probably Iran": (32.4279, 53.6880),
    "Indonesia": (-0.7893, 113.9213),
    "Ghana": (7.9465, -1.0232),
    "Côte d'Ivoire": (7.5400, -5.5471),
    "Papua New Guinea": (-6.3149, 143.9555),
    "Benin": (9.3077, 2.3158),
    "Mali": (17.5707, -3.9962),
    "Cameroon": (7.3697, 12.3547),
    "Bolivia": (-16.2902, -63.5887),
    "Ecuador": (-1.8312, -78.1834),
}

# Regiones egipcias / históricas (más específico que país, aparece seguido en
# los datos de Egyptian Art del Met)
REGION_COORDS = {
    "Memphite Region": (29.8500, 31.2500),
    "Northern Upper Egypt": (26.1500, 32.5000),
    "Southern Upper Egypt": (25.1167, 32.8000),
    "Eastern Delta": (30.7000, 31.6500),
    # Regiones históricas de Asia Occidental (para cuando sumemos ese depto)
    "Mesopotamia": (33.0000, 44.0000),
    "Levant": (33.5000, 36.0000),
    "Anatolia": (39.0000, 35.0000),
    "Northern Syria or eastern Anatolia": (37.0000, 39.0000),
    "Syria": (34.8021, 38.9968),
    "Iran": (32.4279, 53.6880),
    "Iran, Luristan": (33.5000, 47.5000),
    "Bactria-Margiana or eastern Iran": (36.0000, 62.0000),
    "Iberian Peninsula": (40.0000, -4.0000),
    "Mesopotamia or Iran": (33.5000, 45.5000),
    "Mesoamerica": (19.0000, -99.0000),
    "central Côte d'Ivoire": (7.5400, -5.5471),
    "Middle East": (30.0000, 40.0000),
}

# Sitios / subregiones puntuales (lo más preciso que da la API del Met)
SUBREGION_COORDS = {
    "Saqqara": (29.8714, 31.2164),
    "Giza": (29.9765, 31.1313),
    "Giza or Saqqara": (29.9240, 31.1739),
    "Lisht North": (29.5667, 31.2167),
    "Memphis (Mit Rahina)": (29.8483, 31.2500),
    "Dendera area": (26.1400, 32.6700),
    "Abydos": (26.1833, 31.9192),
    "Elkab": (25.1167, 32.8000),
    "Hurbeit (Pharbaethos)": (30.6500, 31.6500),
    "Nippur": (32.1300, 45.2400),
    "Ur (modern Tell al-Muqayyar)": (30.9626, 46.1039),
    "Nimrud (ancient Kalhu)": (36.0994, 43.3250),
    "Tell Taya": (36.4000, 42.0000),
    "probably from Kültepe (Karum Kanesh)": (38.8500, 35.6200),
    "probably from Acemhöyük": (38.1900, 34.1700),
    "said to be from Ziwiye": (36.0500, 47.3000),
    "Kamterlan II": (33.5000, 47.5000),
    "Shahr-i Qumis (ancient Hecatompylos)": (35.9500, 54.3800),
}


# Fallback para departamentos donde country/region/subregion vienen casi
# siempre vacíos y el único dato geográfico real está en el campo `culture`
# (texto libre, ej. "China", "India (Tamil Nadu)", "Northeastern Thailand").
# Esto es lo que pasa con Asian Art: NO se puede usar el mismo pipeline que
# Egyptian Art. Match por substring, en orden (el primero que aparece gana).
CULTURE_KEYWORDS = [
    # Greek and Roman Art: mismo problema que Asian Art, country/region/subregion
    # casi siempre vacíos. Órden importa: lo más específico primero (ej. una
    # pieza "Roman, Cypriot" tiene que resolver a Chipre, no a Italia).
    ("Cypriot", (35.1264, 33.4299)),
    ("Etruscan", (42.8000, 11.5000)),
    ("Corinthian", (37.9061, 22.9327)),
    ("Argive", (37.6333, 22.7167)),
    ("Attic", (38.0000, 23.7000)),
    ("South Italian", (40.5000, 16.5000)),
    ("Greek", (39.0742, 21.8243)),
    ("Roman", (41.8719, 12.5674)),
    ("China", (35.8617, 104.1954)),
    ("Japan", (36.2048, 138.2529)),
    ("Korea", (35.9078, 127.7669)),
    ("Mongolia", (46.8625, 103.8467)),
    ("Tibet", (31.6927, 88.0924)),
    ("Nepal", (28.3949, 84.1240)),
    ("Sri Lanka", (7.8731, 80.7718)),
    ("Pakistan", (30.3753, 69.3451)),
    ("Afghanistan", (33.9391, 67.7100)),
    ("Myanmar", (21.9162, 95.9560)),
    ("Burma", (21.9162, 95.9560)),
    ("Thailand", (15.8700, 100.9925)),
    ("Cambodia", (12.5657, 104.9910)),
    ("Vietnam", (14.0583, 108.2772)),
    ("Indonesia", (-0.7893, 113.9213)),
    ("India", (20.5937, 78.9629)),
    # Agregado 18/08 al resolver el hueco de piezas con layer 3 invisibles en
    # el mapa (ver CLAUDE.md): met:918237 (toros alados victorianos,
    # colección McCall) tiene culture="British" en la API del Met -- dato
    # crudo real, no fabricado por nosotros, así que entra acá con el mismo
    # mecanismo que "Roman"/"Greek" (coordenada aproximada, no un sitio
    # arqueológico puntual). Precisión "culture", igual que el resto de esta
    # lista.
    ("British", (51.5074, -0.1278)),  # Londres, como aproximación de "hecho en Gran Bretaña"
]


def resolve_from_culture(culture: str) -> dict | None:
    for keyword, (lat, lon) in CULTURE_KEYWORDS:
        if _keyword_matches(keyword, culture):
            origin_country = _country_for_keyword(keyword)
            return {
                "label": culture, "label_en": culture, "precision": "culture",
                "lat": lat, "lon": lon,
                "country": origin_country[0] if origin_country else None,
                "country_en": origin_country[1] if origin_country else None,
            }
    return None


# ---------------------------------------------------------------------------
# Overrides editoriales (18/08) — un puñado de piezas bandera (layer 3) cuyos
# campos crudos de layer 1 no tienen NADA matcheable: no es que falte una
# keyword en las listas de arriba, es que el campo de origen en sí viene
# vacío o "Inconnu"/"Unknown" en la fuente del museo. Forzar un match ahí
# significaría inventar texto en layer 1 ("no se calcula ni interpreta nada
# acá", ver CLAUDE.md) — en cambio, layer 2 es explícitamente "una inferencia
# nuestra", así que un override puntual y documentado acá es coherente con el
# modelo de datos, mientras se mantenga separado de layer 1 y visible como
# decisión editorial (precision "editorial", no "site"/"country").
#
# Clave: objectID namespaceado completo (ej. "louvre:cl010256592"), no el id
# nativo del museo, para que no haya ambigüedad entre fuentes.
EDITORIAL_ORIGIN_OVERRIDES: dict[str, dict] = {
    # "Drone Hits Great Ziggurat of Ur" (Hanaa Malallah, 2016) -- obra de arte
    # contemporáneo sin ningún campo geográfico poblado en la API del Met
    # (country/region/subregion/culture todos vacíos, es arte moderno no una
    # antigüedad). El tema de la obra es explícitamente el zigurat de Ur, así
    # que se usa esa ubicación como origen -- no es un hallazgo arqueológico
    # de la pieza física (que se hizo en el estudio de la artista, no en
    # Irak), sino la referencia geográfica central de la obra, documentada en
    # notas/layer 3.
    "met:910742": {
        "label": "Ur, Irak (referencia temática de la obra)",
        "label_en": "Ur, Iraq (the artwork's thematic reference)",
        "precision": "editorial",
        "lat": 30.9626,
        "lon": 46.1039,
        "country": "Irak",
        "country_en": "Iraq",
    },
    # Tiare de Saitapharnes -- falsificación moderna (ver context.csv). El
    # registro del Louvre marca placeOfDiscovery como "Inconnu" a propósito
    # (nunca fue una pieza antigua real). Layer 3 documenta que fue
    # fabricada en 1894 en Odesa (Imperio ruso, actual Ucrania) por el
    # orfebre Israel Rouchomovsky -- se usa ese punto como origen porque es
    # el único lugar real y documentado asociado al objeto físico.
    "louvre:cl010256592": {
        "label": "Odesa, Ucrania (lugar de fabricación de la falsificación)",
        "label_en": "Odesa, Ukraine (where the forgery was made)",
        "precision": "editorial",
        "lat": 46.4825,
        "lon": 30.7233,
        "country": "Ucrania",
        "country_en": "Ukraine",
    },
}


# ---------------------------------------------------------------------------
# País moderno de origen (19/08) — para la búsqueda "al revés" por país
# (elegir un país y ver qué piezas de ahí están en cualquiera de los 3
# museos, ver CLAUDE.md "Pendiente de decidir"). Es un campo NUEVO y
# separado de origin_label: origin_label sigue siendo lo más específico que
# tengamos (un sitio arqueológico, una región histórica, un país), pensado
# para mostrarse en la ficha de la pieza; origin_country es siempre un país
# moderno reconocible, pensado para filtrar/buscar, incluso cuando
# origin_label es un sitio puntual ("Nimrud") o una región sin país en el
# nombre ("Mesopotamia", "Luristán").
#
# Dos mecanismos, según qué matcheó resolve_origin*():
#
# 1. KEYWORD_COUNTRY — cuando lo que matcheó ya es (o corresponde 1:1 a) un
#    país: las claves de COUNTRY_COORDS/CULTURE_KEYWORDS (Met) y
#    LOUVRE_COUNTRY_KEYWORDS (Louvre). La mayoría son nombres de país
#    directos (a veces en francés); un puñado son regiones históricas sin
#    ambigüedad real para nuestro propósito (Luristán/Perse/Elam -> Irán,
#    Assyrie/Mésopotamie/Babylonie/Sumer -> Irak, Anatolie -> Turquía,
#    Levant -> Siria como aproximación) o etnónimos culturales del Met
#    (Roman/Etruscan -> Italia, Greek/Corinthian/Argive/Attic -> Grecia).
#    "Proche-Orient" (Louvre) queda sin país a propósito: es una región
#    demasiado difusa (todo el Cercano Oriente) para asignarle un solo país
#    sin que sea directamente engañoso.
#
# 2. SITE_COUNTRY_BY_POINT — cuando lo que matcheó es un sitio puntual
#    (LOUVRE_SITE_COORDS/BM_SITE_COORDS/SUBREGION_COORDS/REGION_COORDS,
#    ~150 puntos): no tiene sentido mantener un país a mano por cada sitio
#    arqueológico, así que se generó una sola vez, offline, con el paquete
#    reverse_geocode (dataset de ~10mil ciudades, sin red — mismo espíritu
#    que "sin llamadas a Nominatim en bulk") corrido contra los puntos
#    lat/lon que YA vive en este archivo, y el resultado se horneó acá como
#    tabla estática — reverse_geocode NO es una dependencia del pipeline en
#    tiempo de ejecución (no está en requirements.txt), se usó una sola vez
#    para generar estos ~150 pares y después se revisó a mano. Un solo error
#    encontrado en esa revisión: Haida Gwaii (53.25, -132.0) resolvía a
#    Estados Unidos (matcheaba Metlakatla, Alaska, la ciudad más cercana en
#    el dataset) en vez de Canadá (Columbia Británica, donde está en
#    realidad) — corregido a mano abajo. El punto (30.0, 40.0), centroide
#    genérico de "Middle East" (REGION_COORDS del Met, mismo centroide que
#    "Proche-Orient" del Louvre pero ese usa el mecanismo de keyword, no de
#    punto), se excluyó por el mismo motivo que "Proche-Orient": no hay un
#    país real ahí, es un punto medio inventado para toda la región.
KEYWORD_COUNTRY: dict[str, tuple[str, str] | None] = {
    # Met COUNTRY_COORDS — ya son nombres de país
    "Egypt": ("Egipto", "Egypt"),
    "United States": ("Estados Unidos", "United States"),
    "Guatemala": ("Guatemala", "Guatemala"),
    "Peru": ("Perú", "Peru"),
    "Colombia": ("Colombia", "Colombia"),
    "Democratic Republic of the Congo": ("República Democrática del Congo", "Democratic Republic of the Congo"),
    "Mexico": ("México", "Mexico"),
    "China": ("China", "China"),
    "Japan": ("Japón", "Japan"),
    "India": ("India", "India"),
    "Iran": ("Irán", "Iran"),
    "Iraq": ("Irak", "Iraq"),
    "Turkey": ("Turquía", "Turkey"),
    "Greece": ("Grecia", "Greece"),
    "Italy": ("Italia", "Italy"),
    "France": ("Francia", "France"),
    "Nigeria": ("Nigeria", "Nigeria"),
    "Sudan": ("Sudán", "Sudan"),
    "Ethiopia": ("Etiopía", "Ethiopia"),
    "Syria": ("Siria", "Syria"),
    "Cyprus": ("Chipre", "Cyprus"),
    "present-day Uzbekistan": ("Uzbekistán", "Uzbekistan"),
    "probably Iran": ("Irán", "Iran"),
    "Indonesia": ("Indonesia", "Indonesia"),
    "Ghana": ("Ghana", "Ghana"),
    "Côte d'Ivoire": ("Costa de Marfil", "Côte d'Ivoire"),
    "Papua New Guinea": ("Papúa Nueva Guinea", "Papua New Guinea"),
    "Benin": ("Benín", "Benin"),
    "Mali": ("Malí", "Mali"),
    "Cameroon": ("Camerún", "Cameroon"),
    "Bolivia": ("Bolivia", "Bolivia"),
    "Ecuador": ("Ecuador", "Ecuador"),
    # Met CULTURE_KEYWORDS — etnónimos/adjetivos culturales, mapeados al país
    # moderno más asociado (mismo criterio que ya usa CULTURE_KEYWORDS para
    # elegir una coordenada aproximada)
    "Cypriot": ("Chipre", "Cyprus"),
    "Etruscan": ("Italia", "Italy"),
    "Corinthian": ("Grecia", "Greece"),
    "Argive": ("Grecia", "Greece"),
    "Attic": ("Grecia", "Greece"),
    "South Italian": ("Italia", "Italy"),
    "Greek": ("Grecia", "Greece"),
    "Roman": ("Italia", "Italy"),
    "Korea": ("Corea", "Korea"),
    "Mongolia": ("Mongolia", "Mongolia"),
    "Tibet": ("China", "China"),
    "Nepal": ("Nepal", "Nepal"),
    "Sri Lanka": ("Sri Lanka", "Sri Lanka"),
    "Pakistan": ("Pakistán", "Pakistan"),
    "Afghanistan": ("Afganistán", "Afghanistan"),
    "Myanmar": ("Birmania (Myanmar)", "Myanmar (Burma)"),
    "Burma": ("Birmania (Myanmar)", "Myanmar (Burma)"),
    "Thailand": ("Tailandia", "Thailand"),
    "Cambodia": ("Camboya", "Cambodia"),
    "Vietnam": ("Vietnam", "Vietnam"),
    "British": ("Reino Unido", "United Kingdom"),
    # Louvre LOUVRE_COUNTRY_KEYWORDS — francés, países directos + un puñado
    # de regiones históricas mapeadas a su país moderno más asociado
    "Chypre": ("Chipre", "Cyprus"),
    "Égypte": ("Egipto", "Egypt"),
    "Egypte": ("Egipto", "Egypt"),
    "Irak": ("Irak", "Iraq"),
    "Turquie": ("Turquía", "Turkey"),
    "Grèce": ("Grecia", "Greece"),
    "Luristan": ("Irán", "Iran"),
    "Assyrie": ("Irak", "Iraq"),
    "Etrurie": ("Italia", "Italy"),
    "Étrurie": ("Italia", "Italy"),
    "Italie": ("Italia", "Italy"),
    "Syrie": ("Siria", "Syria"),
    "Espagne": ("España", "Spain"),
    "Maroc": ("Marruecos", "Morocco"),
    "Liban": ("Líbano", "Lebanon"),
    "Ouzbékistan": ("Uzbekistán", "Uzbekistan"),
    "Inde": ("India", "India"),
    "Indonésie": ("Indonesia", "Indonesia"),
    "Anatolie": ("Turquía", "Turkey"),
    "Mésopotamie": ("Irak", "Iraq"),
    "Proche-Orient": None,
    "Levant": ("Siria", "Syria"),
    "Perse": ("Irán", "Iran"),
    "Elam": ("Irán", "Iran"),
    "Babylonie": ("Irak", "Iraq"),
    "Sumer": ("Irak", "Iraq"),
    "Tunisie": ("Túnez", "Tunisia"),
    "Sicile": ("Italia", "Italy"),
}

# Generado offline el 19/08 con reverse_geocode contra los puntos lat/lon de
# SUBREGION_COORDS/REGION_COORDS (Met) + LOUVRE_SITE_COORDS + BM_SITE_COORDS,
# revisado a mano (ver comentario arriba) — no es una dependencia del
# pipeline en tiempo de ejecución.
SITE_COUNTRY_BY_POINT: dict[tuple[float, float], tuple[str, str]] = {
    (-27.1836, -109.4306): ("Chile", "Chile"),
    (-27.1667, -109.4333): ("Chile", "Chile"),
    (-22.5752, 144.0848): ("Australia", "Australia"),
    (-20.2675, 30.9337): ("Zimbabue", "Zimbabwe"),
    (-18.65, -173.98): ("Tonga", "Tonga"),
    (-18.4783, -70.3126): ("Chile", "Chile"),
    (-17.65, -67.95): ("Bolivia", "Bolivia"),
    (-16.25, 168.1167): ("Vanuatu", "Vanuatu"),
    (-8.1116, -79.029): ("Perú", "Peru"),
    (-7.5, 110.0): ("Indonesia", "Indonesia"),
    (-6.1659, 39.2026): ("Tanzania", "Tanzania"),
    (-4.1, 143.9): ("Papúa Nueva Guinea", "Papua New Guinea"),
    (-2.9006, -79.0045): ("Ecuador", "Ecuador"),
    (-0.5333, 31.4167): ("Uganda", "Uganda"),
    (0.2667, 32.65): ("Uganda", "Uganda"),
    (6.335, 5.6037): ("Nigeria", "Nigeria"),
    (6.6885, -1.6244): ("Ghana", "Ghana"),
    (6.75, -1.5): ("Ghana", "Ghana"),
    (7.4905, 4.5521): ("Nigeria", "Nigeria"),
    (7.54, -5.5471): ("Costa de Marfil", "Côte d'Ivoire"),
    (8.5711, 81.2335): ("Sri Lanka", "Sri Lanka"),
    (10.2167, 105.1333): ("Vietnam", "Vietnam"),
    (10.391, -75.4794): ("Colombia", "Colombia"),
    (11.2408, -74.199): ("Colombia", "Colombia"),
    (11.8, 39.7): ("Etiopía", "Ethiopia"),
    (13.4125, 103.867): ("Camboya", "Cambodia"),
    (14.1211, 38.7167): ("Etiopía", "Ethiopia"),
    (15.1167, -10.5667): ("Malí", "Mali"),
    (15.4045, -91.1502): ("Guatemala", "Guatemala"),
    (15.43, 45.3286): ("Yemen", "Yemen"),
    (16.573, 80.3567): ("India", "India"),
    (16.9333, 33.75): ("Sudán", "Sudan"),
    (19.0, -99.0): ("México", "Mexico"),
    (19.08, 30.36): ("Sudán", "Sudan"),
    (19.8968, -155.5828): ("Estados Unidos", "United States"),
    (21.9588, 96.0891): ("Birmania (Myanmar)", "Myanmar (Burma)"),
    (22.1833, 31.9): ("Egipto", "Egypt"),
    (24.0833, 32.8833): ("Egipto", "Egypt"),
    (24.0889, 32.8998): ("Egipto", "Egypt"),
    (24.3745, 88.6042): ("Bangladés", "Bangladesh"),
    (24.4514, 32.9283): ("Egipto", "Egypt"),
    (25.1167, 32.8): ("Egipto", "Egypt"),
    (25.6167, 32.5333): ("Egipto", "Egypt"),
    (25.6872, 32.6396): ("Egipto", "Egypt"),
    (25.7188, 32.6081): ("Egipto", "Egypt"),
    (25.7188, 32.6573): ("Egipto", "Egypt"),
    (25.728, 32.6014): ("Egipto", "Egypt"),
    (25.75, 32.6333): ("Egipto", "Egypt"),
    (26.14, 32.67): ("Egipto", "Egypt"),
    (26.1417, 32.6706): ("Egipto", "Egypt"),
    (26.15, 32.5): ("Egipto", "Egypt"),
    (26.1833, 31.9192): ("Egipto", "Egypt"),
    (27.1809, 31.1837): ("Egipto", "Egypt"),
    (27.6453, 30.9017): ("Egipto", "Egypt"),
    (29.5667, 31.2167): ("Egipto", "Egypt"),
    (29.65, 91.1): ("China", "China"),
    (29.8483, 31.25): ("Egipto", "Egypt"),
    (29.85, 31.25): ("Egipto", "Egypt"),
    (29.8714, 31.2164): ("Egipto", "Egypt"),
    (29.924, 31.1739): ("Egipto", "Egypt"),
    (29.9354, 52.8916): ("Irán", "Iran"),
    (29.9765, 31.1313): ("Egipto", "Egypt"),
    (30.1167, 31.2167): ("Egipto", "Egypt"),
    (30.2839, 57.0834): ("Irán", "Iran"),
    (30.65, 31.65): ("Egipto", "Egypt"),
    (30.7, 31.65): ("Egipto", "Egypt"),
    (30.9626, 46.1039): ("Irak", "Iraq"),
    (31.0, -7.9): ("Marruecos", "Morocco"),
    (31.24, 45.8583): ("Irak", "Iraq"),
    (31.3225, 45.6367): ("Irak", "Iraq"),
    (31.4022, 30.4181): ("Egipto", "Egypt"),
    (31.4342, 46.5342): ("Irak", "Iraq"),
    (31.5, 35.7833): ("Jordania", "Jordan"),
    (31.59, 46.15): ("Irak", "Iraq"),
    (31.7683, 35.2137): ("Israel", "Israel"),
    (31.7745, 35.2354): ("Palestina", "Palestine"),
    (32.1167, 20.0667): ("Libia", "Libya"),
    (32.13, 45.24): ("Irak", "Iraq"),
    (32.1881, 48.2578): ("Irán", "Iran"),
    (32.4279, 53.688): ("Irán", "Iran"),
    (32.5425, 44.4213): ("Irak", "Iraq"),
    (32.585, 35.1836): ("Israel", "Israel"),
    (32.75, 36.75): ("Siria", "Syria"),
    (33.0, 44.0): ("Irak", "Iraq"),
    (33.2704, 35.2038): ("Líbano", "Lebanon"),
    (33.5, 36.0): ("Siria", "Syria"),
    (33.5, 45.5): ("Irak", "Iraq"),
    (33.5, 47.5): ("Irán", "Iran"),
    (34.0, 71.5): ("Pakistán", "Pakistan"),
    (34.0059, 36.2042): ("Líbano", "Lebanon"),
    (34.1208, 35.6478): ("Líbano", "Lebanon"),
    (34.43, 70.45): ("Afganistán", "Afghanistan"),
    (34.5514, 38.2792): ("Siria", "Syria"),
    (34.5514, 40.8908): ("Siria", "Syria"),
    (34.7167, 33.1333): ("Chipre", "Cyprus"),
    (34.8021, 38.9968): ("Siria", "Syria"),
    (34.8828, -1.3167): ("Argelia", "Algeria"),
    (35.32, 24.75): ("Grecia", "Greece"),
    (35.4553, 43.2588): ("Irak", "Iraq"),
    (35.6017, 35.7822): ("Siria", "Syria"),
    (35.85, 36.75): ("Siria", "Syria"),
    (35.95, 54.38): ("Irán", "Iran"),
    (36.0, 62.0): ("Turkmenistán", "Turkmenistan"),
    (36.05, 47.3): ("Irán", "Iran"),
    (36.0994, 43.325): ("Irak", "Iraq"),
    (36.1833, 37.2333): ("Siria", "Syria"),
    (36.2021, 36.1603): ("Turquía", "Turkey"),
    (36.36, 43.15): ("Irak", "Iraq"),
    (36.4, 42.0): ("Irak", "Iraq"),
    (36.4341, 28.2176): ("Grecia", "Greece"),
    (36.4667, -5.7167): ("España", "Spain"),
    (36.5, 38.05): ("Siria", "Syria"),
    (36.5117, 43.2278): ("Irak", "Iraq"),
    (36.6833, 27.3667): ("Grecia", "Greece"),
    (36.69, 24.43): ("Grecia", "Greece"),
    (36.75, 38.8667): ("Turquía", "Turkey"),
    (36.75, 66.9): ("Afganistán", "Afghanistan"),
    (36.8167, 38.0167): ("Siria", "Syria"),
    (37.0, 39.0): ("Turquía", "Turkey"),
    (37.0853, 25.1488): ("Grecia", "Greece"),
    (37.15, 68.3667): ("Tayikistán", "Tajikistan"),
    (37.3964, 25.2686): ("Grecia", "Greece"),
    (37.6333, 22.7333): ("Grecia", "Greece"),
    (37.6383, 21.63): ("Grecia", "Greece"),
    (37.75, 26.8): ("Grecia", "Greece"),
    (37.9715, 23.7267): ("Grecia", "Greece"),
    (37.9838, 23.7275): ("Grecia", "Greece"),
    (38.19, 34.17): ("Turquía", "Turkey"),
    (38.3167, 23.5333): ("Grecia", "Greece"),
    (38.4824, 22.501): ("Grecia", "Greece"),
    (38.85, 35.62): ("Turquía", "Turkey"),
    (39.0, 35.0): ("Turquía", "Turkey"),
    (39.2975, 22.3961): ("Grecia", "Greece"),
    (39.7833, 35.75): ("Turquía", "Turkey"),
    (40.0, -4.0): ("España", "Spain"),
    (40.0084, 116.2966): ("China", "China"),
    (40.4708, 25.5228): ("Grecia", "Greece"),
    (40.7461, 14.4989): ("Italia", "Italy"),
    (40.7833, 24.7): ("Grecia", "Greece"),
    (40.8058, 14.3487): ("Italia", "Italy"),
    (41.9028, 12.4964): ("Italia", "Italy"),
    (41.995, 12.103): ("Italia", "Italy"),
    (42.25, 11.75): ("Italia", "Italy"),
    (42.42, 11.625): ("Italia", "Italy"),
    (43.2203, 142.8635): ("Japón", "Japan"),
    (43.6763, 4.628): ("Francia", "France"),
    # Haida Gwaii -- corregido a mano: el punto reverse-geocodeaba a Estados
    # Unidos (Metlakatla, Alaska, la ciudad más cercana en el dataset de
    # reverse_geocode) pero Haida Gwaii es Columbia Británica, Canadá.
    (53.25, -132.0): ("Canadá", "Canada"),
    (64.8255, -124.8457): ("Canadá", "Canada"),
}


def _country_for_keyword(keyword: str) -> tuple[str, str] | None:
    return KEYWORD_COUNTRY.get(keyword)


def _country_for_point(lat: float | None, lon: float | None) -> tuple[str, str] | None:
    if lat is None or lon is None:
        return None
    return SITE_COUNTRY_BY_POINT.get((lat, lon))


def resolve_origin(obj: dict) -> dict:
    """
    Devuelve {"label": str, "precision": str, "lat": float, "lon": float}
    o {"label": ..., "precision": "unresolved", "lat": None, "lon": None}
    si no encontramos coordenadas para lo que trae el objeto.
    """
    subregion = (obj.get("subregion") or "").strip()
    region = (obj.get("region") or "").strip()
    country = (obj.get("country") or "").strip()

    if subregion in SUBREGION_COORDS:
        lat, lon = SUBREGION_COORDS[subregion]
        origin_country = _country_for_point(lat, lon)
        return {
            "label": es_label(subregion), "label_en": en_label(subregion), "precision": "subregion",
            "lat": lat, "lon": lon,
            "country": origin_country[0] if origin_country else None,
            "country_en": origin_country[1] if origin_country else None,
        }

    if region in REGION_COORDS:
        lat, lon = REGION_COORDS[region]
        origin_country = _country_for_point(lat, lon)
        return {
            "label": es_label(region), "label_en": en_label(region), "precision": "region",
            "lat": lat, "lon": lon,
            "country": origin_country[0] if origin_country else None,
            "country_en": origin_country[1] if origin_country else None,
        }

    if country in COUNTRY_COORDS:
        lat, lon = COUNTRY_COORDS[country]
        origin_country = _country_for_keyword(country)
        return {
            "label": es_label(country), "label_en": en_label(country), "precision": "country",
            "lat": lat, "lon": lon,
            "country": origin_country[0] if origin_country else None,
            "country_en": origin_country[1] if origin_country else None,
        }

    culture = (obj.get("culture") or "").strip()
    if culture:
        from_culture = resolve_from_culture(culture)
        if from_culture:
            return from_culture

    raw_label = subregion or region or country or culture or ""
    return {"label": raw_label, "label_en": raw_label, "precision": "unresolved", "lat": None, "lon": None, "country": None, "country_en": None}


# ---------------------------------------------------------------------------
# Louvre: los campos geográficos vienen en texto libre en francés, con un
# formato jerárquico tipo "Sitio (Región -> País)" o "País (Región)", muy
# distinto del country/region/subregion estructurado del Met. En vez de
# tratar de parsear esa jerarquía en general, matcheamos por substring contra
# dos listas (sitio arqueológico primero, más específico; país/región
# genérico después), igual que resolve_from_culture. A expandir con cada
# corrida de build_geography_louvre.py — imprime las etiquetas sin resolver.

LOUVRE_SITE_COORDS = [
    # Antigüedades egipcias
    ("Saqqara", (29.8714, 31.2164)),
    ("Dendéra", (26.1417, 32.6706)),  # templo de Hathor -- faltaba, ver bug de _keyword_matches
    ("Denderah", (26.1417, 32.6706)),
    ("Deir el-Médineh", (25.7280, 32.6014)),
    ("Thèbes", (25.7188, 32.6081)),
    ("Karnak", (25.7188, 32.6573)),
    ("Louxor", (25.6872, 32.6396)),
    ("Assiout", (27.1809, 31.1837)),
    ("Assouan", (24.0889, 32.8998)),
    ("Éléphantine", (24.0833, 32.8833)),
    ("Médamoud", (25.7500, 32.6333)),
    ("Tôd", (25.6167, 32.5333)),
    ("Kôm Ombo", (24.4514, 32.9283)),
    ("Abou Roach", (30.1167, 31.2167)),
    ("Abou Rawach", (30.1167, 31.2167)),
    ("Giza", (29.9765, 31.1313)),
    ("Méroé", (16.9333, 33.7500)),
    # Antigüedades orientales (Cercano Oriente)
    ("Assur", (35.4553, 43.2588)),  # Qalaat Shergat, Irak -- antes se perdía por matchear "Ur" como substring
    ("Baalbeck", (34.0059, 36.2042)),  # Líbano
    ("Suse", (32.1881, 48.2578)),
    ("Persépolis", (29.9354, 52.8916)),
    ("Mari", (34.5514, 40.8908)),
    ("Khorsabad", (36.5117, 43.2278)),
    ("Ninive", (36.3600, 43.1500)),
    ("Nimroud", (36.0994, 43.3250)),
    ("Babylone", (32.5425, 44.4213)),
    ("Larsa", (31.2400, 45.8583)),
    ("Girsu", (31.5900, 46.1500)),
    ("Tello", (31.5900, 46.1500)),
    ("Lagash", (31.4342, 46.5342)),
    ("Ur", (30.9626, 46.1039)),
    ("Uruk", (31.3225, 45.6367)),
    ("Mari sur l'Euphrate", (34.5514, 40.8908)),
    ("Ras Shamra", (35.6017, 35.7822)),
    ("Ougarit", (35.6017, 35.7822)),
    ("Byblos", (34.1208, 35.6478)),
    ("Megiddo", (32.5850, 35.1836)),
    ("Mégiddo", (32.5850, 35.1836)),
    ("Palmyre", (34.5514, 38.2792)),
    ("Arslan Tash", (36.7500, 38.8667)),
    ("Til Barsib", (36.5000, 38.0500)),
    ("Kultépé", (39.7833, 35.7500)),
    ("Bactres", (36.7500, 66.9000)),
    # Antigüedades griegas, etruscas y romanas
    ("Athènes", (37.9838, 23.7275)),
    ("Délos", (37.3964, 25.2686)),
    ("Samothrace", (40.4708, 25.5228)),
    ("Delphes", (38.4824, 22.5010)),
    ("Olympie", (37.6383, 21.6300)),
    ("Cnide", (36.6833, 27.3667)),
    ("Rhodes", (36.4341, 28.2176)),
    ("Cervéteri", (41.9950, 12.1030)),
    ("Vulci", (42.4200, 11.6250)),
    ("Tarquinia", (42.2500, 11.7500)),
    ("Herculanum", (40.8058, 14.3487)),
    ("Pompéi", (40.7461, 14.4989)),
    ("Antioche", (36.2021, 36.1603)),
    ("Cervéteri", (41.9950, 12.1030)),
    ("Cerveteri", (41.9950, 12.1030)),
    ("Rome", (41.9028, 12.4964)),
    ("Arles", (43.6763, 4.6280)),
    ("Samos", (37.7500, 26.8000)),
    ("Mélos", (36.6900, 24.4300)),
    ("Diban", (31.5000, 35.7833)),
    ("Afis", (35.8500, 36.7500)),
    ("Nemara", (32.7500, 36.7500)),  # an-Namara, Siria (inscripción nabatea)
    ("Éleutherne", (35.3200, 24.7500)),  # Creta, Grecia
    ("Amarna", (27.6453, 30.9017)),  # Tell el-Amarna, Egipto
    ("Argos", (37.6333, 22.7333)),  # Grecia, Peloponeso
    ("Benghazi", (32.1167, 20.0667)),  # Bengasi/antigua Berenice, Libia
    ("Kerman", (30.2839, 57.0834)),  # Irán
    ("Neirab", (36.1833, 37.2333)),  # cerca de Alepo, Siria
    ("Paros", (37.0853, 25.1488)),  # isla griega
    ("Pharsale", (39.2975, 22.3961)),  # Farsala, Tesalia, Grecia
    ("Tanagra", (38.3167, 23.5333)),  # Beocia, Grecia
    ("Thasos", (40.7833, 24.7000)),  # isla griega
    ("Tlemcen", (34.8828, -1.3167)),  # Argelia
    ("Tyr", (33.2704, 35.2038)),  # Tiro, Líbano
    ("Alcalá de los Gazules", (36.4667, -5.7167)),  # Cádiz, España
]

LOUVRE_COUNTRY_KEYWORDS = [
    # Exónimos franceses -> mismas coordenadas que COUNTRY_COORDS/REGION_COORDS,
    # más los que faltan para los departamentos que estamos sumando ahora.
    ("Chypre", (35.1264, 33.4299)),
    ("Égypte", (26.8206, 30.8025)),
    ("Egypte", (26.8206, 30.8025)),
    ("Iran", (32.4279, 53.6880)),
    ("Irak", (33.2232, 43.6793)),
    ("Turquie", (38.9637, 35.2433)),
    ("Grèce", (39.0742, 21.8243)),
    ("Luristan", (33.5000, 47.5000)),  # región del oeste de Irán, mismas coords que "Iran, Luristan" en CULTURE_KEYWORDS
    ("Assyrie", (36.3350, 43.1189)),  # región/civilización, corazón asirio cerca de Mosul, Irak
    ("Etrurie", (42.8000, 11.5000)),
    ("Étrurie", (42.8000, 11.5000)),
    ("Italie", (41.8719, 12.5674)),
    ("Syrie", (34.8021, 38.9968)),
    ("Espagne", (40.4637, -3.7492)),
    ("Maroc", (31.7917, -7.0926)),
    ("Liban", (33.8547, 35.8623)),
    ("Afghanistan", (33.9391, 67.7100)),
    ("Ouzbékistan", (41.3775, 64.5853)),
    ("Inde", (20.5937, 78.9629)),
    ("Indonésie", (-0.7893, 113.9213)),
    ("Anatolie", (39.0000, 35.0000)),
    ("Mésopotamie", (33.0000, 44.0000)),
    ("Proche-Orient", (30.0000, 40.0000)),
    ("Levant", (33.5000, 36.0000)),
    ("Perse", (32.4279, 53.6880)),
    ("Elam", (32.1881, 48.2578)),
    ("Babylonie", (33.0000, 44.0000)),  # región, distinto de la ciudad "Babylone" ya listada arriba
    ("Sumer", (31.0000, 45.6000)),
    ("Tunisie", (33.8869, 9.5375)),
    ("Sicile", (37.5000, 14.0000)),
]


def resolve_origin_louvre(obj: dict) -> dict:
    """
    Igual idea que resolve_origin() pero para el shape de datos del Louvre:
    no hay country/region/subregion estructurado, así que buscamos en texto
    libre (placeOfDiscovery > placeOfCreation > provenance, en ese orden de
    prioridad porque el sitio de excavación es el dato más específico que da
    la API) contra sitios arqueológicos primero y país/región genérico
    después.
    """
    place_of_discovery = (obj.get("placeOfDiscovery") or "").strip()
    place_of_creation = (obj.get("placeOfCreation") or "").strip()
    provenance = (obj.get("provenance") or "").strip()

    label = place_of_discovery or place_of_creation or provenance
    haystack = " | ".join([place_of_discovery, place_of_creation, provenance])

    for site, (lat, lon) in LOUVRE_SITE_COORDS:
        if _keyword_matches(site, haystack):
            origin_country = _country_for_point(lat, lon)
            return {
                "label": es_label(site), "label_en": en_label(site), "precision": "site",
                "lat": lat, "lon": lon,
                "country": origin_country[0] if origin_country else None,
                "country_en": origin_country[1] if origin_country else None,
            }

    for country, (lat, lon) in LOUVRE_COUNTRY_KEYWORDS:
        if _keyword_matches(country, haystack):
            origin_country = _country_for_keyword(country)
            return {
                "label": es_label(country), "label_en": en_label(country), "precision": "country",
                "lat": lat, "lon": lon,
                "country": origin_country[0] if origin_country else None,
                "country_en": origin_country[1] if origin_country else None,
            }

    return {"label": label, "label_en": label, "precision": "unresolved", "lat": None, "lon": None, "country": None, "country_en": None}


# ---------------------------------------------------------------------------
# British Museum: findspot/productionPlace vienen en inglés, con un prefijo
# de etiqueta ("Excavated/Findspot:", "Found/Acquired:", "Made in:") seguido
# de un nombre de sitio en texto libre — más simple que el francés del
# Louvre, pero igual necesita su propia lista (nombres de sitio en inglés,
# no siempre los mismos que ya tenemos para otros museos).

# Cada entrada es (palabra clave a buscar en el texto crudo en inglés,
# nombre a mostrar en la ficha de la pieza, coordenadas). La palabra clave
# se mantiene en inglés porque tiene que matchear el texto tal cual lo
# scrapeamos del sitio; el nombre a mostrar es el que ve el usuario y puede
# estar en español o incluir contexto ("Sitio, País") cuando el nombre del
# sitio solo no alcanza para ubicarlo. Antes de esto, resolve_origin_bm()
# mostraba el findspot/productionPlace crudo tal cual (con el prefijo
# "Excavated/Findspot:"/"Found/Acquired:"/"Made in:" y, en varios casos,
# notas de registro larguísimas pegadas) — quedaba ilegible para el
# visitante. Las entradas viejas (antes de la quinta ronda) mantienen el
# nombre en inglés como display por ahora — limpiarlas todas es una mejora
# incremental pendiente, no bloqueante.
# Restructurado el 17/08 (ver "originLabel EN" en CLAUDE.md) de 3-tuplas
# (keyword, display, coords) a 4-tuplas (keyword, display_es, display_en,
# coords): a diferencia de Met/Louvre, los "display" del BM no eran una
# clave de diccionario reutilizable — eran texto final ad-hoc, a veces
# inglés crudo, a veces ya traducido a mano al español en rondas anteriores.
# Meterlos en ES_NAMES/EN_NAMES hubiera requerido las mismas ~90 entradas
# ad-hoc que ya vivían acá, sin ninguna ventaja real. display_es reproduce
# exactamente lo que ya mostraba la app antes de este cambio (incluye los
# casos donde antes se dependía de un lookup en ES_NAMES, ej. "Parthenon" ->
# "Partenón", "Kumase" -> "Kumasi" — ver git history si hace falta
# reconstruir esa cadena).
BM_SITE_COORDS = [
    ("Fort Saint Julien", "Fort Saint Julien", "Fort Saint Julien", (31.4022, 30.4181)),  # Rosetta / el-Rashid, Egipto
    ("Kawa", "Kawa", "Kawa", (19.0800, 30.3600)),  # Nubia, Sudán
    ("Nimrud", "Nimrud", "Nimrud", (36.0994, 43.3250)),
    ("Trincomalee", "Trincomalee", "Trincomalee", (8.5711, 81.2335)),
    ("Benin City", "Benin City", "Benin City", (6.3350, 5.6037)),
    ("Orongo", "Orongo", "Orongo", (-27.1836, -109.4306)),  # Rapa Nui / Isla de Pascua — sitio ceremonial, Hoa Hakananai'a
    ("Rano Kao", "Rano Kao", "Rano Kao", (-27.1667, -109.4333)),  # Rapa Nui / Isla de Pascua
    ("Parthenon", "Partenón", "Parthenon", (37.9715, 23.7267)),  # Acrópolis, Atenas
    ("Maqdala", "Maqdala", "Maqdala", (11.8000, 39.7000)),  # Amba Mariam, Etiopía — colección Maqdala (1868)
    ("Kumase", "Kumasi", "Kumasi", (6.6885, -1.6244)),  # capital histórica del reino Asante
    ("Asante Region", "Región Asante", "Asante Region", (6.7500, -1.5000)),  # Ghana
    ("Yuanmingyuan", "Yuanmingyuan", "Yuanmingyuan", (40.0084, 116.2966)),  # Antiguo Palacio de Verano, Beijing
    ("Amaravati", "Amaravati", "Amaravati", (16.5730, 80.3567)),  # Andhra Pradesh, India
    ("Takht-i Kuwad", "Takht-i Kuwad", "Takht-i Kuwad", (37.1500, 68.3667)),  # Tesoro de Oxus, actual Tayikistán
    ("Babylon", "Babilonia", "Babylon", (32.5425, 44.4213)),  # Irak
    ("Nineveh", "Nínive", "Nineveh", (36.3600, 43.1500)),  # Irak
    ("Queensland", "Queensland", "Queensland", (-22.5752, 144.0848)),
    ("Ife", "Ife", "Ife", (7.4905, 4.5521)),  # Nigeria, distinto de Benin City
    ("Haida Gwaii", "Haida Gwaii", "Haida Gwaii", (53.2500, -132.0000)),  # Columbia Británica, Canadá
    ("Trujillo", "Trujillo", "Trujillo", (-8.1116, -79.0290)),  # costa norte de Perú, cultura moche
    ("Gandhara", "Gandhara", "Gandhara", (34.0000, 71.5000)),  # actual Pakistán
    ("Angkor", "Angkor", "Angkor", (13.4125, 103.8670)),  # Camboya
    ("Carchemish", "Carchemish", "Carchemish", (36.8167, 38.0167)),  # frontera Turquía/Siria
    ("Aksum", "Aksum", "Aksum", (14.1211, 38.7167)),  # Etiopía
    ("Sepik River", "Río Sepik", "Sepik River", (-4.1000, 143.9000)),  # Nueva Guinea
    ("Marib", "Marib", "Marib", (15.4300, 45.3286)),  # Yemen, antigua capital sabea
    ("Faras", "Faras", "Faras", (22.1833, 31.9000)),  # Nubia, Sudán
    ("Hawaiian Islands", "Islas Hawái", "Hawaiian Islands", (19.8968, -155.5828)),
    ("Hawaii", "Hawái", "Hawaii", (19.8968, -155.5828)),
    ("Northwest Territories", "Territorios del Noroeste", "Northwest Territories", (64.8255, -124.8457)),  # Canadá
    ("Hokkaido", "Hokkaido", "Hokkaido", (43.2203, 142.8635)),  # Japón — territorio ainu
    ("Zanzibar", "Zanzibar", "Zanzibar", (-6.1659, 39.2026)),  # Tanzania
    ("Ambrym", "Ambrym", "Ambrym", (-16.2500, 168.1167)),  # Vanuatu
    ("Amathus", "Amathus", "Amathus", (34.7167, 33.1333)),  # Chipre
    ("Cartagena", "Cartagena", "Cartagena", (10.3910, -75.4794)),  # Colombia
    ("Rajshahi", "Rajshahi", "Rajshahi", (24.3745, 88.6042)),  # Bangladés
    ("Santa Marta", "Santa Marta", "Santa Marta", (11.2408, -74.1990)),  # Colombia
    ("Mandalay", "Mandalay", "Mandalay", (21.9588, 96.0891)),  # Birmania (Myanmar)
    # Quinta ronda de curación (17/08) — sitios nuevos sin cobertura previa.
    ("Persepolis", "Persépolis", "Persepolis", (29.9354, 52.8916)),  # Irán, capital aqueménida
    ("Bimaran", "Bimaran, Afganistán", "Bimaran, Afghanistan", (34.4300, 70.4500)),  # cerca de Jalalabad — Estupa de Bimaran
    ("Lhasa", "Lhasa, Tíbet", "Lhasa, Tibet", (29.6500, 91.1000)),
    ("Great Zimbabwe", "Great Zimbabwe", "Great Zimbabwe", (-20.2675, 30.9337)),  # Zimbabue
    ("Luzira", "Luzira, Uganda", "Luzira, Uganda", (0.2667, 32.6500)),  # cerca de Kampala
    ("Bigo", "Bigo bya Mugenyi, Uganda", "Bigo bya Mugenyi, Uganda", (-0.5333, 31.4167)),  # earthworks
    ("Ophel", "Ophel, Jerusalén", "Ophel, Jerusalem", (31.7745, 35.2354)),  # excavación bíblica
    ("Jerusalem", "Jerusalén", "Jerusalem", (31.7683, 35.2137)),
    ("Nebaj", "Nebaj, Guatemala", "Nebaj, Guatemala", (15.4045, -91.1502)),  # tierras altas mayas
    ("Java", "Java", "Java", (-7.5000, 110.0000)),  # Indonesia — coordenada central de la isla
    # Sexta ronda de curación (17/08) — sitios nuevos sin cobertura previa.
    ("Cuenca", "Cuenca, Ecuador", "Cuenca, Ecuador", (-2.9006, -79.0045)),  # colección William Bollaert, s. XIX
    ("Aroma", "Aroma, Bolivia", "Aroma, Bolivia", (-17.6500, -67.9500)),  # provincia de La Paz
    ("Atlas Mountains", "Montañas del Atlas, Marruecos", "Atlas Mountains, Morocco", (31.0000, -7.9000)),
    ("Oc-eo", "Óc Eo, Vietnam", "Óc Eo, Vietnam", (10.2167, 105.1333)),  # provincia de An Giang
    ("Vava'u", "Vava'u, Tonga", "Vava'u, Tonga", (-18.6500, -173.9800)),
    # Séptima ronda de curación (17/08) — sitios nuevos sin cobertura previa.
    ("Arica", "Arica, Chile", "Arica, Chile", (-18.4783, -70.3126)),  # bahía del norte de Chile, cultura chinchorro/arica
    ("Yelimané", "Yelimané, Malí", "Yelimané, Mali", (15.1167, -10.5667)),  # cercle de Yelimané, región de Kayes
]

BM_COUNTRY_KEYWORDS = [
    ("Sudan", "Sudán", "Sudan", (12.8628, 30.2176)),
    ("Egypt", "Egipto", "Egypt", (26.8206, 30.8025)),
    ("Sri Lanka", "Sri Lanka", "Sri Lanka", (7.8731, 80.7718)),
    ("Nigeria", "Nigeria", "Nigeria", (9.0820, 8.6753)),
    ("Iraq", "Irak", "Iraq", (33.2232, 43.6793)),
    ("Iran", "Irán", "Iran", (32.4279, 53.6880)),
    ("Ethiopia", "Etiopía", "Ethiopia", (9.1450, 40.4897)),
    ("Ghana", "Ghana", "Ghana", (7.9465, -1.0232)),
    ("Greece", "Grecia", "Greece", (39.0742, 21.8243)),
    ("Turkey", "Turquía", "Turkey", (38.9637, 35.2433)),
    ("China", "China", "China", (35.8617, 104.1954)),
    ("India", "India", "India", (20.5937, 78.9629)),
    ("Easter Island", "Isla de Pascua", "Easter Island", (-27.1127, -109.3497)),
    ("New Zealand", "Nueva Zelanda", "New Zealand", (-40.9006, 174.8860)),
    ("Tajikistan", "Tayikistán", "Tajikistan", (38.8610, 71.2761)),
    ("Australia", "Australia", "Australia", (-25.2744, 133.7751)),
    ("Democratic Republic of Congo", "República Democrática del Congo", "Democratic Republic of Congo", (-4.0383, 21.7587)),
    ("South Africa", "Sudáfrica", "South Africa", (-30.5595, 22.9375)),
    ("Mexico", "México", "Mexico", (23.6345, -102.5528)),
    ("Korea", "Corea", "Korea", (35.9078, 127.7669)),
    ("Cambodia", "Camboya", "Cambodia", (12.5657, 104.9910)),
    ("Jamaica", "Jamaica", "Jamaica", (18.1096, -77.2975)),
    ("Japan", "Japón", "Japan", (36.2048, 138.2529)),
    ("Pakistan", "Pakistán", "Pakistan", (30.3753, 69.3451)),
    ("Yemen", "Yemen", "Yemen", (15.5527, 48.5164)),
    ("Papua New Guinea", "Papúa Nueva Guinea", "Papua New Guinea", (-6.3149, 143.9555)),
    ("New Guinea", "Nueva Guinea", "New Guinea", (-6.3149, 143.9555)),
    ("Fiji", "Fiyi", "Fiji", (-17.7134, 178.0650)),
    ("Solomon Islands", "Islas Salomón", "Solomon Islands", (-9.6457, 160.1562)),
    ("Canada", "Canadá", "Canada", (56.1304, -106.3468)),
    ("Namibia", "Namibia", "Namibia", (-22.9576, 18.4904)),
    ("Kenya", "Kenia", "Kenya", (-0.0236, 37.9062)),
    ("Cyprus", "Chipre", "Cyprus", (35.1264, 33.4299)),
    ("Cameroon", "Camerún", "Cameroon", (7.3697, 12.3547)),
    ("Bangladesh", "Bangladés", "Bangladesh", (23.6850, 90.3563)),
    # Quinta ronda de curación (17/08) — países nuevos sin cobertura previa.
    ("Afghanistan", "Afganistán", "Afghanistan", (33.9391, 67.7100)),
    ("Tibet", "Tíbet", "Tibet", (31.6927, 88.0924)),
    ("Sierra Leone", "Sierra Leona", "Sierra Leone", (8.4606, -11.7799)),
    ("Uganda", "Uganda", "Uganda", (1.3733, 32.2903)),
    ("Zimbabwe", "Zimbabue", "Zimbabwe", (-19.0154, 29.1549)),
    ("Palestine", "Palestina", "Palestine", (31.9522, 35.2332)),
    ("Malawi", "Malaui", "Malawi", (-13.2543, 34.3015)),
    ("Peru", "Perú", "Peru", (-9.1900, -75.0152)),
    ("Botswana", "Botsuana", "Botswana", (-22.3285, 24.6849)),
    ("Zambia", "Zambia", "Zambia", (-13.1339, 27.8493)),
    ("Trinidad", "Trinidad", "Trinidad", (10.6918, -61.2225)),
    ("Guyana", "Guyana", "Guyana", (4.8604, -58.9302)),
    # Sexta ronda de curación (17/08) — países nuevos sin cobertura previa.
    ("Venezuela", "Venezuela", "Venezuela", (6.4238, -66.5897)),
    ("Brazil", "Brasil", "Brazil", (-14.2350, -51.9253)),
    ("Nepal", "Nepal", "Nepal", (28.3949, 84.1240)),
    # Séptima ronda de curación (17/08) — países nuevos sin cobertura previa.
    # "Sénégal" con tilde a propósito: el texto crudo scrapeado del BM viene
    # en francés para este país ("Made in:Sénégal"), no en inglés.
    ("Sénégal", "Senegal", "Senegal", (14.4974, -14.4524)),
    ("Mali", "Malí", "Mali", (17.5707, -3.9962)),
    ("Thailand", "Tailandia", "Thailand", (15.8700, 100.9925)),
    ("Mongolia", "Mongolia", "Mongolia", (46.8625, 103.8467)),
    ("Madagascar", "Madagascar", "Madagascar", (-18.7669, 46.8691)),
]


# País moderno para BM_COUNTRY_KEYWORDS (19/08): a diferencia de Met/Louvre,
# casi todas las keywords de BM_COUNTRY_KEYWORDS YA son nombres de país
# limpios (traen su propio display_es/display_en, reusado directamente como
# país) -- solo hace falta un override puntual para las pocas que no son un
# país en sentido estricto (un territorio insular, una región dentro de otro
# país).
BM_COUNTRY_FIELD_OVERRIDES: dict[str, tuple[str, str]] = {
    "Easter Island": ("Chile", "Chile"),  # Rapa Nui es territorio chileno
    "New Guinea": ("Papúa Nueva Guinea", "Papua New Guinea"),
    "Tibet": ("China", "China"),
    "Trinidad": ("Trinidad y Tobago", "Trinidad and Tobago"),
}


def resolve_origin_bm(obj: dict) -> dict:
    """
    Igual idea que resolve_origin_louvre() pero para el BM: preferimos
    findspot (excavación/hallazgo, más específico) sobre productionPlace
    (dónde se hizo la pieza, que puede no ser donde se encontró/tomó).

    A diferencia de Louvre/Met, acá el label mostrado NO es el texto crudo
    scrapeado — es el nombre "limpio" asociado a la palabra clave que
    matcheó (ver BM_SITE_COORDS/BM_COUNTRY_KEYWORDS), porque el texto crudo
    del BM viene con prefijos ("Excavated/Findspot:", etc.) y a veces notas
    de registro larguísimas pegadas. El texto crudo se sigue usando como
    fallback solo cuando no matchea nada (precision "unresolved"), para que
    el diagnóstico de build_geography_bm.py siga siendo útil.
    """
    findspot = (obj.get("findspot") or "").strip()
    production_place = (obj.get("productionPlace") or "").strip()

    label = findspot or production_place
    haystack = " | ".join([findspot, production_place])

    for site, display_es, display_en, (lat, lon) in BM_SITE_COORDS:
        if _keyword_matches(site, haystack):
            origin_country = _country_for_point(lat, lon)
            return {
                "label": display_es, "label_en": display_en, "precision": "site",
                "lat": lat, "lon": lon,
                "country": origin_country[0] if origin_country else None,
                "country_en": origin_country[1] if origin_country else None,
            }

    for country, display_es, display_en, (lat, lon) in BM_COUNTRY_KEYWORDS:
        if _keyword_matches(country, haystack):
            origin_country = BM_COUNTRY_FIELD_OVERRIDES.get(country, (display_es, display_en))
            return {
                "label": display_es, "label_en": display_en, "precision": "country",
                "lat": lat, "lon": lon,
                "country": origin_country[0], "country_en": origin_country[1],
            }

    return {"label": label, "label_en": label, "precision": "unresolved", "lat": None, "lon": None, "country": None, "country_en": None}
