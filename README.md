# colonial-museum-routes

Mapa que conecta obras de museos con su lugar de origen, para visualizar patrones de expropiación y colonización en las colecciones.

## Fase 1 — datos (The Met)

Empezamos con el Metropolitan Museum of Art (Open Access API, CC0, sin API key). En fases siguientes se suma Wikidata como puente para cruzar otros museos (ej. British Museum, que no tiene API pública confiable).

Departamentos priorizados por relevancia colonial/arqueológica:

| ID | Departamento |
|----|--------------|
| 3  | Ancient West Asian Art |
| 5  | Arts of Africa, Oceania, and the Americas |
| 6  | Asian Art |
| 10 | Egyptian Art |
| 13 | Greek and Roman Art |
| 14 | Islamic Art |

## Modelo de datos — 3 capas

El modelo separa explícitamente tres cosas que no se deben mezclar: lo que dice
el museo, lo que interpretamos nosotros geográficamente, y lo que investigamos
nosotros históricamente. Cada capa vive en su propio archivo y se junta recién
al armar el mapa — ningún script pisa o modifica campos de otra capa.

```
src/
 ├── fetch_met.py        descarga objetos de la API del Met
 ├── geocode.py          tabla de coordenadas + resolución de origen
 ├── build_dataset.py    layer 1 → met_objects.csv
 ├── build_geography.py  layer 2 → geography.csv
 └── make_map.py         junta las 3 capas y genera el mapa

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

Ambos archivos están vacíos (solo headers) — recién arranca el trabajo de
investigación. `make_map.py` los lee de forma opcional: si una pieza no tiene
fila en ninguno de los dos, la ficha se ve igual que siempre, solo con datos
del Met.

## Uso — pipeline completo

```bash
pip install -r requirements.txt
python src/fetch_met.py --department 10    # baja objetos y mergea en data/raw/met_objects_raw.json
python src/build_dataset.py                 # layer 1 -> data/processed/met_objects.csv
python src/build_geography.py               # layer 2 -> data/processed/geography.csv
python src/make_map.py                      # junta las 3 capas -> maps/map_pilot.html
```

## Estado

- [x] Estructura del repo
- [x] Script de descarga de la API del Met
- [x] Muestreo de calidad de campos geográficos
- [x] Geocodificación (tabla propia de coordenadas, sin Nominatim en bulk)
- [x] Mapa piloto (168 objetos de los 6 departamentos prioritarios completos: Egyptian Art, Arts of Africa/Oceania/Americas, Ancient West Asian Art, Asian Art, Islamic Art, Greek and Roman Art — 161 geocodificados, `maps/map_pilot.html`)
- [x] Reorganización del modelo de datos: raw congelado en `met_objects_raw.json`
- [x] Modelo de 3 capas: `met_objects.csv` (Met) / `geography.csv` (nuestra geocodificación) / `context.csv` + `provenance_events.csv` (nuestra investigación histórica, sin clasificar piezas como robadas/no robadas — documenta el recorrido, no un veredicto)
- [ ] Poblar `provenance_events.csv` / `context.csv` con investigación real (hoy están vacíos, solo headers)
- [ ] Bajar los departamentos completos (no solo la muestra piloto) y ampliar la tabla de coordenadas a medida que aparecen nuevos países/regiones
- [ ] Cruce con Wikidata para piezas en disputa / con historial de expropiación

### Nota sobre Asian Art y Greek and Roman Art

Estos dos departamentos casi nunca completan `country`/`region`/`subregion` — el único dato geográfico confiable es el campo `culture` (texto libre: "China", "India (Tamil Nadu)", "Cypriot", "Greek, Attic", "Roman, Cypriot"). `geocode.py` tiene un fallback (`resolve_from_culture`) que busca nombres de país/región conocidos dentro de ese texto, con el más específico primero (ej. "Cypriot" antes que "Roman", para que una pieza "Roman, Cypriot" resuelva a Chipre y no a Italia). Es menos preciso que el resto (nivel país o región amplia, no sitio) y hay que revisarlo si aparecen culturas ambiguas nuevas.

## Pendiente de decidir (no bloquea el trabajo de datos)

- **Enfoque narrativo**: el modelo de datos ya soporta contexto histórico por pieza (`context.csv` + `provenance_events.csv`, 14/07), pero falta decidir cómo se ve en el mapa una vez que haya investigación real cargada — ¿resaltar visualmente los puntos con `context_flags` pobladas? ¿un filtro por tipo de evento? Se decide cuando haya datos para probarlo.
- **Basemap y fronteras políticas**: el tile actual (CartoDB Positron) trae sus propias convenciones de rotulado de países/fronteras (ej. muestra "Israel" sin "Palestina"). Evaluar basemaps más neutros u ocultar el rotulado de países cuando retomemos el enfoque narrativo — es relevante porque el proyecto trata justamente de visibilizar colonización, y las fronteras políticas modernas no son neutras para muchas de las regiones que vamos a mapear (Cisjordania, Kurdistán, Sahara Occidental, etc.).
