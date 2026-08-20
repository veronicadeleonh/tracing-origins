import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import Map, { Source, Layer, Popup } from "react-map-gl/mapbox";
import type { MapMouseEvent } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import data from "./data/objects.json";
import type { DataBundle, MuseumObject } from "./types";
import { groupByCountry, groupByOrigin, jitteredPoint, objectHasResearch, type OriginCluster } from "./geo";
import { MUSEUM_COLORS, DEFAULT_COLOR, ORIGIN_COLOR } from "./colors";
import { ClusterPanel } from "./components/ClusterPanel";
import { ObjectDetail } from "./components/ObjectDetail";
import { Timeline } from "./components/Timeline";
import { WelcomeModal } from "./components/WelcomeModal";
import { HISTORICAL_EVENTS } from "./data/historicalEvents";
import { NATURAL_EARTH_NAME_TO_COUNTRY_KEY } from "./data/countryPolygons";
import { STRINGS, type Lang } from "./i18n";
import "./App.css";

// Nivel 1 de "notas de contexto en la UI" (ver CLAUDE.md) — se abre solo en
// la primera visita, después queda accesible vía el botón "?" persistente.
const WELCOME_SEEN_KEY = "tracing-origins-welcome-seen";
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

const bundle = data as DataBundle;

// mismo color que cada museo, para reforzar la conexión territorio-colonial
// -> museo que se benefició de él. UK = BM (rojo), Francia = Louvre (teal).
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
type TooltipState = { longitude: number; latitude: number; title: string; subtitle: string } | null;

function App() {
  const [visibleMuseums, setVisibleMuseums] = useState<Record<string, boolean>>(
    () => Object.fromEntries(Object.keys(bundle.museums).map((id) => [id, true])),
  );
  // Filtro por estado de investigación (18/08, pedido explícito de la
  // usuaria junto con el tratamiento visual de context_flags): además de
  // marcar qué piezas tienen layer 3, dejar ocultar/mostrar según eso.
  // "all" es el default — no cambia el comportamiento previo.
  const [researchFilter, setResearchFilter] = useState<"all" | "with" | "without">("all");
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
  // Auto-abre en la primera visita (localStorage), después solo vía el botón
  // "?" — decidido con el usuario el 17/08 (no molestar en visitas siguientes).
  const [welcomeOpen, setWelcomeOpen] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem(WELCOME_SEEN_KEY)) setWelcomeOpen(true);
  }, []);
  const closeWelcome = useCallback(() => {
    localStorage.setItem(WELCOME_SEEN_KEY, "1");
    setWelcomeOpen(false);
  }, []);
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
        if (researchFilter === "with") return objectHasResearch(obj);
        if (researchFilter === "without") return !objectHasResearch(obj);
        return true;
      }),
    [visibleMuseums, researchFilter],
  );

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

  const selectCountryGroup = useCallback((group: { label: string; objects: MuseumObject[] }) => {
    setPanel({ view: "cluster", cluster: { lat: 0, lon: 0, label: group.label, objects: group.objects }, kind: "country" });
  }, []);

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
      if (f.layer?.id === "origins") {
        title = String(properties.label);
        subtitle = s.tooltipPieceCount(Number(properties.count));
      } else if (f.layer?.id === "country-hit") {
        // Mismo lookup que handleClick, pero en hover: avisa de antemano si
        // ese país no tiene piezas en la muestra, para que el click (o la
        // falta de reacción al click) no sorprenda a nadie.
        const naturalEarthName = String(properties.name ?? "");
        const key = NATURAL_EARTH_NAME_TO_COUNTRY_KEY[naturalEarthName];
        const group = key ? countryGroups.find((g) => g.key === key) : undefined;
        title = group?.label ?? naturalEarthName;
        subtitle = group && group.objects.length > 0
          ? s.tooltipPieceCount(group.objects.length)
          : s.tooltipCountryEmptySub;
      } else {
        title = String(properties.name);
        subtitle = String(properties.city);
      }
      setTooltip({ longitude: e.lngLat.lng, latitude: e.lngLat.lat, title, subtitle });
      setCursor("pointer");
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
        {welcomeOpen && <WelcomeModal lang={lang} onToggleLang={toggleLang} onClose={closeWelcome} />}
        <div className="top-controls">
        <div className="museum-toggles">
          <span className="filter-row-label">{s.museumFilterRowLabel}</span>
          {Object.entries(bundle.museums).map(([id, m]) => (
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
          <div className="piece-counter">
            {visibleObjects.length === bundle.objects.length
              ? s.pieceCounterAll(visibleObjects.length)
              : s.pieceCounterFiltered(visibleObjects.length, bundle.objects.length)}
          </div>
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
                onClick={() => setResearchFilter(value)}
              >
                {s.researchFilterLabels[value]}
              </button>
            ))}
          </div>
        </div>
        </div>
        <Map
          ref={mapRef}
          mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
          initialViewState={{ longitude: 10, latitude: 20, zoom: 2 }}
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
              className="map-tooltip-popup"
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
