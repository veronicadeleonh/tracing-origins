# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
pip install -r requirements.txt
cd web && npm install

# Data pipeline — corré en este orden, desde la raíz del repo
python src/fetch_met.py --department 10          # baja/mergea data/raw/met_objects_raw.json (API pública, sin key)
python src/fetch_louvre.py --per-department 60    # baja/mergea data/raw/louvre_objects_raw.json (bridge Wikidata, ver abajo)
python src/fetch_bm.py                             # baja/mergea data/raw/bm_objects_raw.json (scraper, crawl-delay 20s — lento)

python src/build_dataset.py          # layer 1 Met    -> data/processed/met_objects.csv
python src/build_dataset_louvre.py   # layer 1 Louvre -> data/processed/louvre_objects.csv
python src/build_dataset_bm.py       # layer 1 BM     -> data/processed/bm_objects.csv

python src/build_geography.py          # layer 2 Met    -> data/processed/geography.csv
python src/build_geography_louvre.py   # layer 2 Louvre -> data/processed/geography_louvre.csv
python src/build_geography_bm.py       # layer 2 BM     -> data/processed/geography_bm.csv

python src/export_web_data.py        # junta layer 1+2+3 de TODOS los museos -> web/src/data/objects.json
python src/make_map.py               # opcional: mapa estático Folium -> maps/map_pilot.html (fallback, no es la experiencia principal)

# App web (la experiencia principal)
cd web
npm run dev      # servidor local con hot reload — requiere objects.json ya generado
npm run build    # tsc -b && vite build -> web/dist
```

No hay test suite ni linter configurado todavía. `export_web_data.py` no se corre solo — cada vez que cambia algo en `data/processed/` o `data/enrichment/` hay que volver a correrlo antes de ver el cambio en la app.

## Arquitectura

### Modelo de datos — 3 capas, nunca mezcladas

1. **Layer 1** (`build_dataset*.py` → `data/processed/<museo>_objects.csv`): metadata tal cual la da cada museo. No se calcula ni interpreta nada acá.
2. **Layer 2** (`build_geography*.py` → `data/processed/geography_<museo>.csv`): punto de origen geográfico, inferido por nosotros vía `geocode.py`. Separado de layer 1 a propósito: es una inferencia nuestra, no un dato del museo.
3. **Layer 3** (`data/enrichment/context.csv` + `provenance_events.csv`, poblado a mano, sin script de descarga): investigación histórica del recorrido de la pieza. **No clasifica piezas como "robadas"/"no robadas"** — el objetivo es documentar el recorrido (creación → excavación/hallazgo → transferencias → adquisición del museo → hoy), no emitir un veredicto. `event_type` es un vocabulario controlado no acusatorio (`creation`, `excavation`, `transfer`, `sale`, `gift`, `bequest`, `exchange`, `acquisition`, `loan`, `restitution`, `other`). La gran mayoría de las piezas no tiene fila en layer 3 todavía — es el estado por defecto, no una excepción, y `export_web_data.py`/`make_map.py` lo tratan como opcional.

`export_web_data.py` es el único punto que junta las 3 capas (por `objectID`) y las tira a `web/src/data/objects.json`, que consume la app React. No depende de `folium` a propósito — es solo transporte de datos.

### Multi-museo: un builder por museo, mismo shape de salida

Cada museo tiene su propio `fetch_*.py` / `build_dataset_*.py` / `build_geography_*.py` porque el shape de datos de origen es distinto en cada API/sitio, pero los tres devuelven CSVs con las mismas columnas (`objectID`, `sourceMuseum`, `sourceObjectID`, `title`, etc. en layer 1; `origin_label/precision/lat/lon`, `museum_lat/lon` en layer 2). `export_web_data.py` los itera vía `MUSEUM_SOURCES` (lista de pares objects/geography csv) — agregar un museo nuevo es agregar su par de builders + una entrada en esa lista, sin tocar el resto.

`objectID` está namespaceado como `"<museo>:<id-nativo>"` (`met:96404`, `louvre:cl010277627`, `bm:Y_EA24`) porque el id crudo no es único entre museos — ver `src/museum_id.py`. Esto NUNCA se aplica a `data/raw/*.json` (el snapshot crudo se congela tal cual lo entrega cada fuente); se aplica recién al construir layer 1.

### Geocodificación (`geocode.py`)

Sin llamadas a Nominatim en bulk (prohibido por su política de uso) — es una tabla de coordenadas armada a mano, con un `resolve_origin_*()` por museo porque cada fuente da la geografía en un formato distinto:

- **Met** (`resolve_origin`): `country`/`region`/`subregion` estructurado, con fallback a texto libre de `culture` para los departamentos Asian Art y Greek/Roman Art (casi nunca completan country/region/subregion — ahí el único dato confiable es `culture`, ej. "Roman, Cypriot"; el fallback matchea por keyword, más específico primero, para que eso resuelva a Chipre y no a Italia).
- **Louvre** (`resolve_origin_louvre`): texto libre en francés, prioridad `placeOfDiscovery` > `placeOfCreation` > `provenance`, formato jerárquico "Sitio (Región->País)".
- **BM** (`resolve_origin_bm`): texto libre en inglés con prefijo de etiqueta ("Excavated/Findspot:", "Found/Acquired:", "Made in:"), prioridad `findspot` > `productionPlace`.

Cada build script imprime las etiquetas sin resolver al correr — expandir las listas de keywords (`*_SITE_COORDS`/`*_COUNTRY_KEYWORDS`) cuando se repiten es el mecanismo esperado de mejora incremental, no un bug a corregir de una.

### Descubrimiento de objetos por museo — tres estrategias distintas

- **Met**: API pública con `departmentIds`, sin restricciones — `fetch_met.py --department <id>`.
- **Louvre**: la API JSON por objeto es real (`collections.louvre.fr/en/ark:/53355/cl<id>.json`), pero el sitio **bloquea `/search/export`** en `robots.txt` y la búsqueda interactiva tiene **CAPTCHA** — no hay forma automatizada de listar objetos por departamento desde el sitio mismo. Solución: Wikidata tiene `P9394` ("Louvre Museum ARK ID", ~480k registros) cruzable con `P195` (colección = departamento curatorial, como entidad Wikidata) vía SPARQL público. Se piden ordenados por `wikibase:sitelinks` descendente para priorizar piezas documentadas/conocidas ("piezas bandera"). QIDs de departamento usados: Antigüedades Egipcias `Q3044749`, Antigüedades Orientales `Q3044751`, Antigüedades Griegas/Etruscas/Romanas `Q3044747`, Arte Islámico `Q3044748`.
- **BM**: no tiene API pública, y el puente equivalente por Wikidata (`P8565`, "British Museum object ID") **no funciona bien** — casi ningún objeto tiene el departamento curatorial cargado en `P195`, y varios valores de `P8565` no traen el prefijo de letra que la URL real necesita (tiran 404 tal cual). Se raspa directo `/collection/object/<id>` (permitido por robots.txt, que solo bloquea `/search*`, `/admin/`, etc.), pero el robots.txt pide **`Crawl-delay: 20`** (20 segundos entre requests) — se respeta a rajatabla en `fetch_bm.py`, así que bajar piezas ahí es lento. Sin descubrimiento automatizado confiable, `SEED_OBJECT_IDS` en `fetch_bm.py` es una lista curada a mano, anclada en la página oficial de ["contested objects"](https://www.britishmuseum.org/about-us/british-museum-story/contested-objects-collection) del propio Museo (Benin Bronzes, Asante Gold Regalia, Maqdala, Moai, Parthenon Sculptures) — ampliarla es manual, no hay atajo.

### Hallazgo estructural: el Louvre no tiene departamento de África/América

Los 9 departamentos curatoriales del Louvre son todos Egipto/Medio Oriente/Mediterráneo/Europa (Antigüedades Egipcias, Orientales, Griegas-Etruscas-Romanas, Arte Bizantino, Arte Islámico, Pinturas, Escultura, Artes Decorativas, Artes Gráficas) — **no hay Sub-Saharan Africa ni América**. Ese fondo se transfirió al Musée du Quai Branly cuando abrió en 2006. Por eso las líneas del Louvre en el mapa van a seguir concentradas en Egipto/Medio Oriente casi sin importar cuánto se amplíe el piloto — no es un sesgo de muestreo, es la colección real. Si en algún momento se quiere cubrir el ángulo Francia-África/Caribe específicamente, el museo correcto sería Quai Branly (implicaría sumar una cuarta fuente, fuera del alcance actual de 3 museos).

### App web (`web/`)

Vite + React + TypeScript. Migró de `react-leaflet` a `react-map-gl`/Mapbox GL (globo 3D) — requiere `VITE_MAPBOX_TOKEN` en `web/.env` (gitignored, no versionar). Panel lateral con máquina de estados simple: `null | {view:"cluster", cluster} | {view:"object", cluster, object}` en `App.tsx`, dos componentes (`ClusterPanel.tsx` para la lista de piezas por punto de origen, `ObjectDetail.tsx` para el timeline de una pieza). El mapa queda visible/interactivo detrás del panel siempre (layout flex, no modal). Jitter determinístico (`geo.ts`, `jitteredPoint()`) para separar visualmente piezas que comparten origen exacto, sin tocar las coordenadas reales — puramente de render.

## Filosofía / alcance del proyecto

Proyecto curado para portfolio personal, no un dataset exhaustivo ni un intento de competir en cobertura con proyectos tipo [heritage-vault](https://github.com/mente123/heritage-vault). Objetivo de escala: ~150-250 piezas por museo (~500-700 total), con una capa básica pareja para todas (lo que cada museo ya publica) y un subconjunto chico de piezas "bandera" (15-30 en total, 5-10 por museo) con investigación profunda tipo la de las 5 piezas egipcias del Met (`data/enrichment/`). No se persigue bajar departamentos completos ni el 100% de ninguna colección — la app deja esto explícito con un aviso de "muestra curada" en el mapa.

## Pendiente de decidir

- **Modal de información/instrucciones**: reemplaza la idea original de una landing page — mostrar contexto y alcance del proyecto al visitante sin agregar una pantalla previa al mapa. No implementado todavía.
- **Enfoque narrativo una vez haya más investigación cargada**: ¿resaltar visualmente los puntos con `context_flags` pobladas? ¿filtro por tipo de evento? Se decide cuando haya suficiente data real para probarlo.
- **Basemap y fronteras políticas**: evaluar si el basemap de Mapbox necesita ajustes de rotulado de países — relevante porque el proyecto visibiliza colonización y las fronteras políticas modernas no son neutras para varias regiones mapeadas (Cisjordania, Kurdistán, Sahara Occidental, etc.).

## Notas del entorno de desarrollo (Cowork sandbox)

Si estás operando este repo desde un sandbox con red restringida (allowlist), `requests`/`urllib` hacia `query.wikidata.org`, `collections.louvre.fr` o `britishmuseum.org` van a fallar con 403/timeout aunque el script sea correcto — los `fetch_*.py` están escritos para correr con red normal (ej. en la máquina real del usuario), no necesariamente desde ese sandbox. Para poblar datos de piloto desde un sandbox así, usar el navegador conectado (fetch dentro del contexto de la página) en vez de red directa del proceso.

Si `git commit`/`git status` desde el sandbox muestra diffs fantasma (archivos como simultáneamente borrados y untracked), el índice default de git quedó desincronizado — correr `rm -f .git/index .git/index.lock && git read-tree HEAD` antes de confiar en `git status`.
