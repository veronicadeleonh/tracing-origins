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

## Estructura

```
src/            scripts de descarga y procesamiento
data/raw/       JSON crudo bajado de la API del Met (no versionado)
data/processed/ datasets limpios, listos para geocodificar / mapear
```

## Uso

```bash
pip install -r requirements.txt
python src/fetch_met.py --department 10 --limit 50
```

## Uso — pipeline completo

```bash
pip install -r requirements.txt
python src/fetch_met.py --department 10   # baja objetos a data/raw/
python src/build_dataset.py                # geocodifica -> data/processed/objects.csv
python src/make_map.py                     # genera maps/map_pilot.html
```

## Estado

- [x] Estructura del repo
- [x] Script de descarga de la API del Met
- [x] Muestreo de calidad de campos geográficos
- [x] Geocodificación (tabla propia de coordenadas, sin Nominatim en bulk)
- [x] Mapa piloto (168 objetos de los 6 departamentos prioritarios completos: Egyptian Art, Arts of Africa/Oceania/Americas, Ancient West Asian Art, Asian Art, Islamic Art, Greek and Roman Art — 161 geocodificados, `maps/map_pilot.html`)
- [ ] Bajar los departamentos completos (no solo la muestra piloto) y ampliar la tabla de coordenadas a medida que aparecen nuevos países/regiones
- [ ] Cruce con Wikidata para piezas en disputa / con historial de expropiación

### Nota sobre Asian Art y Greek and Roman Art

Estos dos departamentos casi nunca completan `country`/`region`/`subregion` — el único dato geográfico confiable es el campo `culture` (texto libre: "China", "India (Tamil Nadu)", "Cypriot", "Greek, Attic", "Roman, Cypriot"). `geocode.py` tiene un fallback (`resolve_from_culture`) que busca nombres de país/región conocidos dentro de ese texto, con el más específico primero (ej. "Cypriot" antes que "Roman", para que una pieza "Roman, Cypriot" resuelva a Chipre y no a Italia). Es menos preciso que el resto (nivel país o región amplia, no sitio) y hay que revisarlo si aparecen culturas ambiguas nuevas.

## Pendiente de decidir (no bloquea el trabajo de datos)

- **Enfoque narrativo**: ¿el mapa va a limitarse a mostrar origen→museo, o vamos a sumar contexto histórico por pieza/cluster (bajo qué régimen o circunstancia salió) y/o marcar visualmente las piezas con proveniencia disputada (saqueo documentado, ej. Bronces de Benín)? Charlado el 14/07, decidimos posponerlo.
- **Basemap y fronteras políticas**: el tile actual (CartoDB Positron) trae sus propias convenciones de rotulado de países/fronteras (ej. muestra "Israel" sin "Palestina"). Evaluar basemaps más neutros u ocultar el rotulado de países cuando retomemos el enfoque narrativo — es relevante porque el proyecto trata justamente de visibilizar colonización, y las fronteras políticas modernas no son neutras para muchas de las regiones que vamos a mapear (Cisjordania, Kurdistán, Sahara Occidental, etc.).
