"""
Tests centrados en _keyword_matches() y las tres resolve_origin_*() -- son la
parte del pipeline con mayor historial de bugs reales encontrados en
producción (ver CLAUDE.md, "Bug de matching por substring plano, encontrado y
corregido el 17/08"): antes de ese fix, la keyword "Ur" (Mesopotamia)
matcheaba como substring dentro de "sur" (francés, "sobre"), mandando 12
piezas del Louvre a coordenadas equivocadas sin que nada lo señalara. El test
`test_keyword_matches_word_boundary_regression` de acá abajo es exactamente
ese caso -- si alguien vuelve a cambiar `_keyword_matches` a un `in` plano,
este test lo agarra.
"""
from geocode import (
    CULTURE_KEYWORDS,
    EDITORIAL_ORIGIN_OVERRIDES,
    en_label,
    es_label,
    _keyword_matches,
    resolve_from_culture,
    resolve_origin,
    resolve_origin_bm,
    resolve_origin_louvre,
)


# ---------------------------------------------------------------------------
# _keyword_matches: el bug del 17/08 (substring plano vs. límites de palabra)
# ---------------------------------------------------------------------------

def test_keyword_matches_word_boundary_regression():
    # "Ur" NO debe matchear dentro de "sur" (el caso real: Zodiaque de
    # Dendéra, placeOfDiscovery = "...sur le toit").
    assert _keyword_matches("Ur", "Chapelle Est d'Osiris sur le toit") is False
    # Pero sí debe matchear "Ur" como palabra propia.
    assert _keyword_matches("Ur", "Fouilles menées à Ur en 1922") is True


def test_keyword_matches_case_insensitive():
    assert _keyword_matches("egypt", "Made in: EGYPT") is True


def test_keyword_matches_respects_word_boundaries_both_sides():
    # "Mari" no debe matchear dentro de "Maria" (mismo mecanismo de bug,
    # documentado en CLAUDE.md para una pieza de Atenas/Cápua).
    assert _keyword_matches("Mari", "collection de Maria Something") is False
    assert _keyword_matches("Mari", "Mari sur l'Euphrate") is True


# ---------------------------------------------------------------------------
# resolve_origin (Met): prioridad subregion > region > country > culture
# ---------------------------------------------------------------------------

def test_resolve_origin_prefers_subregion_over_region_and_country():
    obj = {"subregion": "Saqqara", "region": "Memphite Region", "country": "Egypt"}
    result = resolve_origin(obj)
    assert result["precision"] == "subregion"
    assert result["lat"] is not None


def test_resolve_origin_falls_back_to_region_then_country():
    obj_region = {"subregion": "", "region": "Memphite Region", "country": "Egypt"}
    assert resolve_origin(obj_region)["precision"] == "region"

    obj_country = {"subregion": "", "region": "", "country": "Egypt"}
    result = resolve_origin(obj_country)
    assert result["precision"] == "country"
    assert result["label"] == "Egipto"  # es_label() traduce "Egypt" -> "Egipto"


def test_resolve_origin_culture_fallback_prefers_more_specific_keyword():
    # Caso documentado en CULTURE_KEYWORDS: una pieza "Roman, Cypriot" tiene
    # que resolver a Chipre (Cypriot), no a Italia (Roman) -- CULTURE_KEYWORDS
    # está ordenado a propósito con lo más específico primero.
    obj = {"subregion": "", "region": "", "country": "", "culture": "Roman, Cypriot"}
    result = resolve_origin(obj)
    assert result["precision"] == "culture"
    cypriot_coords = dict(CULTURE_KEYWORDS)["Cypriot"]
    assert (result["lat"], result["lon"]) == cypriot_coords


def test_resolve_origin_unresolved_when_nothing_matches():
    obj = {"subregion": "", "region": "", "country": "", "culture": ""}
    result = resolve_origin(obj)
    assert result["precision"] == "unresolved"
    assert result["lat"] is None
    assert result["lon"] is None


# ---------------------------------------------------------------------------
# resolve_origin_louvre: texto libre francés, sitio > país, y la regresión
# real del bug de "Ur"/"sur"
# ---------------------------------------------------------------------------

def test_resolve_origin_louvre_dendera_regression():
    # El caso que encontró el bug originalmente (18/08, Zodiaque de Dendéra):
    # el texto crudo contiene "sur" (francés, "sobre") Y "Dendéra" (el sitio
    # correcto, Egipto). Nota: como "Dendéra" aparece antes que "Ur" en
    # LOUVRE_SITE_COORDS, este caso puntual resuelve bien incluso con un
    # matcher por substring plano (el loop encuentra "Dendéra" primero y
    # nunca llega a "Ur") -- se deja como test de correctitud end-to-end del
    # caso real documentado, no como el test que detecta la regresión (ver
    # el de Luristán, más abajo, que sí la detecta).
    obj = {"placeOfDiscovery": "Temple d'Hathor, Dendéra - Chapelle Est d'Osiris sur le toit"}
    result = resolve_origin_louvre(obj)
    assert result["precision"] == "site"
    assert result["label"] == "Dendera"  # es_label() traduce el exónimo
    ur_coords = (30.9626, 46.1039)
    assert (result["lat"], result["lon"]) != ur_coords


def test_resolve_origin_louvre_luristan_regression():
    # Este es el que sí detecta una reintroducción del bug: "Luristan"
    # contiene el substring "ur" (L-u-r-istan), y "Ur" es un SITIO -- se
    # revisa antes que los países, así que con matching por substring plano
    # esto resolvía a Ur (Irak) sin llegar nunca a matchear "Luristan" como
    # país. Caso real: 7 piezas de Luristán mal geocodificadas antes del fix
    # del 17/08 (ver CLAUDE.md).
    obj = {"placeOfDiscovery": "Luristan"}
    result = resolve_origin_louvre(obj)
    assert result["precision"] == "country"
    assert result["label"] == "Luristán"
    ur_coords = (30.9626, 46.1039)
    assert (result["lat"], result["lon"]) != ur_coords


def test_resolve_origin_louvre_no_false_positive_without_a_real_site():
    # Sin ningún sitio real en el texto, "sur" no debe matchear nada -- antes
    # del fix esto resolvía a Ur igual.
    obj = {"placeOfDiscovery": "Une statue trouvée sur le marché parisien"}
    result = resolve_origin_louvre(obj)
    assert result["precision"] == "unresolved"


def test_resolve_origin_louvre_site_wins_over_country():
    # Saqqara Y Égypte aparecen los dos -- el sitio (más específico) tiene
    # que ganar, no el país genérico.
    obj = {"placeOfDiscovery": "Saqqara-Nord, Égypte"}
    result = resolve_origin_louvre(obj)
    assert result["precision"] == "site"


def test_resolve_origin_louvre_field_priority_discovery_over_creation():
    obj = {
        "placeOfDiscovery": "Saqqara",
        "placeOfCreation": "Thèbes",
        "provenance": "",
    }
    # El label mostrado es placeOfDiscovery > placeOfCreation > provenance,
    # pero el matching busca en los tres combinados -- acá alcanza con
    # confirmar que el label preferido es el de placeOfDiscovery.
    result = resolve_origin_louvre(obj)
    assert result["precision"] == "site"


def test_resolve_origin_louvre_unresolved_keeps_raw_label():
    obj = {"placeOfDiscovery": "Inconnu"}
    result = resolve_origin_louvre(obj)
    assert result["precision"] == "unresolved"
    assert result["label"] == "Inconnu"


# ---------------------------------------------------------------------------
# resolve_origin_bm: prefijos ("Excavated/Findspot:", etc.) no deben romper
# el matching, y el label mostrado nunca es el texto crudo con prefijo
# ---------------------------------------------------------------------------

def test_resolve_origin_bm_matches_despite_label_prefix():
    obj = {"findspot": "Excavated/Findspot: Fort Saint Julien", "productionPlace": ""}
    result = resolve_origin_bm(obj)
    assert result["precision"] == "site"
    # El label mostrado es el "limpio" de BM_SITE_COORDS, no el texto crudo
    # con el prefijo "Excavated/Findspot:" pegado.
    assert "Excavated" not in result["label"]


def test_resolve_origin_bm_falls_back_to_production_place():
    obj = {"findspot": "", "productionPlace": "Made in: Fort Saint Julien"}
    result = resolve_origin_bm(obj)
    assert result["precision"] == "site"


def test_resolve_origin_bm_unresolved_uses_raw_text_as_label():
    obj = {"findspot": "Found/Acquired: somewhere undocumented", "productionPlace": ""}
    result = resolve_origin_bm(obj)
    assert result["precision"] == "unresolved"
    assert result["label"] == "Found/Acquired: somewhere undocumented"


# ---------------------------------------------------------------------------
# es_label / en_label: fallback a texto crudo cuando no hay traducción
# ---------------------------------------------------------------------------

def test_es_label_translates_known_and_falls_back_for_unknown():
    assert es_label("Egypt") == "Egipto"
    assert es_label("Not A Real Place") == "Not A Real Place"


def test_en_label_translates_known_and_falls_back_for_unknown():
    assert en_label("Chypre") == "Cyprus"
    assert en_label("Not A Real Place") == "Not A Real Place"


# ---------------------------------------------------------------------------
# resolve_from_culture: usado directamente por resolve_origin() como último
# fallback (Asian Art / Greek-Roman, donde country/region/subregion vienen
# casi siempre vacíos)
# ---------------------------------------------------------------------------

def test_resolve_from_culture_no_match_returns_none():
    assert resolve_from_culture("Some culture with no keyword") is None


# ---------------------------------------------------------------------------
# EDITORIAL_ORIGIN_OVERRIDES: sanity check de forma -- no valida contenido
# editorial (eso es una decisión curatorial, no algo que un test deba
# opinar), solo que cada entrada tiene el shape que build_geography*.py
# espera antes de llamar a resolve_origin*().
# ---------------------------------------------------------------------------

def test_editorial_overrides_have_expected_shape():
    assert len(EDITORIAL_ORIGIN_OVERRIDES) > 0
    for object_id, override in EDITORIAL_ORIGIN_OVERRIDES.items():
        # Namespaceado (museo:id), no el id crudo -- ver museum_id.py.
        assert ":" in object_id
        assert override["precision"] == "editorial"
        assert isinstance(override["lat"], float)
        assert isinstance(override["lon"], float)
        assert override["label"]
        assert override["label_en"]
