"""
Descarga objetos del Musée du Quai Branly vía su propio backend interno,
ccProxy.ashx (endpoint sin documentar, encontrado por reconocimiento manual
en el navegador conectado de Cowork el 31/08 -- ver CLAUDE.md, sección
"Cuarta fuente: Musée du Quai Branly" bajo "Pendiente de decidir", para el
detalle completo de cómo se encontró y qué se probó antes de escribir esto).

Por qué este endpoint y no un scraper de HTML: el sitio público
(collections.quaibranly.fr) es una SPA de React puramente client-side, sin
página de objeto renderizada en servidor ni endpoint JSON documentado. Pero
su propio bundle JS llama a `ccProxy.ashx` (un handler genérico ASP.NET) para
correr las búsquedas -- y ese mismo endpoint responde igual de bien a un GET
simple con query string, sin sesión ni cookie, algo confirmado con
`mcp__workspace__web_fetch` directo (no solo el navegador) y a escala real
(pedidos de cientos de registros, paginación sin duplicados). `robots.txt` de
este dominio está completamente abierto (`Disallow:` vacío), a diferencia del
Louvre (que bloquea `/search/export`) o el BM (que exige `Crawl-delay: 20`).

DSL de búsqueda: expresiones anidadas `and(...)`/`or(...)` sobre paths estilo
XPath bajo `/Record/...`. Acá se usa siempre la misma forma:
    and(/Record/Classification2=Objet;/Record/Department="<departamento>")
`Classification2=Objet` excluye fotografías/archivos/libros (el corpus mixto
del sitio es ~887k registros; solo ~171k son objetos físicos). El filtro por
`Department` usa las categorías curatoriales reales del propio museo --
decisión explícita de la usuaria el 31/08, en vez de descubrir por continente
vía el campo `Toponyme` (que hubiera sido más parecido al puente de Wikidata
del Louvre). Los 5 valores reales de `Department` para objetos físicos,
confirmados por conteo real contra el índice (31/08): Afrique (72.145),
Amériques (32.046), Asie (36.330), Océanie (27.278), y el más relevante
temáticamente para este proyecto -- "Mondialisation historique et
contemporaine" (3.102), un departamento temático (no geográfico) que agrupa
objetos que documentan el propio encuentro colonial/histórico (arte
orientalista, piezas que pasaron por exposiciones coloniales), no la cultura
de origen. "Europe" no existe como departamento (0 resultados) -- el museo es
de artes extra-europeas por diseño, mismo espíritu que la ausencia de un
departamento africano/americano en el Louvre (ver CLAUDE.md, "Hallazgo
estructural").

Pidiendo `fields=*` en la búsqueda misma (no un segundo fetch por objeto) ya
trae el registro completo -- incluido `ConXother`, un campo de procedencia/
adquisición estructurado (actor + tipo de rol + fecha) que ningún otro de los
3 museos expone de forma tan directa, ver CLAUDE.md para ejemplos reales
encontrados en el reconocimiento (una pieza con nota curatorial interna sobre
su propia restitución, otra que documenta haber pasado por el "Musée
permanent des Colonies" de los años 1930).

Uso:
    python src/fetch_quaibranly.py --per-department 40
    python src/fetch_quaibranly.py --department afrique --per-department 60
"""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "quaibranly_objects_raw.json"
ENDPOINT = "https://collections.quaibranly.fr/ccProxy.ashx/"
USER_AGENT = "colonial-museum-routes/0.1 (proyecto personal de portfolio; contacto: v.dleon@gmail.com)"

# Valor real de /Record/Department en el sitio -> clave corta que usamos acá.
# Los 5 valores son, en la práctica, exhaustivos para Classification2=Objet
# (suman 170.901 de un total de 171.190 objetos físicos) -- ver docstring.
DEPARTMENTS = {
    "afrique": "Afrique",
    "ameriques": "Amériques",
    "asie": "Asie",
    "oceanie": "Océanie",
    "mondialisation": "Mondialisation historique et contemporaine",
}

PAGE_SIZE = 50  # registros por request; el endpoint respondió bien hasta 200 en pruebas, nos quedamos conservadores


def _encode_query(query: str) -> str:
    # El endpoint espera "(" ")" ";" literales (sin percent-encode) pero SÍ
    # espera "/" "=" '"' y espacios/acentos percent-encoded -- confirmado
    # reproduciendo exactamente la forma de request que funcionó en el
    # reconocimiento manual (ver docstring). safe="();" preserva justo esos
    # tres caracteres de la sintaxis del DSL.
    return urllib.parse.quote(query, safe="();")


def search_department(dept_label: str, start: int, count: int) -> tuple[list[dict], int]:
    """Pide un rango [start, start+count-1] (1-indexado) de registros completos
    para un departamento. Devuelve (registros, total_del_departamento)."""
    query = f'and(/Record/Classification2=Objet;/Record/Department="{dept_label}")'
    params = {
        "action": "get",
        "command": "search",
        "query": _encode_query(query),
        "fields": "*",
        "range": f"{start}-{start + count - 1}",
        "responseFormat": "json",
    }
    # Armamos la URL a mano en vez de con urlencode porque query ya viene
    # pre-encodeada con las reglas particulares de _encode_query() -- pasarla
    # de nuevo por urlencode la doble-encodearía.
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{ENDPOINT}?{query_string}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)

    total = int(payload.get("request", {}).get("count", 0))
    records_node = payload.get("records", {})
    record = records_node.get("record", [])
    if isinstance(record, dict):  # el endpoint devuelve un dict pelado (no lista) cuando hay un solo resultado
        record = [record]

    objects = [r["data"]["Record"] for r in record if "data" in r and "Record" in r["data"]]
    return objects, total


def load_existing() -> dict[str, dict]:
    if not RAW_PATH.exists():
        return {}
    data = json.loads(RAW_PATH.read_text())
    return {str(obj["ccObjectID"]): obj for obj in data}


def save(objects_by_id: dict[str, dict]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = [objects_by_id[k] for k in sorted(objects_by_id, key=int)]
    RAW_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2))


def fetch_departments(dept_keys: list[str], per_department: int, delay: float = 0.3) -> None:
    objects_by_id = load_existing()

    for dept_key in dept_keys:
        dept_label = DEPARTMENTS[dept_key]
        collected = 0
        start = 1
        new_count = 0
        total = None

        while collected < per_department:
            page = min(PAGE_SIZE, per_department - collected)
            try:
                records, total = search_department(dept_label, start, page)
            except urllib.error.URLError as exc:
                print(f"  error pidiendo {dept_key} (rango {start}-{start + page - 1}): {exc}")
                break

            if not records:
                break  # nos quedamos sin resultados antes de llegar a per_department

            for obj in records:
                cc_id = str(obj["ccObjectID"])
                is_new = cc_id not in objects_by_id
                obj["_qbDepartment"] = dept_key
                objects_by_id[cc_id] = obj
                if is_new:
                    new_count += 1

            collected += len(records)
            start += len(records)
            time.sleep(delay)

        print(f"{dept_key} ({dept_label}): {total if total is not None else '?'} objetos en el índice, "
              f"{collected} pedidos, {new_count} nuevos guardados")
        save(objects_by_id)
        print(f"  guardado, {len(objects_by_id)} objetos totales en {RAW_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--department", choices=list(DEPARTMENTS), help="Solo un departamento (default: todos)")
    parser.add_argument("--per-department", type=int, default=40, help="Cuántos objetos pedir por departamento")
    parser.add_argument("--delay", type=float, default=0.3, help="Segundos entre requests a collections.quaibranly.fr")
    args = parser.parse_args()

    keys = [args.department] if args.department else list(DEPARTMENTS)
    fetch_departments(keys, per_department=args.per_department, delay=args.delay)
