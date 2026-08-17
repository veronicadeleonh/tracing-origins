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
- [x] Louvre: pipeline completo, 239 piezas (215 geocodificadas) vía puente Wikidata — dentro de la meta ~150-250
- [x] British Museum: scraper propio, 50 piezas curadas a mano en distintas regiones del mundo
- [x] Modelo de 3 capas (metadata / geografía / investigación histórica)
- [x] App web con globo interactivo (Mapbox GL), panel lateral con timeline por pieza
- [x] Toggles por museo con contador de piezas visibles
- [x] Capa de contexto: territorios coloniales de UK/Francia, timeline interactivo 1700-2020 (Cliopatria, CC-BY 4.0), opcional vía toggle con leyenda
- [x] Capa de contexto: rutas navales UK/Francia 1700-1900 (CLIWOC/PANGAEA, CC-BY 3.0, 50 rutas curadas), conectada al mismo timeline que los territorios coloniales, toggle independiente ("Imperios"/"Rutas navales")
- [x] Hitos puntuales en el timeline (círculo + tooltip on hover) — 3 eventos institucionales del Met (1870 fundación, 1876 Colección Cesnola, 1906 arranca la Expedición Egipcia propia), extensible a BM/Louvre
- [x] Piloto de investigación profunda: 5 piezas egipcias del Met con fuentes citadas
- [x] Investigación profunda (layer 3) en el Louvre: 8 piezas con timeline citado (mecanismos documentados: partage bajo Mandato Francés y bajo autorización otomana, venta Borghese-Napoleón, excavación privada, mercado de arte) — meta 5-10 por museo cumplida
- [x] Investigación profunda (layer 3) en el British Museum: 8 piezas con timeline citado (Roseta bajo Tratado de Alejandría 1801, Placas de Benín tras la Expedición Punitiva de 1897, excavaciones en Mesopotamia otomana financiadas por el museo, pieza de Amaravati vía India Museum, y casos de contraste sin mecanismo colonial documentado) — meta 5-10 por museo cumplida
- [ ] Ampliar BM a ~150-250 piezas (hoy: Met 161, Louvre 215, BM 50 — 426 de ~500-700)
- [x] Nota por museo en la UI (botón "i" junto a cada toggle) explicando la lógica de extracción particular de cada uno
- [x] Nota por capa de contexto en la UI (botón "i" en "Imperios"/"Rutas navales" del timeline) — explica qué muestra y qué no cada capa
- [ ] Modal de información/instrucciones del proyecto (nivel 1 de "notas de contexto en la UI", ver `CLAUDE.md`) — todavía no implementado
- [ ] Cruce con Wikidata para piezas en disputa / con historial de expropiación documentado
- [ ] Decidir tratamiento narrativo una vez haya más `context_flags` cargadas (¿resaltar piezas en el mapa? ¿filtro por tipo de evento?)
- [ ] Revisar rotulado de fronteras políticas del basemap de Mapbox en zonas disputadas (Cisjordania, Kurdistán, Sahara Occidental)
- [ ] Evaluar Musée du Quai Branly como 4ta fuente — el Louvre no tiene departamento de África Subsahariana/América (fondo transferido a Quai Branly en 2006), así que no puede cubrir el ángulo Francia↔África/Caribe
- [ ] Toggle de idioma (inglés) en la UI — hoy la app está solo en español, no arrancado todavía
- [ ] Test suite / linter (no configurado todavía)

Nota: la investigación profunda (layer 3) queda como una línea de trabajo abierta e indefinida para los 3 museos, no una tarea que se cierra al llegar a 5-10 piezas por museo — Met, Louvre y BM ya cumplieron la meta mínima pero pueden seguir sumando piezas bandera en cualquier momento.

## Proyectos relacionados

Referencia, no fuente de datos: [heritage-vault](https://github.com/mente123/heritage-vault) mapea objetos africanos del British Museum agrupados por país. El diferencial de este proyecto es la ruta por pieza individual y el modelo de 3 capas con investigación citada.

---

Documentación técnica más profunda (metodología de descubrimiento por museo, decisiones de scraping, arquitectura interna) en `CLAUDE.md`.
