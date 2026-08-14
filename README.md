# colonial-museum-routes

Mapa que conecta obras de museos con su lugar de origen, para visualizar patrones de expropiación y colonización en las colecciones. El foco son tres museos "de prestigio" en países que colonizaron: The Metropolitan Museum of Art (Nueva York), Musée du Louvre (París) y British Museum (Londres). Es un proyecto curado, no exhaustivo — no busca representar cada museo completo, sino armar un conjunto manejable y bien documentado por institución (ver "Escala" en Estado).

## Fase 1 — datos (The Met)

Empezamos con el Metropolitan Museum of Art (Open Access API, CC0, sin API key). El British Museum no tiene API pública activa, pero sí es raspable (confirmado por un proyecto de terceros, ver abajo) — va a necesitar un scraper propio, no un cliente de API limpio como el Met o el Louvre.

## Fase 2 — datos (Louvre)

El Louvre sí tiene una API JSON real por objeto: agregando `.json` a la URL de cualquier ficha (`collections.louvre.fr/en/ark:/53355/<arkId>.json`) se obtiene el registro completo, con campos que ya modelan buena parte de lo que armamos a mano para el Met (`placeOfCreation`, `placeOfDiscovery`, `previousOwner`, `acquisitionDetails.mode` — cuyo propio ejemplo en la documentación es `"partage après fouilles"`). Documentación completa: `collections.louvre.fr/en/page/documentationJSON`.

Lo que **no** existe es una forma automatizada de listar "todos los objetos del departamento X": el `robots.txt` del sitio bloquea explícitamente `/search/export` (el endpoint de descarga masiva) para todos los user-agents, y la búsqueda interactiva (`/en/recherche-avancee`) está detrás de un CAPTCHA. Ninguna de las dos es una vía que debamos o podamos usar.

La solución: Wikidata tiene una propiedad dedicada, **P9394 ("Louvre Museum ARK ID")**, con ~480k registros (casi 1:1 con la colección completa). Cruzando `P9394` con `P195` (colección = departamento curatorial del Louvre como entidad Wikidata) se consiguen listas de `arkId` por departamento vía SPARQL público — sin tocar el endpoint bloqueado ni la búsqueda con CAPTCHA. Ver `src/fetch_louvre.py`.

Los IDs se piden ordenados por `wikibase:sitelinks` descendente (más artículos de Wikipedia enlazados primero), lo que de paso prioriza piezas conocidas/documentadas — calza bien con la idea de "piezas bandera" del proyecto. El piloto (20 piezas por departamento, 80 en total, en `data/raw/louvre_objects_raw.json`) trajo así la Vénus de Milo, la Victoire de Samothrace, Le Scribe accroupi, el Code de Hammurabi... piezas de alto perfil, varias con historias de adquisición documentadas (partage, saisie révolutionnaire, saisie napoléonienne, achat directo).

Geocodificación del Louvre: texto libre en francés (`placeOfDiscovery` > `placeOfCreation` > `provenance`, en ese orden de prioridad), sin country/region/subregion estructurado como en el Met. Ver `resolve_origin_louvre()` en `geocode.py` — 89% de resolución en el piloto (71/80).

Departamentos priorizados por relevancia colonial/arqueológica:

| ID | Departamento |
|----|--------------|
| 3  | Ancient West Asian Art |
| 5  | Arts of Africa, Oceania, and the Americas |
| 6  | Asian Art |
| 10 | Egyptian Art |
| 13 | Greek and Roman Art |
| 14 | Islamic Art |

## Multi-museo: namespacing de IDs

`objectID` ya no es el id crudo del museo — es `"<museo>:<id-nativo>"` (`met:96404`, y en el futuro `louvre:cl010277627`, `bm:...`), porque el id crudo no es único entre museos. Ver `src/museum_id.py`. `met_objects.csv` guarda además `sourceMuseum` y `sourceObjectID` (el id nativo, sin prefijo) para no perder trazabilidad hacia `met_objects_raw.json`. `data/raw/*.json` no se toca — el namespacing se aplica recién al construir layer 1, nunca en el snapshot crudo. `geography.csv` pasó de `met_lat`/`met_lon` a `museum_lat`/`museum_lon` por el mismo motivo: ya no es Met-específico.

## Modelo de datos — 3 capas

El modelo separa explícitamente tres cosas que no se deben mezclar: lo que dice
el museo, lo que interpretamos nosotros geográficamente, y lo que investigamos
nosotros históricamente. Cada capa vive en su propio archivo y se junta recién
al armar el mapa — ningún script pisa o modifica campos de otra capa.

```
src/
 ├── fetch_met.py         descarga objetos de la API del Met
 ├── geocode.py           tabla de coordenadas + resolución de origen
 ├── build_dataset.py     layer 1 → met_objects.csv
 ├── build_geography.py   layer 2 → geography.csv
 ├── make_map.py          junta las 3 capas, genera el mapa estático (Folium)
 └── export_web_data.py   junta las 3 capas, genera web/src/data/objects.json

web/                      app en React + Leaflet (panel lateral, timeline por
                          pieza) — reemplaza de a poco a make_map.py como
                          experiencia principal; ver web/README más abajo

data/
 ├── raw/
 │    └── met_objects_raw.json     snapshot crudo congelado (versionado en git)
 │
 ├── processed/
 │    ├── met_objects.csv          layer 1: metadata del Met, sin tocar
 │    └── geography.csv            layer 2: nuestra interpretación geográfica
 │
 └── enrichment/
      ├── context.csv              layer 3: estado de investigación + tags por pieza
      └── provenance_events.csv    layer 3: timeline de eventos históricos por pieza
```

**Layer 1 — `met_objects.csv`** (`build_dataset.py`): campos tal cual los da la
API del Met (título, cultura, medio, creditLine, country/region/subregion en
texto, etc.). Nunca se calcula ni se interpreta nada acá.

**Layer 2 — `geography.csv`** (`build_geography.py`): el punto de origen que
inferimos nosotros vía `geocode.py` (subregion > region > country > culture >
sin resolver), separado en su propio archivo porque es una inferencia
nuestra, no un dato provisto por el museo.

**Layer 3 — investigación histórica** (`data/enrichment/`, poblado a mano, sin
script de descarga): documenta el recorrido de la pieza sin clasificarla como
"robada" o "no robada" — el objetivo es visibilizar los distintos mecanismos
por los que las piezas entraron a la colección, no emitir un veredicto.

- `provenance_events.csv`: 0+ filas por objeto, una por evento (creación,
  excavación, venta, transferencia bajo administración colonial, adquisición
  por el museo, reclamo de restitución, etc.). Columnas: `objectID`,
  `event_order`, `event_type`, `event_date`, `actor_or_institution`,
  `location`, `description`, `source_url`, `source_type`, `confidence_level`,
  `researcher`, `last_reviewed_date`.

  `event_type` (vocabulario controlado, descriptivo, no acusatorio):
  `creation`, `excavation_licensed`, `excavation_undocumented`,
  `colonial_administration_transfer`, `military_conflict_removal`,
  `missionary_collection`, `private_sale`, `art_market_transaction`, `gift`,
  `bequest`, `institutional_exchange`, `museum_acquisition`,
  `restitution_request`, `restitution_completed`, `exhibition_loan`,
  `unknown_transfer`, `other`.

- `context.csv`: 1 fila por objeto, estado del trabajo de investigación, no
  hechos históricos. Columnas: `objectID`, `research_status` (`not_started` /
  `in_progress` / `documented` / `needs_review`), `context_flags` (tags
  separados por `;`, ej. `colonial_administration;expedition`),
  `associated_communities_or_states`, `notes`.

`make_map.py`/`export_web_data.py` los leen de forma opcional: si una pieza
no tiene fila en ninguno de los dos, la ficha se ve igual que siempre, solo
con datos del Met — ese es el estado por defecto para la gran mayoría de las
piezas, no una excepción. Hay 5 piezas piloto ya investigadas a fondo
(excavaciones egipcias con partage documentado, ver commit correspondiente)
para probar que el timeline con eventos reales funciona de punta a punta.

## Uso — pipeline de datos

```bash
pip install -r requirements.txt
python src/fetch_met.py --department 10    # baja objetos y mergea en data/raw/met_objects_raw.json
python src/build_dataset.py                 # layer 1 -> data/processed/met_objects.csv
python src/build_geography.py               # layer 2 -> data/processed/geography.csv
python src/make_map.py                      # mapa estático (Folium) -> maps/map_pilot.html
python src/export_web_data.py               # junta las 3 capas -> web/src/data/objects.json
```

## Uso — app web (React + Leaflet)

Mapa interactivo con panel lateral (en construcción). Requiere haber corrido
`export_web_data.py` al menos una vez para tener `web/src/data/objects.json`.

```bash
cd web
npm install
npm run dev      # servidor local con hot reload
npm run build    # build de producción en web/dist
```

`objects.json` no se regenera solo — cada vez que cambie algo en `data/processed/`
o `data/enrichment/`, hay que correr `python src/export_web_data.py` de nuevo
desde la raíz del repo antes de ver los cambios en la app.

## Estado

- [x] Estructura del repo
- [x] Script de descarga de la API del Met
- [x] Muestreo de calidad de campos geográficos
- [x] Geocodificación (tabla propia de coordenadas, sin Nominatim en bulk)
- [x] Mapa piloto (168 objetos de los 6 departamentos prioritarios completos: Egyptian Art, Arts of Africa/Oceania/Americas, Ancient West Asian Art, Asian Art, Islamic Art, Greek and Roman Art — 161 geocodificados, `maps/map_pilot.html`)
- [x] Reorganización del modelo de datos: raw congelado en `met_objects_raw.json`
- [x] Modelo de 3 capas: `met_objects.csv` (Met) / `geography.csv` (nuestra geocodificación) / `context.csv` + `provenance_events.csv` (nuestra investigación histórica, sin clasificar piezas como robadas/no robadas — documenta el recorrido, no un veredicto)
- [x] Piloto de investigación profunda: 5 piezas egipcias (partage / compra directa al gobierno egipcio, con fuentes citadas del propio Met + contexto institucional)
- [ ] Bajar los departamentos completos del Met (no solo la muestra piloto) — de momento no es prioridad, ver "Escala" abajo
- [x] Scaffold de la app en React (`web/`): Vite + React + react-leaflet, mapa base con los 161 puntos y una línea por pieza (jitter determinístico portado de `make_map.py`, ver `web/src/geo.ts`).
- [x] Panel lateral: estado cluster (lista de piezas) ↔ estado detalle (timeline de la pieza), con flecha de "volver" (`web/src/components/ClusterPanel.tsx`, `ObjectDetail.tsx`)
- [x] Estado de "sin investigar" (2 nodos: origen → ahora) en el panel de detalle
- [x] Namespacing de objectID por museo (`met:`, listo para sumar `louvre:`/`bm:`)
- [ ] Landing / framing antes del mapa
- [x] Pipeline del Louvre: descubrimiento de arkIds vía Wikidata (P9394 + P195, ver "Fase 2" arriba) + fetch por objeto + layer 1/2 propios (`fetch_louvre.py`, `build_dataset_louvre.py`, `build_geography_louvre.py`) — piloto de 80 piezas (20 por departamento prioritario), 71 geocodificadas
- [ ] Ampliar el piloto del Louvre de 80 a ~150-250 piezas
- [ ] Scraper del British Museum
- [ ] Cruce con Wikidata para piezas en disputa / con historial de expropiación

### Escala (definido 14/08)

Proyecto curado para portfolio personal, no un dataset exhaustivo. Objetivo:
~150-250 piezas por museo (~500-700 en total, mismo orden de magnitud que el
Met ahora), con una capa básica pareja para todas (el dato que cada museo ya
publica) y un subconjunto chico y deliberado de piezas "bandera"
(15-30 en total, 5-10 por museo) con investigación profunda tipo la del
piloto egipcio. No se persigue bajar departamentos completos ni el 100% de
cada colección.

### Proyectos relacionados (referencia, no fuente de datos)

Al buscar cómo otros abordaron esto: [heritage-vault](https://github.com/mente123/heritage-vault) mapea objetos africanos del British Museum agrupados por país (sin líneas de ruta, más simple que lo nuestro), y confirma que el sitio del BM es raspable sin API formal. Ese proyecto está a su vez inspirado en uno de un estudiante de MIT construyendo un mapa de patrimonio a escala global (no localizado, no verificado en detalle). No competimos en cobertura — el diferencial de este proyecto es la ruta por pieza individual y el modelo de 3 capas con investigación citada.

### Nota sobre Asian Art y Greek and Roman Art

Estos dos departamentos casi nunca completan `country`/`region`/`subregion` — el único dato geográfico confiable es el campo `culture` (texto libre: "China", "India (Tamil Nadu)", "Cypriot", "Greek, Attic", "Roman, Cypriot"). `geocode.py` tiene un fallback (`resolve_from_culture`) que busca nombres de país/región conocidos dentro de ese texto, con el más específico primero (ej. "Cypriot" antes que "Roman", para que una pieza "Roman, Cypriot" resuelva a Chipre y no a Italia). Es menos preciso que el resto (nivel país o región amplia, no sitio) y hay que revisarlo si aparecen culturas ambiguas nuevas.

## Pendiente de decidir (no bloquea el trabajo de datos)

- **Enfoque narrativo**: el modelo de datos ya soporta contexto histórico por pieza (`context.csv` + `provenance_events.csv`, 14/07), pero falta decidir cómo se ve en el mapa una vez que haya investigación real cargada — ¿resaltar visualmente los puntos con `context_flags` pobladas? ¿un filtro por tipo de evento? Se decide cuando haya datos para probarlo.
- **Basemap y fronteras políticas**: el tile actual (CartoDB Positron) trae sus propias convenciones de rotulado de países/fronteras (ej. muestra "Israel" sin "Palestina"). Evaluar basemaps más neutros u ocultar el rotulado de países cuando retomemos el enfoque narrativo — es relevante porque el proyecto trata justamente de visibilizar colonización, y las fronteras políticas modernas no son neutras para muchas de las regiones que vamos a mapear (Cisjordania, Kurdistán, Sahara Occidental, etc.).
