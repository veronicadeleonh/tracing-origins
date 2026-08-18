"""
Busca en data/raw/*_objects_raw.json (ya descargado por fetch_met.py /
fetch_louvre.py / fetch_bm.py) los campos relevantes para investigación de
layer 3 (historia de propietarios, adquisición, hallazgo) de una pieza, y los
imprime como JSON chico -- sin bibliografía, sin lista de imágenes, sin menú
de navegación.

Por qué existe (18/08): durante varias sesiones de investigación de layer 3
se re-pidieron en vivo páginas del Louvre y del British Museum para piezas
que YA estaban completas en los raw JSON de este repo -- el ejemplo más claro
es el altar sabeo del BM (bm:W_1970-0604-2) y las 5 piezas del Louvre de la
ronda del 18/08: los 3 fetch_*.py ya habían bajado esos objetos hace tiempo,
con el campo `curatorComments`/`objectHistory`/`previousOwner` completo, y
terminamos gastando tokens de la sesión de Claude leyendo la página HTML
completa (con bibliografía de 30+ referencias, galería de imágenes, banner
de cookies) para extraer 3 líneas de esa data. Este script filtra antes de
que Claude lo vea.

No hace falta red para correr esto -- es lectura local pura. Solo hace falta
ir a la web en vivo (ver web_research.py) cuando: (a) la pieza todavía no
está en ningún raw JSON (objeto nuevo, no bajado todavía por los fetch_*.py),
o (b) se necesita investigación adicional que el registro del museo no tiene
(Wikipedia, prensa, disputas) -- eso es investigación libre, no un lookup.

Uso:
    python src/research_lookup.py louvre:cl010119651
    python src/research_lookup.py bm:W_1970-0604-2
    python src/research_lookup.py met:240028
    python src/research_lookup.py met:240028 louvre:cl010119651 bm:W_1970-0604-2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# Campos relevantes para procedencia por museo -- el resto (bibliografía,
# imágenes, índices de facetas, menús) se descarta a propósito.
MET_FIELDS = [
    "objectID", "title", "objectName", "department", "culture", "period",
    "dynasty", "objectDate", "medium", "creditLine", "accessionYear",
    "excavation", "geographyType", "country", "region", "subregion",
    "artistDisplayName", "artistDisplayBio", "constituents", "objectURL",
]
LOUVRE_FIELDS = [
    "arkId", "title", "displayDateCreated", "dateCreated", "previousOwner",
    "acquisitionDetails", "placeOfCreation", "placeOfDiscovery", "provenance",
    "dateOfDiscovery", "objectHistory", "historicalContext",
    "jabachInventory", "napoleonInventory", "objectNumber", "collection",
    "ownedBy", "heldBy", "url",
]
BM_FIELDS = [
    "objectID", "title", "pageTitle", "description", "objectType",
    "museumNumber", "culturesPeriods", "productionDate", "productionPlace",
    "excavator", "findspot", "materials", "curatorComments",
    "associatedNames", "acquisitionName", "acquisitionDate", "department",
    "url",
]


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def lookup(namespaced_id: str) -> dict | None:
    museum, _, native_id = namespaced_id.partition(":")
    if museum == "met":
        objects = _load(DATA_RAW / "met_objects_raw.json")
        match = next((o for o in objects if str(o.get("objectID")) == native_id), None)
        fields = MET_FIELDS
    elif museum == "louvre":
        objects = _load(DATA_RAW / "louvre_objects_raw.json")
        match = next((o for o in objects if o.get("arkId") == native_id), None)
        fields = LOUVRE_FIELDS
    elif museum == "bm":
        objects = _load(DATA_RAW / "bm_objects_raw.json")
        match = next((o for o in objects if o.get("objectID") == native_id), None)
        fields = BM_FIELDS
    else:
        print(f"Museo desconocido en '{namespaced_id}' (esperado met:/louvre:/bm:)", file=sys.stderr)
        return None

    if match is None:
        return None

    filtered = {f: match.get(f) for f in fields if match.get(f) not in (None, "", [], {})}
    filtered["_namespacedId"] = namespaced_id
    return filtered


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    results = {}
    missing = []
    for arg in sys.argv[1:]:
        found = lookup(arg)
        if found is None:
            missing.append(arg)
        else:
            results[arg] = found

    if results:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    if missing:
        print(
            f"\nNo encontrado en raw JSON local (no bajado todavía, o el "
            f"objectID no matchea): {', '.join(missing)}",
            file=sys.stderr,
        )
        print(
            "Para piezas nuevas: correr el fetch_*.py correspondiente primero, "
            "o usar web_research.py para investigación libre.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
