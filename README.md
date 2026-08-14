# colonial-museum-routes

Mapa interactivo que conecta obras de museos con su lugar de origen, para visualizar patrones de expropiación y colonización en las colecciones. El foco son tres museos "de prestigio" en países que colonizaron: **The Metropolitan Museum of Art** (Nueva York), **Musée du Louvre** (París) y **British Museum** (Londres).

Es un proyecto curado para portfolio personal, no un dataset exhaustivo — no busca representar cada museo completo, sino armar un conjunto manejable y bien documentado por institución (~150-250 piezas por museo, con un subconjunto de piezas "bandera" investigadas a fondo).

## Cómo funciona

Cada pieza tiene una línea que conecta el museo con su lugar de origen inferido. Al hacer click en un punto de origen se abre un panel con las piezas de ese lugar; al entrar a una pieza se ve su timeline documentado (creación, excavación, transferencias, adquisición) cuando existe investigación cargada.

El modelo de datos separa explícitamente tres cosas: lo que dice el museo (metadata original), lo que interpretamos nosotros geográficamente (origen inferido), y lo que investigamos nosotros históricamente (timeline de eventos, citado). Ver `CLAUDE.md` para el detalle completo de arquitectura y metodología por museo.

## Uso — pipeline de datos

```bash
pip install -r requirements.txt

python src/fetch_met.py --department 10
python src/fetch_louvre.py --per-department 60
python src/fetch_bm.py

python src/build_dataset.py && python src/build_dataset_louvre.py && python src/build_dataset_bm.py
python src/build_geography.py && python src/build_geography_louvre.py && python src/build_geography_bm.py

python src/export_web_data.py   # junta todo -> web/src/data/objects.json
```

## Uso — app web

Vite + React + TypeScript + Mapbox GL (globo 3D). Requiere `web/.env` con `VITE_MAPBOX_TOKEN` y haber corrido `export_web_data.py` al menos una vez.

```bash
cd web
npm install
npm run dev      # servidor local con hot reload
npm run build    # build de producción en web/dist
```

## Estado

- [x] The Met: pipeline completo, 161 piezas geocodificadas (6 departamentos prioritarios)
- [x] Louvre: pipeline completo, piloto de 80 piezas (71 geocodificadas) vía puente Wikidata
- [x] British Museum: scraper propio, piloto de 9 piezas curadas a mano
- [x] Modelo de 3 capas (metadata / geografía / investigación histórica)
- [x] App web con globo interactivo (Mapbox GL), panel lateral con timeline por pieza
- [x] Piloto de investigación profunda: 5 piezas egipcias del Met con fuentes citadas
- [ ] Ampliar Louvre y BM a ~150-250 piezas por museo
- [ ] Modal de información/instrucciones para el visitante
- [ ] Cruce con Wikidata para piezas en disputa / con historial de expropiación documentado

## Proyectos relacionados

Referencia, no fuente de datos: [heritage-vault](https://github.com/mente123/heritage-vault) mapea objetos africanos del British Museum agrupados por país. El diferencial de este proyecto es la ruta por pieza individual y el modelo de 3 capas con investigación citada.

---

Documentación técnica más profunda (metodología de descubrimiento por museo, decisiones de scraping, arquitectura interna) en `CLAUDE.md`.
