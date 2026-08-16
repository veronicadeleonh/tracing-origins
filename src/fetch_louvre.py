"""
Descarga objetos del Louvre vía collections.louvre.fr, con un puente por
Wikidata para descubrir qué arkIds pertenecen a cada departamento.

Por qué el puente: collections.louvre.fr da JSON por objeto individual
(agregando ".json" a la URL del ark, ver src/museum_id.py y la doc en
https://collections.louvre.fr/en/page/documentationJSON), pero:
  - su robots.txt bloquea /search/export (el endpoint de descarga masiva) para
    todos los user-agents, y
  - la búsqueda interactiva (/en/recherche-avancee) está detrás de un CAPTCHA.
No hay forma automatizada ni respetuosa de listar "todos los objetos del
departamento X" directo desde el sitio del Louvre.

Wikidata sí tiene una propiedad dedicada, P9394 ("Louvre Museum ARK ID"), con
~480k registros (casi 1:1 con la colección completa). Cruzando P9394 con P195
(colección = departamento curatorial, como entidad Wikidata) conseguimos listas
de arkIds por departamento vía SPARQL público, sin tocar el endpoint bloqueado
ni la búsqueda con CAPTCHA. Priorizamos por wikibase:sitelinks (más artículos
de Wikipedia enlazados = pieza más documentada/conocida), que además calza
bien con la idea de "piezas bandera" del proyecto.

Uso:
    python src/fetch_louvre.py --per-department 60
    python src/fetch_louvre.py --department egyptian --per-department 100
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "louvre_objects_raw.json"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
OBJECT_JSON_TMPL = "https://collections.louvre.fr/en/ark:/53355/{ark}.json"
USER_AGENT = "colonial-museum-routes/0.1 (proyecto personal de portfolio; contacto: v.dleon@gmail.com)"

# QID del departamento curatorial en Wikidata (propiedad P195 = colección).
DEPARTMENTS = {
    "egyptian": "Q3044749",
    "near_eastern": "Q3044751",
    "greek_etruscan_roman": "Q3044747",
    "islamic": "Q3044748",
}


def sparql_arks(qid: str, limit: int) -> list[str]:
    query = f"""
    SELECT ?ark WHERE {{
      ?item wdt:P9394 ?ark; wdt:P195 wd:{qid}.
      OPTIONAL {{ ?item wikibase:sitelinks ?sitelinks. }}
    }}
    ORDER BY DESC(?sitelinks)
    LIMIT {limit}
    """
    url = SPARQL_ENDPOINT + "?query=" + urllib.parse.quote(query) + "&format=json"
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    # P9394 (Louvre Museum ARK ID) está cargado de forma inconsistente en
    # Wikidata: la mayoría de los valores incluyen el prefijo "cl" que es
    # parte real del ark (ej. "cl010277627"), pero algunos ediciones lo
    # cargaron sin él ("010277627"). Sin normalizar esto, esos casos:
    # (a) tiran 404 al armar la URL porque el ark real necesita el "cl", y
    # (b) no deduplican contra el cache existente (que sí tiene el "cl"),
    # así que se reintentan como "nuevos" en cada corrida.
    raw_arks = [b["ark"]["value"].strip() for b in data["results"]["bindings"]]
    return [a if a.startswith("cl") else f"cl{a}" for a in raw_arks]


def fetch_object(ark: str) -> dict:
    url = OBJECT_JSON_TMPL.format(ark=ark)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def load_existing() -> dict[str, dict]:
    if not RAW_PATH.exists():
        return {}
    data = json.loads(RAW_PATH.read_text())
    return {obj["arkId"]: obj for obj in data}


def save(objects_by_ark: dict[str, dict]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = [objects_by_ark[k] for k in sorted(objects_by_ark)]
    RAW_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2))


def fetch_departments(dept_keys: list[str], per_department: int, delay: float = 0.3) -> None:
    objects_by_ark = load_existing()

    for dept_key in dept_keys:
        qid = DEPARTMENTS[dept_key]
        arks = sparql_arks(qid, per_department)
        pending = [a for a in arks if a not in objects_by_ark]
        print(f"{dept_key} ({qid}): {len(arks)} arks en Wikidata, {len(pending)} nuevos a bajar")

        for ark in pending:
            try:
                obj = fetch_object(ark)
            except Exception as exc:  # urllib no tiene una excepción base tan cómoda como requests
                print(f"  error en {ark}: {exc}")
                continue
            obj["_wikidataDepartmentKey"] = dept_key
            objects_by_ark[ark] = obj
            time.sleep(delay)

        save(objects_by_ark)
        print(f"  guardado, {len(objects_by_ark)} objetos totales en {RAW_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--department", choices=list(DEPARTMENTS), help="Solo un departamento (default: todos)")
    parser.add_argument("--per-department", type=int, default=60, help="Cuántos arks pedir por departamento")
    parser.add_argument("--delay", type=float, default=0.3, help="Segundos entre requests a collections.louvre.fr")
    args = parser.parse_args()

    keys = [args.department] if args.department else list(DEPARTMENTS)
    fetch_departments(keys, per_department=args.per_department, delay=args.delay)
