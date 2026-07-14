# Calidad de datos geográficos — muestreo real (18 objetos, 3 departamentos)

Muestra tomada directo de la API el 14/07/2026. No es estadísticamente robusta (18 casos) pero alcanza para decidir cómo diseñar el pipeline.

## Arts of Africa, Oceania, and the Americas (dept. 5) — 12.254 objetos
6/6 con `country` lleno (Guatemala, Perú, R.D. Congo, EEUU, Guatemala, Colombia). `culture` también lleno siempre. `city`/`region` vacíos.
→ **`country` alcanza para geocodificar.**

## Egyptian Art (dept. 10) — 27.968 objetos
6/6 con `country`="Egypt". Varios además traen `region`/`subregion`/`locale`/`excavation` con detalle fino (ej. "Memphite Region" / "Saqqara" / "MMA excavations, 1920–22"). Esta es la data más rica de las tres: permite ubicar la pieza a nivel de sitio arqueológico, no solo país.
→ **Mejor candidato para el primer mapa piloto.**

## Ancient West Asian Art (dept. 3) — 6.375 objetos
6/6 con `country` VACÍO. En cambio `region` está siempre lleno, pero con nombres históricos, no países modernos: "Mesopotamia", "Levant", "Anatolia", "Northern Syria or eastern Anatolia".
→ **Acá `country` no sirve. Hay que armar un fallback `country → region → subregion` y un diccionario propio de nombres históricos a coordenadas** (Mesopotamia, Levant, Anatolia, etc. no los resuelve un geocoder moderno de forma directa).

## Conclusión para el pipeline

1. Lógica de extracción de origen: usar `country` si existe; si no, `region`; si no, `subregion`. Guardar también `culture` como dato secundario (útil para el storytelling, no para geocodificar).
2. Nada de geocodificar en vivo contra Nominatim (política lo prohíbe para bulk). Armar una tabla estática propia: países modernos (fácil, hay datasets libres de centroides) + un diccionario chico a mano para regiones históricas recurrentes (Mesopotamia, Levant, Anatolia, Nubia, etc. — van a aparecer una y otra vez).
3. Egyptian Art es el mejor punto de partida: dato limpio, alto volumen, y con contexto de excavación que conecta directo con el tema de expropiación/colonización.
