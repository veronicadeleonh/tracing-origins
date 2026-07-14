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

## Estado

- [x] Estructura del repo
- [x] Script de descarga de la API del Met
- [ ] Muestreo de calidad de campos geográficos
- [ ] Geocodificación (tabla propia de coordenadas, sin Nominatim en bulk)
- [ ] Cruce con Wikidata para piezas en disputa
- [ ] Mapa interactivo (Leaflet)
