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
- [x] Mapa piloto (41 objetos de Egyptian Art, 40 geocodificados, `maps/map_pilot.html`)
- [ ] Bajar el departamento completo de Egyptian Art (27.968 objetos) y ampliar la tabla de coordenadas
- [ ] Cruce con Wikidata para piezas en disputa / con historial de expropiación
- [ ] Sumar otros departamentos (Arts of Africa/Oceania/Americas, Ancient West Asian Art)
