from museum_id import BRITISH_MUSEUM, LOUVRE, MET, namespaced_id


def test_namespaced_id_basic():
    assert namespaced_id(MET, 96404) == "met:96404"
    assert namespaced_id(LOUVRE, "cl010119651") == "louvre:cl010119651"
    assert namespaced_id(BRITISH_MUSEUM, "W_1970-0604-2") == "bm:W_1970-0604-2"


def test_namespaced_id_accepts_int_or_str_raw_id():
    # objectID crudo del Met es int, Louvre/BM son str -- namespaced_id no
    # debería importarle el tipo, solo formatearlo.
    assert namespaced_id("met", 123) == namespaced_id("met", "123")
