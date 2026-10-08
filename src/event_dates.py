"""Traducción ES -> EN de `event_date` (provenance_events.csv).

`event_date` es texto libre en español ("antes de 1903", "13 de abril de 1868",
"s. XIX", "h. -2450"...). Se traduce por reglas (regex) + un diccionario de
overrides para las frases largas/únicas. `export_web_data.py` lo expone como
`event_date_en`; el frontend lo usa cuando lang == "en".

Mismo criterio de siempre: si una fecha no matchea ninguna regla se deja tal
cual (nunca se inventa). `python src/event_dates.py` imprime las fechas que
todavía tienen palabras en español, para ampliar reglas/overrides.
"""
import csv
import re
from pathlib import Path

MONTHS = {
    "enero": "January", "febrero": "February", "marzo": "March", "abril": "April",
    "mayo": "May", "junio": "June", "julio": "July", "agosto": "August",
    "septiembre": "September", "setiembre": "September", "octubre": "October",
    "noviembre": "November", "diciembre": "December",
}
_MONTH_RE = "|".join(MONTHS)

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def _roman(s: str) -> int:
    total = 0
    prev = 0
    for ch in reversed(s):
        v = ROMAN[ch]
        total += v if v >= prev else -v
        prev = max(prev, v)
    return total


def _ord(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


# Frases largas / únicas, traducidas a mano (clave = texto exacto del CSV).
OVERRIDES = {
    "18/07/1929 (comité); 04/11/1929 (consejo)": "07/18/1929 (committee); 11/04/1929 (council)",
    "1801-1802 (registro Louvre) / 1825 (fuentes secundarias)": "1801-1802 (Louvre record) / 1825 (secondary sources)",
    "1807-09-27 (decreto); inscripta 1810": "1807-09-27 (decree); registered 1810",
    "1816-1939 (familia Raffles, donaciones en 1859 y 1939)": "1816-1939 (Raffles family, donations in 1859 and 1939)",
    "1829-05 (campana de 6 semanas desde el 10/05)": "1829-05 (6-week campaign from 05/10)",
    "1865 (legado); ingreso efectivo 1883": "1865 (bequest); actual entry 1883",
    "1875 (según nota de Quai Branly; una fuente externa sitúa la actividad consular de Brower en Fiyi 'en la década de 1860')": "1875 (per Quai Branly note; an external source places Brower's consular activity in Fiji 'in the 1860s')",
    "1876-1880 (usualmente citado 1877)": "1876-1880 (usually cited as 1877)",
    "1903 (comite 29/01, 20/05, 02/07)": "1903 (committee 01/29, 05/20, 07/02)",
    "1907 (asignacion) / 1919 (traslado fisico)": "1907 (assignment) / 1919 (physical transfer)",
    "1911-1914, reanudada 1919-1920": "1911-1914, resumed 1919-1920",
    "1920 (según fuente académica) o 1926 (según ficha del Met)": "1920 (per academic source) or 1926 (per Met record)",
    "1924-1934 (reparto formal, fecha exacta no documentada)": "1924-1934 (formal division, exact date not documented)",
    "1930 (accesionado en 1932)": "1930 (accessioned 1932)",
    "1981 (fecha de registro; compra puntual sin fecha exacta documentada)": "1981 (registration date; individual purchase with no exact date documented)",
    "1er cuarto del s. V a.C. (antes de -480)": "first quarter of the 5th century BCE (before 480 BCE)",
    "2000-12 (comite 07/12, consejo 13/12, decreto 21/12)": "2000-12 (committee 12/07, council 12/13, decree 12/21)",
    "27/02/1903-fines de mayo de 1903": "02/27/1903-late May 1903",
    "539 BCE (despues de la conquista de Babilonia)": "539 BCE (after the conquest of Babylon)",
    "Registro del Louvre: siglo XIX. Fuentes secundarias asocian fragmentos relacionados a las campañas de Pierre Montet (1921-1924) y Maurice Dunand (1937-1958)": "Louvre record: 19th century. Secondary sources associate related fragments with the campaigns of Pierre Montet (1921-1924) and Maurice Dunand (1937-1958)",
    "Dinasties amorreas, época de Zimri-Lim (?) (h. -1782/-1759)": "Amorite dynasties, era of Zimri-Lim (?) (ca. 1782-1759 BCE)",
    "años 1950 (probablemente asociado al relevamiento de Lanning de 1953-54)": "1950s (probably associated with Lanning's 1953-54 survey)",
    "cultura Santa María (prehispánico; el registro data la pieza en el s. XIX, ver notas)": "Santa María culture (pre-Hispanic; the record dates the piece to the 19th century, see notes)",
    "dataciones discutidas, entre s. II a.C. y s. II d.C.": "disputed dating, between 2nd century BCE and 2nd century CE",
    "h. 700-500 a.C. (narrativamente ambientada en el reinado de Ramses II, h. 1279-1213 a.C.)": "ca. 700-500 BCE (narratively set in the reign of Ramesses II, ca. 1279-1213 BCE)",
    "h. finales del III-comienzos del II milenio a.C.": "ca. late 3rd-early 2nd millennium BCE",
    "h. 1876-1881 (antes de la misión final de 1882)": "ca. 1876-1881 (before the final 1882 mission)",
    "h. 1860-1865, sin fecha exacta documentada": "ca. 1860-1865, no exact date documented",
    "finales del primer milenio CE": "late 1st millennium CE",
    "segunda mitad del II milenio a.C.": "second half of the 2nd millennium BCE",
    "posiblemente s. XII, documentada desde 1505": "possibly 12th century, documented since 1505",
    "s. XII, antes de la donacion a Saint-Denis": "12th century, before the donation to Saint-Denis",
    "s. XIX (colonia francesa desde 1853)": "19th century (French colony since 1853)",
    "s. XIX-XX (sitio de fabricación sin resolver, ver notas)": "19th-20th century (manufacture site unresolved, see notes)",
    "1ª mitad del s. XIII": "first half of the 13th century",
    "Ano 2 de la revuelta, 67-68 d.C.": "Year 2 of the revolt, 67-68 CE",
    "100 BCE-700 CE aprox. (atribucion incierta)": "ca. 100 BCE-700 CE (uncertain attribution)",
    "1826-1829 o 1837-1840 (sin resolver)": "1826-1829 or 1837-1840 (unresolved)",
    "1902-1903 o fines de 1930s": "1902-1903 or late 1930s",
    "1618 (algunas fuentes secundarias dan 1608)": "1618 (some secondary sources give 1608)",
    "1776-1795 (fecha exacta no identificada)": "1776-1795 (exact date not identified)",
    "1868-03 (fin de marzo)": "1868-03 (end of March)",
    "antes de 480 BCE (aprox. 1er cuarto del s. V a.C.)": "before 480 BCE (approx. first quarter of the 5th century BCE)",
    "ca. 1250 (2do-3er cuarto s. XIII)": "ca. 1250 (2nd-3rd quarter of the 13th century)",
    "comienzos Dinastía 12 (contexto de excavación)": "early Dynasty 12 (excavation context)",
    "dinastia VI, primera mitad, h. -2323 a -2255": "Dynasty VI, first half, ca. 2323-2255 BCE",
    "s. X-IX a.C. (reinado de Elibaal de Biblos)": "10th-9th centuries BCE (reign of Elibaal of Byblos)",
    "s. XIX (segunda mitad)": "19th century (second half)",
    "ca. siglo I a.C.-I d.C.": "ca. 1st century BCE-1st century CE",
    "Dinastía XVIII (atribución estilística), h. -1539/-1295": "Dynasty XVIII (stylistic attribution), ca. 1539-1295 BCE",
}

# Reglas en orden. Cada una: (regex, reemplazo o función).
_RULES = []


def _rule(pattern, repl, flags=re.IGNORECASE):
    _RULES.append((re.compile(pattern, flags), repl))


# --- fechas con mes -------------------------------------------------------
def _day_month_year(m):
    d1, d2, mon, y = m.group(1), m.group(2), m.group(3).lower(), m.group(4)
    days = f"{d1}-{d2}" if d2 else d1
    return f"{MONTHS[mon]} {days}, {y}"


_rule(rf"(\d{{1,2}})(?:-(\d{{1,2}}))? de ({_MONTH_RE}) de (\d{{4}})", _day_month_year)
_rule(rf"({_MONTH_RE}) de (\d{{4}})", lambda m: f"{MONTHS[m.group(1).lower()]} {m.group(2)}")
_rule(rf"fines de ({_MONTH_RE})", lambda m: f"late {MONTHS[m.group(1).lower()]}")

# --- años BCE expresados como negativos ------------------------------------
_rule(r"antes de -(\d+)", r"before \1 BCE")
_rule(
    r"(?:\bh\.|\bvers)\s*-(\d+)(?:\s*(?:/|a|-)\s*-?(\d+))?",
    lambda m: f"ca. {m.group(1)}{'-' + m.group(2) if m.group(2) else ''} BCE",
)

# --- décadas ----------------------------------------------------------------
_rule(r"comienzos de la d[eé]cada de (\d{3})0", r"early \g<1>0s")
_rule(
    r"d[eé]cadas? de (\d{3})0(?:-(\d{3})0)?",
    lambda m: f"{m.group(1)}0s" + (f"-{m.group(2)}0s" if m.group(2) else ""),
)
_rule(r"a[nñ]os (\d{3})0", r"\g<1>0s")

# --- siglos -----------------------------------------------------------------
_QUAL = {
    "mediados": "mid-", "fines": "late ", "finales": "late ", "comienzos": "early ",
    "principios": "early ", "inicio": "early ", "inicios": "early ", "início": "early ",
    "primera mitad": "first half of the ", "segunda mitad": "second half of the ",
    "primer cuarto": "first quarter of the ",
}
_QUAL_RE = "|".join(sorted(_QUAL, key=len, reverse=True))


def _century(m):
    qual = (m.group(1) or "").lower()
    r1, r2 = m.group(2), m.group(3)
    era = {"a.c.": " BCE", "d.c.": " CE"}.get((m.group(4) or "").lower(), "")
    prefix = _QUAL.get(qual, "")
    if r2:
        body = f"{_ord(_roman(r1))}-{_ord(_roman(r2))} centuries"
    else:
        body = f"{_ord(_roman(r1))} century"
    return f"{prefix}{body}{era}"


_rule(r"siglo XX medio", "mid-20th century")
_rule(
    rf"(?:\b({_QUAL_RE})\s+(?:del |de la |de )?)?(?:siglos?|\bs\.)\s*((?-i:[IVXL]+))(?:\s*-\s*(?:s\.\s*)?((?-i:[IVXL]+)))?(?:\s*(a\.C\.|d\.C\.))?",
    _century,
)

# --- vocabulario general ----------------------------------------------------
_WORDS = [
    (r"sin fecha exacta documentada", "no exact date documented"),
    (r"sin fecha precisa documentada", "no precise date documented"),
    (r"sin fecha documentada", "no documented date"),
    (r"sin fecha espec[ií]fica", "no specific date"),
    (r"sin fecha exacta", "no exact date"),
    (r"sin fecha", "undated"),
    (r"fecha exacta desconocida", "exact date unknown"),
    (r"fecha exacta no documentada", "exact date not documented"),
    (r"fecha desconocida", "unknown date"),
    (r"fecha indeterminada", "undetermined date"),
    (r"fecha incierta", "uncertain date"),
    (r"desconocida", "unknown"),
    (r"antes de donaci[oó]n", "before donation"),
    (r"antes de(?:l)?", "before"),
    (r"anterior a", "before"),
    (r"posterior a", "after"),
    (r"comienzos Dinast[ií]a", "early Dynasty"),
    (r"\bdesde\b", "since"),
    (r"\bhasta\b", "until"),
    (r"entre h\. (\d+) y (\d+)", r"between ca. \1 and \2"),
    (r"entre (\d+) y (\d+)", r"between \1 and \2"),
    (r"(\d) y (\d)", r"\1 and \2"),
    (r"(\d) a (\d)", r"\1 to \2"),
    (r"en adelante", "onward"),
    (r"en curso", "ongoing"),
    (r"\bh\.", "ca."),
    (r"aprox\.", "approx."),
    (r"\bposiblemente\b", "possibly"),
    (r"\bprobablemente\b", "probably"),
    (r"\bprobable\b", "probable"),
    (r"\btentativo\b", "tentative"),
    (r"\bestimado\b", "estimated"),
    (r"\bsin resolver\b", "unresolved"),
    (r"\bsin confirmar\b", "unconfirmed"),
    (r"\bsegún\b", "per"),
    (r"datación por radiocarbono", "radiocarbon dating"),
    (r"\bcabeza\b", "head"),
    (r"\bcuerpo\b", "body"),
    (r"\bmision de\b", "mission of"),
    (r"\bmisión de\b", "mission of"),
    (r"\bantig[uü]edad\b", "antiquity"),
    (r"\bper[ií]odo prehisp[aá]nico\b", "pre-Hispanic period"),
    (r"\bper[ií]odo inca\b", "Inca period"),
    (r"\bprehistoria\b", "prehistory"),
    (r"\bBronce Medio - Bronce Reciente\b", "Middle Bronze - Late Bronze Age"),
    (r"\bBronce Reciente II\b", "Late Bronze Age II"),
    (r"\bBronce Medio\b", "Middle Bronze Age"),
    (r"\bDinast[ií]co Arcaico\b", "Early Dynastic"),
    (r"\bReino Antiguo\b", "Old Kingdom"),
    (r"\bEdad del Hierro\b", "Iron Age"),
    (r"\bNeo-asirio\b", "Neo-Assyrian"),
    (r"\bneohitita\b", "Neo-Hittite"),
    (r"\bdinast[ií]a de ([A-Z]\w+)", r"\1 dynasty"),
    (r"\bdinast[ií]as\b", "Dynasties"),
    (r"\bdinast[ií]a\b", "Dynasty"),
    (r"\breinado de\b", "reign of"),
    (r"\bAjenat[oó]n\b", "Akhenaten"),
    (r"\bAkenat[oó]n\b", "Akhenaten"),
    (r"\bDar[ií]o I\b", "Darius I"),
    (r"\bAsurbanipal\b", "Ashurbanipal"),
    (r"\bRamses\b", "Ramesses"),
    (r"\bBiblos\b", "Byblos"),
    (r"\bTaharqo\b", "Taharqa"),
    (r"\bNazi-Maruttash\b", "Nazimaruttash"),
]
for _p, _r in _WORDS:
    _rule(_p, _r)

_rule(r"\bd\.C\.", "CE")
_rule(r"\ba\.C\.", "BCE")


def translate_event_date(value):
    if not value:
        return value
    if value in OVERRIDES:
        return OVERRIDES[value]
    out = value
    for rx, repl in _RULES:
        out = rx.sub(repl, out)
    return re.sub(r"\s+", " ", out).strip()


_SPANISH_HINT = re.compile(
    r"\b(de|del|la|el|los|las|sin|antes|desde|hasta|entre|siglo|fecha|mitad|"
    r"fines|mediados|comienzos|principios|sobre|probablemente|según|reinado|"
    r"cuarto|década|decada|años|aprox)\b",
    re.IGNORECASE,
)

if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent / "data" / "enrichment" / "provenance_events.csv"
    seen = sorted({r["event_date"] for r in csv.DictReader(open(path, encoding="utf-8"))})
    for v in seen:
        t = translate_event_date(v)
        if t != v or _SPANISH_HINT.search(v):
            flag = "  <-- REVISAR" if _SPANISH_HINT.search(t) else ""
            print(f"{v!r:70} -> {t!r}{flag}")
