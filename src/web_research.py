"""
Búsqueda libre en la web (Wikipedia, prensa, catálogos de subastas, etc.)
para investigación de layer 3, usando DuckDuckGo vía la librería `ddgs`
(sin API key, sin costo) en vez de que Claude fetchee páginas completas en
vivo durante la sesión.

IMPORTANTE — correr esto en tu máquina, no desde el sandbox de Cowork: la
red del sandbox está restringida (mismo motivo que fetch_louvre.py y
fetch_bm.py, ver CLAUDE.md) y DuckDuckGo/Startpage no son alcanzables desde
ahí. Confirmado el 18/08: `ddgs` se instala bien en el sandbox pero la
búsqueda falla con ConnectError.

Cachea cada resultado en research_cache/web/ (gitignored, ver .gitignore)
con un nombre de archivo basado en la query, para que:
  1. no se vuelva a pegarle a la red por la misma pregunta en una sesión
     futura, y
  2. Claude pueda leer el JSON chico ya cacheado (solo título/url/snippet
     por resultado) en vez de fetchear páginas completas para decidir cuáles
     valen la pena.

Este script NO reemplaza a research_lookup.py -- ese lee lo que ya bajaron
fetch_met.py/fetch_louvre.py/fetch_bm.py (sin red, siempre primero). Este es
para cuando el registro del museo no alcanza y hace falta ir a buscar afuera
(ej. una nota de prensa sobre una subasta, un artículo de Wikipedia sobre una
colección privada).

Requiere: pip install ddgs

Uso:
    python src/web_research.py "Gudea statue Emile Sery collection Louvre 1967"
    python src/web_research.py "Tiara of Saitaphernes Rouchomovsky forgery" --n 8
    python src/web_research.py "British Museum Yemen looted heritage Sabaean" --no-cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "research_cache" / "web"


def _cache_path(query: str) -> Path:
    slug = "".join(c if c.isalnum() else "_" for c in query.lower())[:60]
    digest = hashlib.sha1(query.encode("utf-8")).hexdigest()[:8]
    return CACHE_DIR / f"{slug}_{digest}.json"


def search(query: str, n: int = 5, use_cache: bool = True) -> list[dict]:
    cache_path = _cache_path(query)
    if use_cache and cache_path.exists():
        cached = json.loads(cache_path.read_text())
        print(f"(cacheado: {cache_path.relative_to(cache_path.parent.parent.parent)})", file=sys.stderr)
        return cached["results"]

    try:
        from ddgs import DDGS
    except ImportError:
        print("Falta la librería ddgs -- correr: pip install ddgs", file=sys.stderr)
        sys.exit(1)

    raw_results = DDGS().text(query, max_results=n)
    results = [
        {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
        for r in raw_results
    ]

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"query": query, "results": results}, indent=2, ensure_ascii=False)
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="Query de búsqueda")
    parser.add_argument("--n", type=int, default=5, help="Cantidad de resultados (default 5)")
    parser.add_argument("--no-cache", action="store_true", help="Ignorar y no escribir caché")
    args = parser.parse_args()

    results = search(args.query, n=args.n, use_cache=not args.no_cache)

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['url']}")
        if r["snippet"]:
            print(f"   {r['snippet'][:200]}")
        print()


if __name__ == "__main__":
    main()
