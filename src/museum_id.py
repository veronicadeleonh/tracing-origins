"""
Namespacing de IDs entre museos.

Cada museo tiene su propio espacio de numeración (el objectID 96404 existe
tanto en el Met como, potencialmente, en cualquier otro museo), así que en
cuanto sumamos una segunda fuente el objectID crudo deja de ser una clave
única global. A partir de acá, el objectID que usamos como clave de join en
processed/ y enrichment/ es siempre "<museo>:<id-nativo-del-museo>" — nunca
el id crudo solo.

Esto NO toca data/raw/*.json: los snapshots crudos guardan el id tal cual lo
da cada museo, sin prefijo. El namespacing se aplica recién al construir
layer 1 (build_dataset.py / el equivalente de cada museo).
"""

MET = "met"
LOUVRE = "louvre"
BRITISH_MUSEUM = "bm"


def namespaced_id(museum: str, raw_id) -> str:
    return f"{museum}:{raw_id}"
