"""
Geocodificación estática (sin llamadas a Nominatim en bulk, prohibido por su
política de uso). Tabla de coordenadas armada a mano, a expandir a medida que
aparecen nuevos países/regiones en los datos.

Prioridad de resolución: subregion > region > country.
"""

from __future__ import annotations

# Coordenadas del propio museo (Met = Nueva York)
MET_COORDS = (40.7794, -73.9632)

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

    raw_label = subregion or region or country or ""
    return {"label": raw_label, "precision": "unresolved", "lat": None, "lon": None}
