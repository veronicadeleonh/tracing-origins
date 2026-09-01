import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import Map, { Source, Layer, Popup } from "react-map-gl/mapbox";
import type { MapMouseEvent } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import data from "./data/objects.json";
import type { DataBundle, MuseumObject } from "./types";
import { groupByCountry, groupByOrigin, jitteredPoint, objectHasResearch, type OriginCluster } from "./geo";
import { MUSEUM_COLORS, MUSEUM_COUNTRY, DEFAULT_COLOR, ORIGIN_COLOR } from "./colors";
import { ClusterPanel } from "./components/ClusterPanel";
import { ObjectDetail } from "./components/ObjectDetail";
import { Timeline } from "./components/Timeline";
import { WelcomeModal } from "./components/WelcomeModal";
import { SpotlightTour } from "./components/SpotlightTour";
import { HISTORICAL_EVENTS } from "./data/historicalEvents";
import { NATURAL_EARTH_NAME_TO_COUNTRY_KEY } from "./data/countryPolygons";
import { STRINGS, type Lang } from "./i18n";
import "./App.css";

// Nivel 1 de "notas de contexto en la UI" (ver CLAUDE.md) — accesible vía el
// botón "?" persistente. Ya no se auto-abre en la primera visita (01/09, ver
// TOUR_SEEN_KEY) -- la key se mantiene igual para no perder el estado
// "visto" de quienes ya cerraron el modal antes de este cambio.
const WELCOME_SEEN_KEY = "tracing-origins-welcome-seen";
// Onboarding interactivo con spotlight (01/09) — reemplaza la apertura
// automática de WelcomeModal en la primera visita, ver SpotlightTour.tsx.
const TOUR_SEEN_KEY = "tracing-origins-tour-seen";
// Toggle ES/EN (17/08) — alcance acordado con el usuario: solo texto de
// interfaz (ver i18n.ts). Persistido igual que WELCOME_SEEN_KEY, mismo
// patrón de localStorage + useEffect al montar.
const LANG_KEY = "tracing-origins-lang";

const TIMELINE_MIN_YEAR = 1700;
const TIMELINE_MAX_YEAR = 2020;
const TIMELINE_DEFAULT_YEAR = 1920;

// Se sirve desde public/ y se pide con fetch() recién cuando el usuario activa
// la capa (en vez de bundlearlo con ?raw) porque el geojson del timeline
// completo (todas las décadas) pesa varios MB — inlinearlo en el JS del build
// infla el bundle principal innecesariamente para quien nunca prende la capa.
const COLONIAL_OVERLAY_URL = `${import.meta.env.BASE_URL}colonial_overlay.geojson`;
// navigator_routes.geojson pesa ~12KB (50 rutas, cada una una línea de 2
// puntos) — nada que ver con el overlay colonial, pero se fetchea con el
// mismo trigger (timelineOpen) por consistencia de patrón, no por necesidad
// real de lazy-loading.
const NAVIGATOR_ROUTES_URL = `${import.meta.env.BASE_URL}navigator_routes.geojson`;
// Búsqueda por país vía click en el mapa (19/08, segunda vuelta) — capa
// invisible de polígonos de país (Natural Earth 110m, ver countryPolygons.ts
// para la traducción de nombres), fetcheada bajo demanda recién cuando se
// activa el toggle "Click en el mapa" (mismo patrón lazy que el overlay
// colonial), no de entrada — la mayoría de las visitas nunca la va a usar.
const COUNTRIES_GEOJSON_URL = `${import.meta.env.BASE_URL}countries.geojson`;
// Orden fijo para agrupar los toggles de museo por país (31/08) -- ver
// museumGroups más abajo.
const MUSEUM_COUNTRY_ORDER = ["us", "fr", "uk"];

// Zoom inicial del globo, responsive (01/09, pedido de la usuaria: "el mapa
// en mobile debe empezar más alejado, que se vea todo el globo terráqueo").
// zoom:2 fijo se eligió y se ve bien en un viewport ancho de desktop, pero
// en un teléfono angosto el mismo zoom muestra una porción mucho más
// recortada del globo -- a igual zoom, un viewport más angosto en píxeles
// siempre encuadra menos superficie del planeta, sin importar la proyección.
// Se usa el lado más chico del viewport (no solo el ancho) para que
// funcione igual de bien en landscape que en portrait. Calculado una sola
// vez al montar -- initialViewState de react-map-gl solo se lee al primer
// render, así que no hace falta recalcular en cada resize.
function getInitialMapZoom(): number {
  if (typeof window === "undefined") return 2;
  const size = Math.min(window.innerWidth, window.innerHeight);
  if (size <= 420) return 0.4;
  if (size <= 640) return 0.9;
  if (size <= 900) return 1.4;
  return 2;
}

const bundle = data as DataBundle;

// mismo color que cada museo, para reforzar la conexión territorio-colonial
// -> museo que se benefició de él. UK = BM (rojo), Francia = el teal de
// Louvre/Quai Branly (31/08: ahora hay 2 museos franceses en la muestra,
// MUSEUM_COLORS.qb es una variante más oscura del mismo teal -- ver
// colors.ts -- así que este fill sigue representando "Francia" en general,
// no específicamente al Louvre).
const COLONIAL_POWER_COLORS: Record<string, string> = {
  uk: MUSEUM_COLORS.bm,
  fr: MUSEUM_COLORS.louvre,
};

// Ícono de barco repetido a lo largo de las rutas de navegación (symbol-
// placement: "line") — la única diferenciación visual entre esas líneas y
// las de pieza->museo era el line-dasharray, que no se nota lo suficiente a
// simple vista (confirmado por el usuario el 17/08). Se dibuja a mano en un
// canvas en vez de cargar un asset externo, así el color exacto por potencia
// (mismo COLONIAL_POWER_COLORS que ya se usa en el resto de esta capa) queda
// resuelto sin necesitar 2 archivos SVG separados o un ícono SDF.
function buildShipIcon(color: string, size = 11): { width: number; height: number; data: Uint8Array } {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = color;
  // Triángulo simple apuntando "al este" — Mapbox lo rota solo según la
  // dirección de la línea en cada tramo (symbol-placement: "line"). Alto
  // proporcional a `size` (no un offset fijo en px) para que reducir el
  // tamaño no lo deforme.
  const halfHeight = size * 0.32;
  ctx.beginPath();
  ctx.moveTo(1, size / 2 - halfHeight);
  ctx.lineTo(size - 1, size / 2);
  ctx.lineTo(1, size / 2 + halfHeight);
  ctx.closePath();
  ctx.fill();
  const { data } = ctx.getImageData(0, 0, size, size);
  return { width: size, height: size, data: new Uint8Array(data.buffer) };
}

// Mismo triángulo que buildShipIcon (arriba), como SVG en vez de canvas —
// para el chip "Rutas navales" del timeline, así el ícono del toggle es
// literalmente la misma forma que se ve repetida sobre las rutas en el mapa,
// no un emoji de barco sin relación visual con lo que representa.
const ROUTES_TOGGLE_ICON = (
  <svg viewBox="0 0 12 12" width="9" height="9" aria-hidden="true">
    <polygon points="1,2.16 11,6 1,9.84" fill="currentColor" />
  </svg>
);

// `kind: "country"` (19/08) marca que `cluster` no es un punto de origen real
// sino un resultado de la búsqueda "al revés" por país (ver groupByCountry en
// geo.ts) — mismo shape que OriginCluster (label + objects, lat/lon sin uso
// real acá), reusado tal cual para no duplicar ClusterPanel/ObjectDetail ni
// la lógica de prev/next. Sin `kind`, el comportamiento es exactamente el de
// siempre (click en un punto de origen del mapa).
type PanelState =
  | { view: "cluster"; cluster: OriginCluster; kind?: "country" }
  | { view: "object"; cluster: OriginCluster; object: MuseumObject; kind?: "country" }
  | null;

// Tooltip de 2 líneas (19/08, pedido de la usuaria) -- título en negrita
// (nombre del punto: origen, museo o país) + una segunda línea con el dato
// secundario (cuenta de piezas, ciudad del museo). Reemplaza el string
// plano de una sola línea que tenía antes.
// `kind` (31/08, pedido de la usuaria: "diferenciar el tooltip de museos del
// de origen") -- el tooltip de museos invierte la paleta (fondo oscuro,
// texto claro) respecto del de origen/país (fondo claro, texto oscuro) para
// que se distingan de un vistazo, sin depender de leer el texto. Ver
// .map-tooltip-popup--museum en App.css.
type TooltipState = { longitude: number; latitude: number; title: string; subtitle: string; kind: "origin" | "museum" | "country" } | null;

function App() {
  const [visibleMuseums, setVisibleMuseums] = useState<Record<string, boolean>>(
    () => Object.fromEntries(Object.keys(bundle.museums).map((id) => [id, true])),
  );
  // Filtro por estado de investigación (18/08, pedido explícito de la
  // usuaria junto con el tratamiento visual de context_flags): además de
  // marcar qué piezas tienen layer 3, dejar ocultar/mostrar según eso.
  // "all" es el default — no cambia el comportamiento previo.
  const [researchFilter, setResearchFilter] = useState<"all" | "with" | "without">("all");
  // Filtro por mecanismo (context_flags), agregado 23/08 al retomar el ítem
  // "tratamiento narrativo de context_flags" del backlog -- ver CLAUDE.md.
  // Multi-select (Set): una pieza matchea si tiene AL MENOS UNO de los
  // flags elegidos (OR, no AND) -- la mayoría de las piezas tienen 2-3
  // flags, exigir todos sería demasiado restrictivo. Vacío = sin filtro,
  // mismo comportamiento que antes de esta ronda.
  const [selectedFlags, setSelectedFlags] = useState<Set<string>>(new Set());
  const [mechanismMenuOpen, setMechanismMenuOpen] = useState(false);
  // Cerrar el dropdown al tocar/clickear afuera (01/09, reportado por la
  // usuaria: "tap afuera no funciona" -- las casillas ya aplican el filtro
  // al toquealtirte, así que no hace falta un botón "Aplicar"; lo único que
  // faltaba era el gesto esperado de cerrar el menú al tocar en cualquier
  // otro lado, en vez de tener que volver a tocar el botón "Mecanismo").
  // pointerdown (no click) para que el cierre ocurra ANTES de que un tap en
  // otro control dispare su propio onClick en el mismo gesto.
  const mechanismMenuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!mechanismMenuOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      if (mechanismMenuRef.current && !mechanismMenuRef.current.contains(e.target as Node)) {
        setMechanismMenuOpen(false);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [mechanismMenuOpen]);
  // Búsqueda "al revés" por país, segunda vuelta (19/08) — reemplazó al
  // buscador de texto original (retirado a pedido de la usuaria, ver
  // CLAUDE.md): ahora la única forma de elegir un país es clickeándolo
  // directamente en el mapa. Apagado por default: sin esto, cualquier click
  // en tierra (que hoy no hace nada) abriría un panel, lo que rompería el
  // gesto normal de arrastrar/rotar el globo para quien no busca esto. Se
  // activa a mano con el toggle "Click en el mapa" + su botón "i".
  const [countryClickEnabled, setCountryClickEnabled] = useState(false);
  const [countryClickNoteOpen, setCountryClickNoteOpen] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- geojson global type no está disponible, mismo criterio que colonialOverlay/navigatorRoutes
  const [countryPolygons, setCountryPolygons] = useState<any>(null);
  useEffect(() => {
    if (!countryClickEnabled || countryPolygons) return;
    fetch(COUNTRIES_GEOJSON_URL)
      .then((res) => res.json())
      .then(setCountryPolygons)
      .catch((err) => console.error("No se pudo cargar countries.geojson", err));
  }, [countryClickEnabled, countryPolygons]);
  const [panel, setPanel] = useState<PanelState>(null);
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const [cursor, setCursor] = useState("grab");
  const [timelineYear, setTimelineYear] = useState(TIMELINE_DEFAULT_YEAR);
  const [timelineOpen, setTimelineOpen] = useState(false);
  // Dos capas independientes dentro del mismo dock/timeline — el usuario
  // puede ver solo imperios, solo rutas, o ambas a la vez. Arrancan
  // prendidas las dos cuando se abre el dock (menos fricción que arrancar
  // todo apagado y obligar a 2 clicks extra).
  const [showTerritories, setShowTerritories] = useState(true);
  const [showRoutes, setShowRoutes] = useState(true);
  const [museumNoteOpen, setMuseumNoteOpen] = useState<string | null>(null);
  // Drawer de filtros para mobile (01/09, feedback de la usuaria con
  // capturas de iPhone SE/iPad mini: los filtros de museo/investigación +
  // el switch de país se superponían ilegibles arriba del mapa en pantallas
  // angostas). En desktop este estado no hace nada -- .mobile-filters-toggle
  // queda display:none y .mobile-filters-wrap se muestra siempre vía CSS,
  // ver App.css. Arranca cerrado para no tapar el mapa apenas se carga.
  const [filtersOpen, setFiltersOpen] = useState(false);
  // WelcomeModal ya no se auto-abre (01/09, ver TOUR_SEEN_KEY más abajo) --
  // queda accesible solo vía el botón "?" persistente, sin cambios en su
  // propio comportamiento de apertura/cierre manual.
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  const closeWelcome = useCallback(() => {
    localStorage.setItem(WELCOME_SEEN_KEY, "1");
    setWelcomeOpen(false);
  }, []);
  // Onboarding interactivo con spotlight (01/09) -- reemplaza la apertura
  // automática de WelcomeModal en la primera visita (ver CLAUDE.md, feedback
  // de usuarios de prueba). Key de localStorage nueva y separada de
  // WELCOME_SEEN_KEY a propósito: es contenido nuevo, así que quien ya había
  // visto el modal viejo igual ve el tour una vez.
  const [tourOpen, setTourOpen] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem(TOUR_SEEN_KEY)) setTourOpen(true);
  }, []);
  const closeTour = useCallback(() => {
    localStorage.setItem(TOUR_SEEN_KEY, "1");
    setTourOpen(false);
  }, []);
  const openInfoFromTour = useCallback(() => {
    closeTour();
    setWelcomeOpen(true);
  }, [closeTour]);
  // Default inglés (19/08, pedido de la usuaria) — antes era español por
  // default. localStorage sigue siendo la fuente de verdad si el visitante
  // ya tocó el toggle antes; el fallback (primera visita, sin nada guardado
  // todavía) es el único que cambió, de "es" a "en".
  const [lang, setLang] = useState<Lang>(() => (localStorage.getItem(LANG_KEY) === "es" ? "es" : "en"));
  const s = STRINGS[lang];
  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const next = prev === "es" ? "en" : "es";
      localStorage.setItem(LANG_KEY, next);
      return next;
    });
  }, []);
  // HISTORICAL_EVENTS trae year/color fijos (no cambian por idioma); el label
  // se toma de i18n.ts por índice — mismo orden que el array de datos.
  const localizedEvents = useMemo(
    () => HISTORICAL_EVENTS.map((ev, i) => ({ ...ev, label: s.historicalEvents[i] ?? ev.label })),
    [s],
  );
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- tipo de MapRef de react-map-gl no vale la pena importar solo para esto
  const mapRef = useRef<any>(null);

  const handleMapLoad = useCallback(() => {
    const map = mapRef.current?.getMap?.();
    if (!map) return;
    // Se registran una sola vez, al cargar el mapa — los símbolos de las
    // rutas de navegación (más abajo) referencian estos IDs por nombre.
    if (!map.hasImage("ship-uk")) map.addImage("ship-uk", buildShipIcon(COLONIAL_POWER_COLORS.uk));
    if (!map.hasImage("ship-fr")) map.addImage("ship-fr", buildShipIcon(COLONIAL_POWER_COLORS.fr));
  }, []);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- geojson global type no está disponible, ver nota de colonialOverlay más arriba
  const [colonialOverlay, setColonialOverlay] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- ídem colonialOverlay
  const [navigatorRoutes, setNavigatorRoutes] = useState<any>(null);

  useEffect(() => {
    if (!timelineOpen || colonialOverlay) return;
    fetch(COLONIAL_OVERLAY_URL)
      .then((res) => res.json())
      .then(setColonialOverlay)
      .catch((err) => console.error("No se pudo cargar colonial_overlay.geojson", err));
  }, [timelineOpen, colonialOverlay]);

  useEffect(() => {
    if (!timelineOpen || navigatorRoutes) return;
    fetch(NAVIGATOR_ROUTES_URL)
      .then((res) => res.json())
      .then(setNavigatorRoutes)
      .catch((err) => console.error("No se pudo cargar navigator_routes.geojson", err));
  }, [timelineOpen, navigatorRoutes]);

  const toggleMuseum = useCallback((id: string) => {
    setVisibleMuseums((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  // Agrupar los toggles de museo por país (31/08, pedido de la usuaria) --
  // MUSEUM_COUNTRY_ORDER (fijo, no alfabético ni el de bundle.museums) para
  // que los grupos salgan en el mismo orden relativo de siempre (Met,
  // Louvre/Quai Branly, BM) en vez de saltar según qué claves trae el JSON.
  // Un museo cuyo país no esté en MUSEUM_COUNTRY (no debería pasar, pero por
  // las dudas) queda afuera de todo grupo en vez de romper el render.
  const museumGroups = useMemo(
    () =>
      MUSEUM_COUNTRY_ORDER.map((country) => ({
        country,
        museums: Object.entries(bundle.museums).filter(([id]) => MUSEUM_COUNTRY[id] === country),
      })).filter((group) => group.museums.length > 0),
    [],
  );

  // Apagar "Click en el mapa" con un resultado de país abierto (19/08,
  // pedido de la usuaria): no alcanza con dejar de atenuar las líneas
  // futuras -- si hay un panel de país abierto, se cierra entero (vuelve
  // `null`), lo que a su vez limpia highlightedObjectIds y devuelve todas
  // las líneas a opacidad normal. Un cluster de origen normal (kind
  // indefinido) no se toca.
  const toggleCountryClick = useCallback(() => {
    setCountryClickEnabled((prev) => {
      const next = !prev;
      if (!next) setPanel((p) => (p && p.kind === "country" ? null : p));
      return next;
    });
  }, []);

  const visibleObjects = useMemo(
    () =>
      bundle.objects.filter((obj) => {
        if (!obj.sourceMuseum || !visibleMuseums[obj.sourceMuseum]) return false;
        if (researchFilter === "with" && !objectHasResearch(obj)) return false;
        if (researchFilter === "without" && objectHasResearch(obj)) return false;
        // Filtro por mecanismo: implica "con investigación" aunque
        // researchFilter esté en "all" -- una pieza sin layer 3 no tiene
        // flags, así que nunca podría matchear de todos modos.
        if (selectedFlags.size > 0) {
          if (!objectHasResearch(obj)) return false;
          const flags = obj.context?.context_flags ?? [];
          if (!flags.some((f) => selectedFlags.has(f))) return false;
        }
        return true;
      }),
    [visibleMuseums, researchFilter, selectedFlags],
  );

  // Texto del contador de piezas, compartido entre las 2 copias del pill
  // (la de siempre, al final de .museum-toggles, y la nueva de arriba del
  // drawer mobile -- ver .piece-counter-top/.piece-counter-inline en
  // App.css) para no duplicar el ternario.
  const pieceCounterText =
    visibleObjects.length === bundle.objects.length
      ? s.pieceCounterAll(visibleObjects.length)
      : s.pieceCounterFiltered(visibleObjects.length, bundle.objects.length);

  // Cuenta de piezas por flag, para el dropdown de mecanismo -- se calcula
  // sobre TODO el dataset (no visibleObjects) para que la lista de opciones
  // y sus conteos no cambien según qué otros filtros estén activos en ese
  // momento, mismo criterio que ya usa groupByCountry en geo.ts.
  const flagCounts = useMemo(() => {
    // Objeto plano en vez de `new Map(...)` -- el import por default de
    // react-map-gl se llama "Map" y shadowea el constructor global acá.
    const counts: Record<string, number> = {};
    for (const obj of bundle.objects) {
      for (const flag of obj.context?.context_flags ?? []) {
        counts[flag] = (counts[flag] ?? 0) + 1;
      }
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, []);

  const toggleFlag = useCallback((flag: string) => {
    setSelectedFlags((prev) => {
      const next = new Set(prev);
      if (next.has(flag)) next.delete(flag);
      else next.add(flag);
      return next;
    });
  }, []);

  // Elegir "Sin investigación" con flags activos dejaría el filtro en un
  // estado sin resultados posibles (esas piezas nunca tienen flags) -- se
  // limpia la selección de flags al mismo tiempo, en vez de dejar al
  // usuario con un resultado vacío sin pista de por qué.
  const setResearchFilterAndClearFlags = useCallback((value: "all" | "with" | "without") => {
    setResearchFilter(value);
    if (value === "without") setSelectedFlags(new Set());
  }, []);

  const clusters = useMemo(() => groupByOrigin(visibleObjects, lang), [visibleObjects, lang]);

  // Búsqueda por país: agrupa TODOS los objetos (bundle.objects, no
  // visibleObjects) — ver comentario en groupByCountry (geo.ts). Usado por
  // el click-en-el-mapa (handleClick/handleMouseMove) para encontrar el
  // CountryGroup correspondiente al país clickeado/hovereado.
  const countryGroups = useMemo(() => groupByCountry(bundle.objects, lang), [lang]);

  // Búsqueda por país (19/08): mientras el panel abierto sea un resultado de
  // país (kind === "country", por click en el mapa), se atenúan todas las
  // líneas pieza->museo salvo las que salen de ese país — "revela" el
  // patrón de ese origen sin tocar el resto del modelo de datos. Cuarta
  // vuelta (19/08, mismo día, feedback de la usuaria: "no estoy segura de
  // esta función, quizás debería atenuar todo apenas se activa, como hint
  // de que algo se prendió"): mientras el toggle "Click en el mapa" está
  // prendido pero todavía no se eligió ningún país, se atenúan TODAS las
  // líneas (Set vacío — ninguna coincide, así que `dimmed` da true para
  // todas) en vez de dejarlas como si nada hubiera cambiado; es la señal
  // visual de "este modo está activo, clickeá un país". Apagar el toggle
  // sin haber elegido país vuelve todo a la opacidad normal (null).
  const highlightedObjectIds = useMemo(() => {
    if (panel && panel.kind === "country") return new Set(panel.cluster.objects.map((o) => o.objectID));
    if (countryClickEnabled) return new Set<string>();
    return null;
  }, [panel, countryClickEnabled]);

  const linesGeoJSON = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: clusters.flatMap((cluster) =>
      cluster.objects.flatMap((obj, i) => {
        const dest = obj.sourceMuseum ? bundle.museums[obj.sourceMuseum] : undefined;
        if (!dest) return [];
        const [jLat, jLon] = jitteredPoint(cluster.lat, cluster.lon, i, cluster.objects.length);
        const color = (obj.sourceMuseum && MUSEUM_COLORS[obj.sourceMuseum]) || DEFAULT_COLOR;
        const dimmed = highlightedObjectIds ? !highlightedObjectIds.has(obj.objectID) : false;
        return [{
          type: "Feature" as const,
          geometry: { type: "LineString" as const, coordinates: [[jLon, jLat], [dest.lon, dest.lat]] },
          properties: { objectID: obj.objectID, color, dimmed },
        }];
      })
    ),
  }), [clusters, highlightedObjectIds]);

  const originsGeoJSON = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: clusters.map((cluster) => {
      // Tratamiento narrativo de context_flags, segunda vuelta (18/08,
      // feedback de la usuaria sobre la primera versión): en vez de un
      // color de acento genérico para "investigado", se rellena el punto
      // con el color del museo dueño de la primera pieza investigada del
      // cluster (orden determinístico, cluster.objects ya viene ordenado
      // por objectID) — visualmente sugiere "sabemos el recorrido de acá
      // hasta ese museo", reforzando el mismo lenguaje de color que ya usan
      // las líneas origen->museo. Simplificación conocida: si un cluster
      // tiene piezas investigadas de más de un museo, se muestra el color
      // de la primera nomás — no se intenta partir el círculo.
      const researched = cluster.objects.find(objectHasResearch);
      const circleColor = researched
        ? MUSEUM_COLORS[researched.sourceMuseum ?? ""] ?? ORIGIN_COLOR
        : ORIGIN_COLOR;
      return {
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [cluster.lon, cluster.lat] },
        properties: {
          label: cluster.label,
          count: cluster.objects.length,
          clusterKey: `${cluster.lat}|${cluster.lon}|${cluster.label}`,
          circleColor,
        },
      };
    }),
  }), [clusters]);

  const museumsGeoJSON = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: Object.entries(bundle.museums)
      .filter(([id]) => visibleMuseums[id])
      .map(([id, m]) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [m.lon, m.lat] },
        properties: { id, name: m.name, city: m.city, color: MUSEUM_COLORS[id] ?? DEFAULT_COLOR },
      })),
  }), [visibleMuseums]);

  // Navegación prev/next dentro de un cluster de origen (18/08) — update
  // funcional para no depender de `panel` en las deps del callback (evita
  // handlers con closures viejas si el usuario navega rápido). Sirve tanto
  // para prev como para next: solo cambia qué índice le pasan los botones.
  const selectClusterObject = useCallback((index: number) => {
    setPanel((prev) => {
      if (!prev) return prev;
      const object = prev.cluster.objects[index];
      if (!object) return prev;
      return { view: "object", cluster: prev.cluster, object, kind: prev.kind };
    });
  }, []);

  const selectCountryGroup = useCallback((group: { key: string; label: string; objects: MuseumObject[] }) => {
    setPanel({
      view: "cluster",
      cluster: { lat: 0, lon: 0, label: group.label, objects: group.objects, key: group.key },
      kind: "country",
    });
  }, []);

  // Highlight visual del país seleccionado (20/08, pedido de la usuaria: con
  // "Click en el mapa" activo, hacer evidente qué país está elegido, no solo
  // atenuar el resto de las líneas). `panel.cluster.key` es el
  // `originCountry`/`originCountryEn` (ver geo.ts), pero el polígono de
  // `countries.geojson` está indexado por nombre de Natural Earth -- puede
  // haber más de un nombre por key (ej. "North Korea"/"South Korea" ambos
  // mapean a "Corea", ver countryPolygons.ts), así que se resuelve la lista
  // completa de nombres que matchean, no un único nombre. Vacío (no `[]`
  // fijo, sino el resultado de un filter que no encuentra nada) cuando no
  // hay país seleccionado -- el filtro de Mapbox con `["literal", []]` no
  // matchea ningún feature, así que la capa de highlight queda sin pintar
  // nada en vez de tener que condicionar su render.
  const highlightedCountryNames = useMemo(() => {
    if (!panel || panel.kind !== "country" || !panel.cluster.key) return [];
    const key = panel.cluster.key;
    return Object.entries(NATURAL_EARTH_NAME_TO_COUNTRY_KEY)
      .filter(([, k]) => k === key)
      .map(([name]) => name);
  }, [panel]);

  const handleClick = useCallback((e: MapMouseEvent) => {
    if (!e.features?.length) return;
    const f = e.features[0] as unknown as { layer?: { id?: string }; properties?: Record<string, string | number | undefined> };
    const properties = f.properties ?? {};
    if (f.layer?.id === "origins") {
      const key = properties.clusterKey as string;
      const cluster = clusters.find((c) => `${c.lat}|${c.lon}|${c.label}` === key);
      if (cluster) setPanel({ view: "cluster", cluster });
    } else if (f.layer?.id === "country-hit") {
      // Click en el mapa (19/08, segunda vuelta) -- mismo flujo que elegir
      // un país en el buscador (selectCountryGroup), solo cambia cómo se
      // identificó el país. Si el nombre de Natural Earth no mapea a
      // ninguno de nuestros países (país sin piezas en la muestra), no pasa
      // nada -- el hover ya avisó "sin piezas" antes del click, ver
      // handleMouseMove.
      const naturalEarthName = String(properties.name ?? "");
      const key = NATURAL_EARTH_NAME_TO_COUNTRY_KEY[naturalEarthName];
      const group = key ? countryGroups.find((g) => g.key === key) : undefined;
      if (group && group.objects.length > 0) selectCountryGroup(group);
    }
  }, [clusters, countryGroups, selectCountryGroup]);

  const handleMouseMove = useCallback((e: MapMouseEvent) => {
    if (e.features?.length) {
      const f = e.features[0] as unknown as { layer?: { id?: string }; properties?: Record<string, string | number | undefined> };
      const properties = f.properties ?? {};
      let title: string;
      let subtitle: string;
      let kind: "origin" | "museum" | "country";
      // "pointer" solo cuando lo que está debajo del mouse realmente hace
      // algo al clickear -- para country-hit eso significa un país con al
      // menos 1 pieza en la muestra (22/08, pedido de la usuaria: antes el
      // cursor cambiaba a mano sobre cualquier país, incluidos los que no
      // tienen ninguna pieza y por lo tanto el click no hace nada).
      let clickable = true;
      if (f.layer?.id === "origins") {
        title = String(properties.label);
        subtitle = s.tooltipPieceCount(Number(properties.count));
        kind = "origin";
      } else if (f.layer?.id === "country-hit") {
        // Mismo lookup que handleClick, pero en hover: avisa de antemano si
        // ese país no tiene piezas en la muestra, para que el click (o la
        // falta de reacción al click) no sorprenda a nadie.
        const naturalEarthName = String(properties.name ?? "");
        const key = NATURAL_EARTH_NAME_TO_COUNTRY_KEY[naturalEarthName];
        const group = key ? countryGroups.find((g) => g.key === key) : undefined;
        const hasPieces = !!group && group.objects.length > 0;
        title = group?.label ?? naturalEarthName;
        subtitle = hasPieces ? s.tooltipPieceCount(group.objects.length) : s.tooltipCountryEmptySub;
        clickable = hasPieces;
        kind = "country";
      } else {
        title = String(properties.name);
        subtitle = String(properties.city);
        kind = "museum";
      }
      setTooltip({ longitude: e.lngLat.lng, latitude: e.lngLat.lat, title, subtitle, kind });
      setCursor(clickable ? "pointer" : "grab");
    } else {
      setTooltip(null);
      setCursor("grab");
    }
  }, [s, countryGroups]);

  return (
    <div className="app-layout">
      <div className="map-pane">
        <button
          type="button"
          className="welcome-trigger-btn"
          aria-label={s.welcomeTriggerAria}
          onClick={() => setWelcomeOpen(true)}
        >
          ?
        </button>
        <button
          type="button"
          className="lang-toggle-btn"
          aria-label={s.langToggleAria}
          onClick={toggleLang}
        >
          {s.langToggleLabel}
        </button>
        {/* Drawer de filtros para mobile (01/09) -- botón pull-tab siempre en
            el DOM, pero display:none arriba de ~900px (ver App.css): en
            desktop .mobile-filters-wrap de abajo ya está siempre visible por
            su cuenta, este botón sería redundante ahí. En pantallas angostas
            reemplaza a los filtros/switch de país, que dejan de mostrarse
            solos y pasan a vivir dentro del drawer que este botón abre. */}
        <button
          type="button"
          className={`mobile-filters-toggle${filtersOpen ? " open" : ""}`}
          aria-expanded={filtersOpen}
          aria-label={s.mobileFiltersToggleAria}
          onClick={() => setFiltersOpen((v) => !v)}
        >
          {s.mobileFiltersToggleLabel}
          <span className="mobile-filters-toggle-arrow" aria-hidden="true">{filtersOpen ? "▲" : "▼"}</span>
        </button>
        {/* Envoltorio puramente estructural en desktop (los hijos siguen
            position:absolute contra .map-pane, este div no les cambia nada);
            en mobile es lo que el botón de arriba muestra/oculta como un
            único panel apilado en columna -- ver .mobile-filters-wrap.open
            en App.css. */}
        <div className={`mobile-filters-wrap${filtersOpen ? " open" : ""}`}>
          {/* Copia del contador de piezas, visible solo dentro del drawer
              mobile (pedido de la usuaria: que el total quede arriba de
              todo, no perdido al final de la lista de museos) -- ver
              pieceCounterText más arriba y .piece-counter-top en App.css.
              La copia de siempre (.piece-counter-inline, al final de
              .museum-toggles) se oculta cuando el drawer está abierto para
              no duplicar el número dos veces en pantalla. */}
          <div className="piece-counter piece-counter-top">{pieceCounterText}</div>
          {/* Búsqueda por país vía click en el mapa (19/08, quinta vuelta) --
              movida fuera de top-controls (filtros de museo/investigación,
              arriba a la izquierda) a su propio control flotante arriba a la
              derecha, debajo de "?"/idioma: es una función completamente
              distinta a los filtros (no oculta/muestra piezas, cambia qué
              hace un click en el mapa), así que separarla espacialmente y
              usar un switch en vez de un pill-botón (mismo lenguaje visual
              que los filtros) evita que se lea como "un filtro más". */}
          <div className="country-click-panel">
            <span className="country-click-label">{s.countryClickToggleLabel}</span>
            <button
              type="button"
              role="switch"
              aria-checked={countryClickEnabled}
              aria-label={s.countryClickToggleAria}
              className={`country-click-switch${countryClickEnabled ? " on" : ""}`}
              onClick={toggleCountryClick}
            >
              <span className="country-click-switch-knob" aria-hidden="true" />
            </button>
            <button
              type="button"
              className={`museum-info-btn${countryClickNoteOpen ? " open" : ""}`}
              aria-label={s.countryClickNoteAria}
              aria-expanded={countryClickNoteOpen}
              onClick={() => setCountryClickNoteOpen((v) => !v)}
            >
              i
            </button>
            {countryClickNoteOpen && <div className="museum-note country-click-note">{s.countryClickNoteText}</div>}
          </div>
          <div className="top-controls">
        <div className="museum-toggles">
          <span className="filter-row-label">{s.museumFilterRowLabel}</span>
          {museumGroups.map(({ country, museums }) => (
            <div key={country} className="museum-country-group">
              <span className="museum-country-label">{s.museumCountryNames[country]}</span>
              <div className="museum-country-row">
                {museums.map(([id, m]) => (
                  <div
                    key={id}
                    className={`museum-toggle-wrap${visibleMuseums[id] ? " active" : " inactive"}`}
                  >
                    <button
                      type="button"
                      className="museum-toggle"
                      onClick={() => toggleMuseum(id)}
                    >
                      <span
                        className="museum-toggle-dot"
                        style={{ background: MUSEUM_COLORS[id] ?? DEFAULT_COLOR }}
                      />
                      {m.name}
                    </button>
                    <button
                      type="button"
                      className={`museum-info-btn${museumNoteOpen === id ? " open" : ""}`}
                      aria-label={s.museumInfoAria(m.name)}
                      aria-expanded={museumNoteOpen === id}
                      onClick={() => setMuseumNoteOpen((cur) => (cur === id ? null : id))}
                    >
                      i
                    </button>
                    {museumNoteOpen === id && (
                      <div className="museum-note">{s.museumNotes[id]}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div className="piece-counter piece-counter-inline">{pieceCounterText}</div>
        </div>
        <div className="research-filter-row">
          <span className="filter-row-label">{s.researchFilterRowLabel}</span>
          <div className="research-filter" role="group" aria-label={s.researchFilterAria}>
            {(["all", "with", "without"] as const).map((value) => (
              <button
                key={value}
                type="button"
                className={`research-filter-btn${researchFilter === value ? " active" : ""}`}
                aria-pressed={researchFilter === value}
                onClick={() => setResearchFilterAndClearFlags(value)}
              >
                {s.researchFilterLabels[value]}
              </button>
            ))}
          </div>
          {/* Filtro por mecanismo (context_flags), 23/08 -- dropdown aparte
              del pill de arriba porque son ~21 opciones, no 3: un pill no
              escala a eso. Deshabilitado con "Sin investigación" activo
              (esas piezas nunca tienen flags, ver setResearchFilterAndClearFlags). */}
          <div className="mechanism-filter-wrap" ref={mechanismMenuRef}>
            <button
              type="button"
              className={`mechanism-filter-btn${selectedFlags.size > 0 ? " active" : ""}`}
              aria-expanded={mechanismMenuOpen}
              aria-label={s.mechanismFilterAria}
              disabled={researchFilter === "without"}
              onClick={() => setMechanismMenuOpen((v) => !v)}
            >
              {selectedFlags.size > 0 ? s.mechanismFilterLabelActive(selectedFlags.size) : s.mechanismFilterLabel}
              <span className="mechanism-filter-caret" aria-hidden="true">{mechanismMenuOpen ? "▲" : "▼"}</span>
            </button>
            {mechanismMenuOpen && (
              <div className="mechanism-menu">
                {selectedFlags.size > 0 && (
                  <button
                    type="button"
                    className="mechanism-menu-clear"
                    onClick={() => setSelectedFlags(new Set())}
                  >
                    {s.mechanismClearLabel}
                  </button>
                )}
                <ul className="mechanism-menu-list">
                  {flagCounts.map(([flag, count]) => (
                    <li key={flag}>
                      <label className="mechanism-menu-item">
                        <input
                          type="checkbox"
                          checked={selectedFlags.has(flag)}
                          onChange={() => toggleFlag(flag)}
                        />
                        <span className="mechanism-menu-item-label">{s.contextFlagLabels[flag] ?? flag}</span>
                        <span className="mechanism-menu-item-count">{count}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
        </div>
        </div>
        {welcomeOpen && <WelcomeModal lang={lang} onToggleLang={toggleLang} onClose={closeWelcome} />}
        {tourOpen && <SpotlightTour lang={lang} onClose={closeTour} onOpenInfo={openInfoFromTour} />}
        <Map
          ref={mapRef}
          mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
          initialViewState={{ longitude: 10, latitude: 20, zoom: getInitialMapZoom() }}
          style={{ width: "100%", height: "100%" }}
          mapStyle="mapbox://styles/mapbox/light-v11"
          projection="globe"
          fog={{}}
          interactiveLayerIds={countryClickEnabled ? ["origins", "museums", "country-hit"] : ["origins", "museums"]}
          cursor={cursor}
          onLoad={handleMapLoad}
          onClick={handleClick}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { setTooltip(null); setCursor("grab"); }}
        >
          {countryClickEnabled && countryPolygons && (
            // Capa invisible de hit-testing (19/08, click en el mapa) --
            // agregada primero a propósito, para que quede debajo de
            // origins/museums en el stack de capas: si el click cae
            // exactamente sobre un punto de origen o un museo, ese feature
            // sigue ganando (e.features[0] es el de más arriba), el país
            // solo responde en el resto del área del mapa.
            <Source id="country-hit-src" type="geojson" data={countryPolygons}>
              <Layer id="country-hit" type="fill" paint={{ "fill-color": "#000000", "fill-opacity": 0 }} />
              {/* Highlight del país seleccionado (20/08) -- mismo violeta que
                  ya identifica "activo/seleccionado" en el resto de la UI
                  (.research-filter-btn.active, .country-click-switch.on), en
                  vez de introducir un color nuevo. No son capas
                  interactivas (no entran en interactiveLayerIds): son puro
                  feedback visual sobre la capa invisible de hit-testing. */}
              <Layer
                id="country-hit-highlight-fill"
                type="fill"
                filter={["in", ["get", "name"], ["literal", highlightedCountryNames]]}
                paint={{ "fill-color": "#6a4c93", "fill-opacity": 0.22 }}
              />
              <Layer
                id="country-hit-highlight-outline"
                type="line"
                filter={["in", ["get", "name"], ["literal", highlightedCountryNames]]}
                paint={{ "line-color": "#6a4c93", "line-width": 2.5, "line-opacity": 0.9 }}
              />
            </Source>
          )}
          {timelineOpen && showTerritories && colonialOverlay && (
            <Source id="colonial-overlay-src" type="geojson" data={colonialOverlay}>
              <Layer
                id="colonial-overlay-fill"
                type="fill"
                filter={["all", ["<=", ["get", "FromYear"], timelineYear], [">=", ["get", "ToYear"], timelineYear]]}
                paint={{
                  "fill-color": ["match", ["get", "power"], "uk", COLONIAL_POWER_COLORS.uk, "fr", COLONIAL_POWER_COLORS.fr, DEFAULT_COLOR],
                  "fill-opacity": 0.16,
                }}
              />
              <Layer
                id="colonial-overlay-outline"
                type="line"
                filter={["all", ["<=", ["get", "FromYear"], timelineYear], [">=", ["get", "ToYear"], timelineYear]]}
                paint={{
                  "line-color": ["match", ["get", "power"], "uk", COLONIAL_POWER_COLORS.uk, "fr", COLONIAL_POWER_COLORS.fr, DEFAULT_COLOR],
                  "line-width": 0.6,
                  "line-opacity": 0.4,
                }}
              />
            </Source>
          )}
          {timelineOpen && showRoutes && navigatorRoutes && (
            <Source id="navigator-routes-src" type="geojson" data={navigatorRoutes}>
              <Layer
                id="navigator-routes"
                type="line"
                filter={["all", ["<=", ["get", "FromYear"], timelineYear], [">=", ["get", "ToYear"], timelineYear]]}
                paint={{
                  "line-color": ["match", ["get", "power"], "uk", COLONIAL_POWER_COLORS.uk, "fr", COLONIAL_POWER_COLORS.fr, DEFAULT_COLOR],
                  "line-width": 0.8,
                  "line-opacity": 0.35,
                  // discontinua y más fina que antes — ahora la diferenciación
                  // fuerte con las líneas pieza->museo la hacen los íconos de
                  // barco (capa de abajo), la línea es solo referencia del trazo
                  "line-dasharray": [2, 1.5],
                }}
              />
              <Layer
                id="navigator-routes-ships"
                type="symbol"
                filter={["all", ["<=", ["get", "FromYear"], timelineYear], [">=", ["get", "ToYear"], timelineYear]]}
                layout={{
                  "symbol-placement": "line",
                  "symbol-spacing": 160,
                  "icon-image": ["match", ["get", "power"], "uk", "ship-uk", "fr", "ship-fr", "ship-uk"],
                  "icon-size": 0.75,
                  "icon-rotation-alignment": "map",
                  "icon-allow-overlap": true,
                  "icon-ignore-placement": true,
                }}
              />
            </Source>
          )}
          <Source id="lines" type="geojson" data={linesGeoJSON}>
            <Layer
              id="lines"
              type="line"
              paint={{
                "line-color": ["get", "color"],
                "line-width": 1.4,
                // dimmed viene de highlightedObjectIds (búsqueda por país,
                // 19/08 segunda vuelta) -- 0.55 de siempre cuando no hay país
                // seleccionado o la línea pertenece a él, casi invisible si no.
                "line-opacity": ["case", ["get", "dimmed"], 0.06, 0.55],
              }}
            />
          </Source>
          <Source id="origins-src" type="geojson" data={originsGeoJSON}>
            <Layer
              id="origins"
              type="circle"
              paint={{
                // Relleno con el color del museo que investigó la pieza
                // (o el primero, si hay más de uno en el cluster), gris
                // neutro (ORIGIN_COLOR) para puntos sin ninguna pieza
                // investigada — calculado por feature en originsGeoJSON,
                // no acá, porque depende de qué museo es (ver comentario
                // ahí). Antes era un anillo/stroke con un violeta genérico;
                // cambiado el 18/08 dos veces por feedback de la usuaria:
                // primero a fill (más notorio que un stroke), después a
                // color-por-museo en vez de un acento nuevo (reusa el
                // mismo lenguaje visual de las líneas origen->museo).
                "circle-color": ["get", "circleColor"],
                "circle-opacity": 0.85,
                "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 5, 10, 14],
                "circle-stroke-color": "#fbfaf7",
                "circle-stroke-width": 1,
              }}
            />
          </Source>
          <Source id="museums-src" type="geojson" data={museumsGeoJSON}>
            {/* Diferenciar visualmente los puntos de museo de los de origen
                (19/08, pedido de la usuaria — antes ambos eran círculos lisos
                y se confundían a simple vista). El halo es puramente
                decorativo: no entra en interactiveLayerIds, así que no
                interfiere con clicks/hover, solo hace que el punto de museo
                se lea como un "ancla" institucional (mancha suave + núcleo
                sólido con borde grueso) en vez de un dato más entre los
                puntos de origen (círculos lisos, radio variable, borde fino
                de 1px). */}
            <Layer
              id="museums-halo"
              type="circle"
              paint={{ "circle-color": ["get", "color"], "circle-radius": 16, "circle-opacity": 0.22 }}
            />
            <Layer
              id="museums"
              type="circle"
              paint={{
                "circle-color": ["get", "color"],
                "circle-radius": 9,
                "circle-opacity": 1,
                "circle-stroke-color": "#fbfaf7",
                "circle-stroke-width": 2.5,
              }}
            />
          </Source>
          {tooltip && (
            <Popup
              longitude={tooltip.longitude}
              latitude={tooltip.latitude}
              closeButton={false}
              anchor="bottom"
              className={`map-tooltip-popup${tooltip.kind === "museum" ? " map-tooltip-popup--museum" : ""}`}
              style={{ pointerEvents: "none" }}
            >
              <div className="map-tooltip-title">{tooltip.title}</div>
              <div className="map-tooltip-subtitle">{tooltip.subtitle}</div>
            </Popup>
          )}
        </Map>
        <div className="year-timeline-dock">
          <button
            type="button"
            className={`year-timeline-handle${timelineOpen ? "" : " collapsed"}`}
            onClick={() => setTimelineOpen((v) => !v)}
            aria-expanded={timelineOpen}
          >
            <span className={`year-timeline-handle-arrow${timelineOpen ? " open" : ""}`}>▲</span>
            {s.contextDockLabel}
          </button>
          {timelineOpen && (
            <Timeline
              minYear={TIMELINE_MIN_YEAR}
              maxYear={TIMELINE_MAX_YEAR}
              year={timelineYear}
              onChange={setTimelineYear}
              legend={[
                { label: s.legendUK, color: COLONIAL_POWER_COLORS.uk },
                { label: s.legendFR, color: COLONIAL_POWER_COLORS.fr },
              ]}
              layerToggles={[
                { id: "territories", label: s.layerToggleTerritories, active: showTerritories, note: s.layerNotes.territories },
                { id: "routes", label: s.layerToggleRoutes, active: showRoutes, icon: ROUTES_TOGGLE_ICON, note: s.layerNotes.routes },
              ]}
              onToggleLayer={(id) => {
                if (id === "territories") setShowTerritories((v) => !v);
                if (id === "routes") setShowRoutes((v) => !v);
              }}
              events={localizedEvents}
              lang={lang}
            />
          )}
        </div>
      </div>

      {panel?.view === "cluster" && (
        <ClusterPanel
          cluster={panel.cluster}
          lang={lang}
          onClose={() => setPanel(null)}
          onSelectObject={(object) => setPanel({ view: "object", cluster: panel.cluster, object, kind: panel.kind })}
          showOriginAndMuseum={panel.kind === "country"}
          museums={bundle.museums}
          subtitleOverride={panel.kind === "country" ? s.countryResultsSubtitle(panel.cluster.objects.length) : undefined}
        />
      )}
      {panel?.view === "object" && (() => {
        const objects = panel.cluster.objects;
        const index = objects.findIndex((o) => o.objectID === panel.object.objectID);
        const clusterPosition = index >= 0 ? { index: index + 1, total: objects.length } : undefined;
        return (
          <ObjectDetail
            object={panel.object}
            museums={bundle.museums}
            lang={lang}
            onBack={() => setPanel({ view: "cluster", cluster: panel.cluster, kind: panel.kind })}
            onClose={() => setPanel(null)}
            clusterPosition={clusterPosition}
            onPrev={index > 0 ? () => selectClusterObject(index - 1) : undefined}
            onNext={index >= 0 && index < objects.length - 1 ? () => selectClusterObject(index + 1) : undefined}
          />
        );
      })()}
    </div>
  );
}

export default App;
