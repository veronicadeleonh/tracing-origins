"""
Geocodificación estática (sin llamadas a Nominatim en bulk, prohibido por su
política de uso). Tabla de coordenadas armada a mano, a expandir a medida que
aparecen nuevos países/regiones en los datos.

Prioridad de resolución: subregion > region > country.
"""

from __future__ import annotations

# Coordenadas del propio museo (destino de las líneas)
MET_COORDS = (40.7794, -73.9632)
LOUVRE_COORDS = (48.8606, 2.3376)
BM_COORDS = (51.5194, -0.1270)

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
]


def resolve_from_culture(culture: str) -> dict | None:
    for keyword, (lat, lon) in CULTURE_KEYWORDS:
        if keyword.lower() in culture.lower():
            return {"label": culture, "precision": "culture", "lat": lat, "lon": lon}
    return None


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
        return {"label": subregion, "precision": "subregion", "lat": lat, "lon": lon}

    if region in REGION_COORDS:
        lat, lon = REGION_COORDS[region]
        return {"label": region, "precision": "region", "lat": lat, "lon": lon}

    if country in COUNTRY_COORDS:
        lat, lon = COUNTRY_COORDS[country]
        return {"label": country, "precision": "country", "lat": lat, "lon": lon}

    culture = (obj.get("culture") or "").strip()
    if culture:
        from_culture = resolve_from_culture(culture)
        if from_culture:
            return from_culture

    raw_label = subregion or region or country or culture or ""
    return {"label": raw_label, "precision": "unresolved", "lat": None, "lon": None}


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
        if site.lower() in haystack.lower():
            return {"label": label or site, "precision": "site", "lat": lat, "lon": lon}

    for country, (lat, lon) in LOUVRE_COUNTRY_KEYWORDS:
        if country.lower() in haystack.lower():
            return {"label": label or country, "precision": "country", "lat": lat, "lon": lon}

    return {"label": label, "precision": "unresolved", "lat": None, "lon": None}


# ---------------------------------------------------------------------------
# British Museum: findspot/productionPlace vienen en inglés, con un prefijo
# de etiqueta ("Excavated/Findspot:", "Found/Acquired:", "Made in:") seguido
# de un nombre de sitio en texto libre — más simple que el francés del
# Louvre, pero igual necesita su propia lista (nombres de sitio en inglés,
# no siempre los mismos que ya tenemos para otros museos).

BM_SITE_COORDS = [
    ("Fort Saint Julien", (31.4022, 30.4181)),  # Rosetta / el-Rashid, Egipto
    ("Kawa", (19.0800, 30.3600)),  # Nubia, Sudán
    ("Nimrud", (36.0994, 43.3250)),
    ("Trincomalee", (8.5711, 81.2335)),
    ("Benin City", (6.3350, 5.6037)),
    ("Orongo", (-27.1836, -109.4306)),  # Rapa Nui / Isla de Pascua — sitio ceremonial, Hoa Hakananai'a
    ("Rano Kao", (-27.1667, -109.4333)),  # Rapa Nui / Isla de Pascua
    ("Parthenon", (37.9715, 23.7267)),  # Acrópolis, Atenas
    ("Maqdala", (11.8000, 39.7000)),  # Amba Mariam, Etiopía — colección Maqdala (1868)
    ("Kumase", (6.6885, -1.6244)),  # Kumasi, capital histórica del reino Asante
    ("Asante Region", (6.7500, -1.5000)),  # Ghana
    ("Yuanmingyuan", (40.0084, 116.2966)),  # Antiguo Palacio de Verano, Beijing
    ("Amaravati", (16.5730, 80.3567)),  # Andhra Pradesh, India
    ("Takht-i Kuwad", (37.1500, 68.3667)),  # Tesoro de Oxus, actual Tayikistán
    ("Babylon", (32.5425, 44.4213)),  # Irak
    ("Nineveh", (36.3600, 43.1500)),  # Irak
    ("Queensland", (-22.5752, 144.0848)),
    ("Ife", (7.4905, 4.5521)),  # Nigeria, distinto de Benin City
    ("Haida Gwaii", (53.2500, -132.0000)),  # Columbia Británica, Canadá
    ("Trujillo", (-8.1116, -79.0290)),  # costa norte de Perú, cultura moche
    ("Gandhara", (34.0000, 71.5000)),  # actual Pakistán
    ("Angkor", (13.4125, 103.8670)),  # Camboya
    ("Carchemish", (36.8167, 38.0167)),  # frontera Turquía/Siria
    ("Aksum", (14.1211, 38.7167)),  # Etiopía
    ("Sepik River", (-4.1000, 143.9000)),  # Nueva Guinea
    ("Marib", (15.4300, 45.3286)),  # Yemen, antigua capital sabea
    ("Faras", (22.1833, 31.9000)),  # Nubia, Sudán
    ("Hawaiian Islands", (19.8968, -155.5828)),
    ("Hawaii", (19.8968, -155.5828)),
    ("Northwest Territories", (64.8255, -124.8457)),  # Canadá
    ("Hokkaido", (43.2203, 142.8635)),  # Japón — territorio ainu
    ("Zanzibar", (-6.1659, 39.2026)),  # Tanzania
    ("Ambrym", (-16.2500, 168.1167)),  # Vanuatu
    ("Amathus", (34.7167, 33.1333)),  # Chipre
    ("Cartagena", (10.3910, -75.4794)),  # Colombia
    ("Rajshahi", (24.3745, 88.6042)),  # Bangladés
]

BM_COUNTRY_KEYWORDS = [
    ("Sudan", (12.8628, 30.2176)),
    ("Egypt", (26.8206, 30.8025)),
    ("Sri Lanka", (7.8731, 80.7718)),
    ("Nigeria", (9.0820, 8.6753)),
    ("Iraq", (33.2232, 43.6793)),
    ("Iran", (32.4279, 53.6880)),
    ("Ethiopia", (9.1450, 40.4897)),
    ("Ghana", (7.9465, -1.0232)),
    ("Greece", (39.0742, 21.8243)),
    ("Turkey", (38.9637, 35.2433)),
    ("China", (35.8617, 104.1954)),
    ("India", (20.5937, 78.9629)),
    ("Easter Island", (-27.1127, -109.3497)),
    ("New Zealand", (-40.9006, 174.8860)),
    ("Tajikistan", (38.8610, 71.2761)),
    ("Australia", (-25.2744, 133.7751)),
    ("Democratic Republic of Congo", (-4.0383, 21.7587)),
    ("South Africa", (-30.5595, 22.9375)),
    ("Mexico", (23.6345, -102.5528)),
    ("Korea", (35.9078, 127.7669)),
    ("Cambodia", (12.5657, 104.9910)),
    ("Jamaica", (18.1096, -77.2975)),
    ("Japan", (36.2048, 138.2529)),
    ("Pakistan", (30.3753, 69.3451)),
    ("Yemen", (15.5527, 48.5164)),
    ("Papua New Guinea", (-6.3149, 143.9555)),
    ("New Guinea", (-6.3149, 143.9555)),
    ("Fiji", (-17.7134, 178.0650)),
    ("Solomon Islands", (-9.6457, 160.1562)),
    ("Canada", (56.1304, -106.3468)),
    ("Namibia", (-22.9576, 18.4904)),
    ("Kenya", (-0.0236, 37.9062)),
    ("Cyprus", (35.1264, 33.4299)),
    ("Cameroon", (7.3697, 12.3547)),
    ("Bangladesh", (23.6850, 90.3563)),
]


def resolve_origin_bm(obj: dict) -> dict:
    """
    Igual idea que resolve_origin_louvre() pero para el BM: preferimos
    findspot (excavación/hallazgo, más específico) sobre productionPlace
    (dónde se hizo la pieza, que puede no ser donde se encontró/tomó).
    """
    findspot = (obj.get("findspot") or "").strip()
    production_place = (obj.get("productionPlace") or "").strip()

    label = findspot or production_place
    haystack = " | ".join([findspot, production_place])

    for site, (lat, lon) in BM_SITE_COORDS:
        if site.lower() in haystack.lower():
            return {"label": label or site, "precision": "site", "lat": lat, "lon": lon}

    for country, (lat, lon) in BM_COUNTRY_KEYWORDS:
        if country.lower() in haystack.lower():
            return {"label": label or country, "precision": "country", "lat": lat, "lon": lon}

    return {"label": label, "precision": "unresolved", "lat": None, "lon": None}
