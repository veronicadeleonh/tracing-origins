"""
Búsqueda libre en la web (Wikipedia, prensa, catálogos de subastas, etc.)
para investigación de layer 3, en vez de que Claude fetchee páginas completas
en vivo durante la sesión.

Dos backends:
  - **tavily** (preferido si hay API key): pensado para agentes/LLMs, devuelve
    contenido ya extraído de cada página (no solo un snippet), más confiable
    que scrapear un buscador. Requiere cuenta en tavily.com y `pip install
    tavily-python`. Se activa poniendo la key en la variable de entorno
    TAVILY_API_KEY -- NUNCA hardcodeada acá ni commiteada (este repo es
    público). Ej.: `export TAVILY_API_KEY=tvly-...` antes de correr el
    script, o anteponerlo al comando.
  - **ddgs** (fallback sin key): DuckDuckGo vía la librería `ddgs`, gratis,
    sin registro, resultados más pobres (solo snippet corto). Se usa
    automáticamente si no hay TAVILY_API_KEY en el entorno, o forzando
    `--backend ddgs`.

IMPORTANTE — correr esto en tu máquina, no desde el sandbox de Cowork: la
red del sandbox está restringida (mismo motivo que fetch_louvre.py y
fetch_bm.py, ver CLAUDE.md) y ni DuckDuckGo/Startpage ni (probablemente)
Tavily son alcanzables desde ahí. Confirmado el 18/08 para ddgs: se instala
bien en el sandbox pero la búsqueda falla con ConnectError.

Cachea cada resultado en research_cache/web/ (gitignored, ver .gitignore)
con un nombre de archivo basado en la query, para que:
  1. no se vuelva a pegarle a la red (ni gastar cuota de Tavily) por la misma
     pregunta en una sesión futura, y
  2. Claude pueda leer el JSON chico ya cacheado en vez de fetchear páginas
     completas para decidir cuáles valen la pena.

Este script NO reemplaza a research_lookup.py -- ese lee lo que ya bajaron
fetch_met.py/fetch_louvre.py/fetch_bm.py (sin red, siempre primero, y
gratis). Este es para cuando el registro del museo no alcanza y hace falta
ir a buscar afuera (ej. una nota de prensa sobre una subasta, un artículo de
Wikipedia sobre una colección privada).

Requiere: pip install ddgs tavily-python  (tavily-python solo hace falta si
vas a usar ese backend; el script no rompe si falta y usás --backend ddgs)

Uso:
    python src/web_research.py "Gudea statue Emile Sery collection Louvre 1967"
    python src/web_research.py "Tiara of Saitaphernes Rouchomovsky forgery" --n 8
    python src/web_research.py "British Museum Yemen looted heritage Sabaean" --backend ddgs
    python src/web_research.py "..." --no-cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "research_cache" / "web"


def _cache_path(query: str, backend: str) -> Path:
    slug = "".join(c if c.isalnum() else "_" for c in query.lower())[:60]
    digest = hashlib.sha1(f"{backend}:{query}".encode("utf-8")).hexdigest()[:8]
    return CACHE_DIR / f"{slug}_{digest}.json"


def _search_tavily(query: str, n: int) -> list[dict]:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print(
            "Falta TAVILY_API_KEY en el entorno -- exportala antes de correr "
            "(export TAVILY_API_KEY=tvly-...) o usá --backend ddgs.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        from tavily import TavilyClient
    except ImportError:
        print("Falta la librería tavily-python -- correr: pip install tavily-python", file=sys.stderr)
        sys.exit(1)

    client = TavilyClient(api_key=api_key)
    response = client.search(query, max_results=n, search_depth="advanced")
    return [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": (r.get("content") or "")[:800],
        }
        for r in response.get("results", [])
    ]


def _search_ddgs(query: str, n: int) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        print("Falta la librería ddgs -- correr: pip install ddgs", file=sys.stderr)
        sys.exit(1)

    raw_results = DDGS().text(query, max_results=n)
    return [
        {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
        for r in raw_results
    ]


def search(query: str, n: int = 5, use_cache: bool = True, backend: str = "auto") -> list[dict]:
    if backend == "auto":
        backend = "tavily" if os.environ.get("TAVILY_API_KEY") else "ddgs"

    cache_path = _cache_path(query, backend)
    if use_cache and cache_path.exists():
        cached = json.loads(cache_path.read_text())
        print(f"(cacheado, backend={backend}: {cache_path.relative_to(cache_path.parent.parent.parent)})", file=sys.stderr)
        return cached["results"]

    results = _search_tavily(query, n) if backend == "tavily" else _search_ddgs(query, n)

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"query": query, "backend": backend, "results": results}, indent=2, ensure_ascii=False)
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="Query de búsqueda")
    parser.add_argument("--n", type=int, default=5, help="Cantidad de resultados (default 5)")
    parser.add_argument(
        "--backend",
        choices=["auto", "tavily", "ddgs"],
        default="auto",
        help="auto = tavily si hay TAVILY_API_KEY en el entorno, si no ddgs (default: auto)",
    )
    parser.add_argument("--no-cache", action="store_true", help="Ignorar y no escribir caché")
    args = parser.parse_args()

    results = search(args.query, n=args.n, use_cache=not args.no_cache, backend=args.backend)

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['url']}")
        if r["snippet"]:
            print(f"   {r['snippet'][:300]}")
        print()


if __name__ == "__main__":
    main()
