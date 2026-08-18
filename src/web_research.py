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
    público). Dos formas de setearla:
      1. `export TAVILY_API_KEY=tvly-...` antes de correr el script, o
      2. un archivo `.env` en la raíz del repo (gitignored, mismo patrón que
         `web/.env` para el token de Mapbox) con una línea
         `TAVILY_API_KEY=tvly-...` -- este script lo lee solo, sin
         dependencias nuevas (parser manual de `KEY=VALUE`, ver
         `_load_dotenv()`). El `.env` NUNCA se commitea.
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

Cómo reducir ruido (18/08, después de una prueba real con la estatua de
Gudea que trajo 2 de 3 resultados irrelevantes -- la misma página del Louvre
que ya teníamos vía research_lookup.py, y un libro de una biblioteca de
Boston de 1859 sin relación):
  1. **Excluí los dominios de los 3 museos** -- ya los cubre
     research_lookup.py sin gastar red, así que aparecer de nuevo acá es
     puro ruido. Excluidos por default (`DEFAULT_EXCLUDE_DOMAINS`); pasá
     `--exclude-domains ""` para desactivarlo si por algún motivo querés
     ver también esas páginas.
  2. **Frasealo como pregunta específica, no como lista de keywords.** Una
     query tipo "Gudea statue Emile Sery Louvre 1967 provenance" es
     básicamente una bolsa de palabras -- cualquier página que mencione 2-3
     de esos términos sueltos matchea, aunque no tenga nada que ver. Mejor:
     "Who was Emile Sery, the collector who owned the Louvre's Gudea statue
     before 1967?" -- una pregunta acotada le da a Tavily/DuckDuckGo una
     intención clara en vez de coincidencias de palabras sueltas.
  3. **Mirá el campo `score` en los resultados de Tavily** (0-1, relevancia
     según su propio ranking) -- con `--min-score 0.3` (default) se
     descartan automáticamente los que Tavily mismo considera poco
     relevantes, antes de que lleguen a la salida.
  4. Si una pieza genuinamente no tiene nada más documentado en la web
     (como pasó con la estatua de Gudea), CERO resultados relevantes es una
     respuesta válida -- no hace falta forzar la búsqueda ni bajar el
     `--min-score` para completar el hueco con algo.

Uso:
    python src/web_research.py "Who was Emile Sery, collector of the Louvre's Gudea statue before 1967?"
    python src/web_research.py "Tiara of Saitaphernes Rouchomovsky forgery" --n 8
    python src/web_research.py "British Museum Yemen looted heritage Sabaean altar" --backend ddgs
    python src/web_research.py "..." --exclude-domains "" --min-score 0
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
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# Los 3 museos ya están cubiertos por research_lookup.py (local, sin red) --
# que vuelvan a aparecer acá es ruido, no información nueva. Excluidos por
# default; --exclude-domains "" los reincluye si hace falta.
DEFAULT_EXCLUDE_DOMAINS = ["collections.louvre.fr", "britishmuseum.org", "metmuseum.org"]


def _load_dotenv() -> None:
    """
    Parser manual de `.env` (KEY=VALUE por línea, `#` para comentarios) --
    no agrega python-dotenv como dependencia nueva por algo tan chico. Solo
    completa variables que no estén YA seteadas en el entorno, para que
    `export TAVILY_API_KEY=...` en la shell siga ganando sobre el archivo si
    ambos están presentes.
    """
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _cache_path(query: str, backend: str, exclude_domains: list[str]) -> Path:
    slug = "".join(c if c.isalnum() else "_" for c in query.lower())[:60]
    cache_key = f"{backend}:{','.join(exclude_domains)}:{query}"
    digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()[:8]
    return CACHE_DIR / f"{slug}_{digest}.json"


def _search_tavily(query: str, n: int, exclude_domains: list[str]) -> list[dict]:
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
    response = client.search(
        query,
        max_results=n,
        search_depth="advanced",
        exclude_domains=exclude_domains or None,
    )
    return [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": (r.get("content") or "")[:800],
            "score": r.get("score"),
        }
        for r in response.get("results", [])
    ]


def _search_ddgs(query: str, n: int, exclude_domains: list[str]) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        print("Falta la librería ddgs -- correr: pip install ddgs", file=sys.stderr)
        sys.exit(1)

    # ddgs no tiene un parámetro dedicado de exclusión de dominio -- usa el
    # operador -site: de DuckDuckGo directo en el texto de la query.
    full_query = query + "".join(f" -site:{d}" for d in exclude_domains)
    raw_results = DDGS().text(full_query, max_results=n)
    return [
        {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body"), "score": None}
        for r in raw_results
    ]


def search(
    query: str,
    n: int = 5,
    use_cache: bool = True,
    backend: str = "auto",
    exclude_domains: list[str] | None = None,
    min_score: float = 0.3,
) -> list[dict]:
    if backend == "auto":
        backend = "tavily" if os.environ.get("TAVILY_API_KEY") else "ddgs"
    exclude_domains = DEFAULT_EXCLUDE_DOMAINS if exclude_domains is None else exclude_domains

    cache_path = _cache_path(query, backend, exclude_domains)
    if use_cache and cache_path.exists():
        cached = json.loads(cache_path.read_text())
        print(f"(cacheado, backend={backend}: {cache_path.relative_to(cache_path.parent.parent.parent)})", file=sys.stderr)
        results = cached["results"]
    else:
        results = (
            _search_tavily(query, n, exclude_domains)
            if backend == "tavily"
            else _search_ddgs(query, n, exclude_domains)
        )
        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps({"query": query, "backend": backend, "results": results}, indent=2, ensure_ascii=False)
            )

    # Filtro de score: solo aplica a resultados con score real (Tavily) --
    # ddgs no da score, así que sus resultados siempre pasan sin filtrar.
    filtered = [r for r in results if r.get("score") is None or r["score"] >= min_score]
    dropped = len(results) - len(filtered)
    if dropped:
        print(f"({dropped} resultado(s) descartados por score < {min_score})", file=sys.stderr)
    return filtered


def main() -> None:
    _load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="Query de búsqueda")
    parser.add_argument("--n", type=int, default=5, help="Cantidad de resultados (default 5)")
    parser.add_argument(
        "--backend",
        choices=["auto", "tavily", "ddgs"],
        default="auto",
        help="auto = tavily si hay TAVILY_API_KEY en el entorno, si no ddgs (default: auto)",
    )
    parser.add_argument(
        "--exclude-domains",
        default=",".join(DEFAULT_EXCLUDE_DOMAINS),
        help=(
            "Dominios a excluir, separados por coma (default: los 3 museos, "
            "ya cubiertos por research_lookup.py). Pasar '' para no excluir nada."
        ),
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.3,
        help="Descarta resultados de Tavily con score menor a esto (default 0.3; no aplica a ddgs)",
    )
    parser.add_argument("--no-cache", action="store_true", help="Ignorar y no escribir caché")
    args = parser.parse_args()

    exclude_domains = [d.strip() for d in args.exclude_domains.split(",") if d.strip()]
    results = search(
        args.query,
        n=args.n,
        use_cache=not args.no_cache,
        backend=args.backend,
        exclude_domains=exclude_domains,
        min_score=args.min_score,
    )

    for i, r in enumerate(results, 1):
        score_note = f" (score {r['score']:.2f})" if r.get("score") is not None else ""
        print(f"{i}. {r['title']}{score_note}")
        print(f"   {r['url']}")
        if r["snippet"]:
            print(f"   {r['snippet'][:300]}")
        print()


if __name__ == "__main__":
    main()
