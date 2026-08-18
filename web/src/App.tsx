import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import Map, { Source, Layer, Popup } from "react-map-gl/mapbox";
import type { MapMouseEvent } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import data from "./data/objects.json";
import type { DataBundle, MuseumObject } from "./types";
import { groupByOrigin, jitteredPoint, type OriginCluster } from "./geo";
import { ClusterPanel } from "./components/ClusterPanel";
import { ObjectDetail } from "./components/ObjectDetail";
import { Timeline } from "./components/Timeline";
import { WelcomeModal } from "./components/WelcomeModal";
import { HISTORICAL_EVENTS } from "./data/historicalEvents";
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

const bundle = data as DataBundle;

const MUSEUM_COLORS: Record<string, string> = {
  met: "#c9a227",
  louvre: "#3d7a8c",
  bm: "#b23a48",
};
const DEFAULT_COLOR = "#928d82";
const ORIGIN_COLOR = "#8a8478";
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

type PanelState =
  | { view: "cluster"; cluster: OriginCluster }
  | { view: "object"; cluster: OriginCluster; object: MuseumObject }
  | null;

type TooltipState = { longitude: number; latitude: number; text: string } | null;

function App() {
  const [visibleMuseums, setVisibleMuseums] = useState<Record<string, boolean>>(
    () => Object.fromEntries(Object.keys(bundle.museums).map((id) => [id, true])),
  );
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
  // La nota "muestra curada" vivía anclada en una esquina del mapa (primero
  // bottom-left, después top-right) y en las dos terminaba tapada por algo
  // (el dock del timeline, el panel lateral) — pasa a un botón "i" en la
  // fila de arriba, mismo patrón que MUSEUM_NOTES, inmune a qué esté abierto
  // en el resto de la pantalla. Mismo contenido que va a alimentar el modal
  // de bienvenida (nivel 1 de "notas de contexto en la UI", ver CLAUDE.md)
  // cuando se implemente — por ahora es un popover simple.
  const [curatedNoteOpen, setCuratedNoteOpen] = useState(false);
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
  const [lang, setLang] = useState<Lang>(() => (localStorage.getItem(LANG_KEY) === "en" ? "en" : "es"));
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

  const visibleObjects = useMemo(
    () => bundle.objects.filter((obj) => obj.sourceMuseum && visibleMuseums[obj.sourceMuseum]),
    [visibleMuseums],
  );

  const clusters = useMemo(() => groupByOrigin(visibleObjects, lang), [visibleObjects, lang]);

  const linesGeoJSON = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: clusters.flatMap((cluster) =>
      cluster.objects.flatMap((obj, i) => {
        const dest = obj.sourceMuseum ? bundle.museums[obj.sourceMuseum] : undefined;
        if (!dest) return [];
        const [jLat, jLon] = jitteredPoint(cluster.lat, cluster.lon, i, cluster.objects.length);
        const color = (obj.sourceMuseum && MUSEUM_COLORS[obj.sourceMuseum]) || DEFAULT_COLOR;
        return [{
          type: "Feature" as const,
          geometry: { type: "LineString" as const, coordinates: [[jLon, jLat], [dest.lon, dest.lat]] },
          properties: { objectID: obj.objectID, color },
        }];
      })
    ),
  }), [clusters]);

  const originsGeoJSON = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: clusters.map((cluster) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [cluster.lon, cluster.lat] },
      properties: {
        label: cluster.label,
        count: cluster.objects.length,
        clusterKey: `${cluster.lat}|${cluster.lon}|${cluster.label}`,
      },
    })),
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

  const handleClick = useCallback((e: MapMouseEvent) => {
    if (!e.features?.length) return;
    const f = e.features[0] as unknown as { layer?: { id?: string }; properties?: Record<string, string | number | undefined> };
    const properties = f.properties ?? {};
    if (f.layer?.id === "origins") {
      const key = properties.clusterKey as string;
      const cluster = clusters.find((c) => `${c.lat}|${c.lon}|${c.label}` === key);
      if (cluster) setPanel({ view: "cluster", cluster });
    }
  }, [clusters]);

  // Navegación prev/next dentro de un cluster de origen (18/08) — update
  // funcional para no depender de `panel` en las deps del callback (evita
  // handlers con closures viejas si el usuario navega rápido). Sirve tanto
  // para prev como para next: solo cambia qué índice le pasan los botones.
  const selectClusterObject = useCallback((index: number) => {
    setPanel((prev) => {
      if (!prev) return prev;
      const object = prev.cluster.objects[index];
      if (!object) return prev;
      return { view: "object", cluster: prev.cluster, object };
    });
  }, []);

  const handleMouseMove = useCallback((e: MapMouseEvent) => {
    if (e.features?.length) {
      const f = e.features[0] as unknown as { layer?: { id?: string }; properties?: Record<string, string | number | undefined> };
      const properties = f.properties ?? {};
      const text = f.layer?.id === "origins"
        ? s.tooltipOrigin(String(properties.label), Number(properties.count))
        : `${properties.name} (${properties.city})`;
      setTooltip({ longitude: e.lngLat.lng, latitude: e.lngLat.lat, text });
      setCursor("pointer");
    } else {
      setTooltip(null);
      setCursor("grab");
    }
  }, [s]);

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
        {welcomeOpen && <WelcomeModal lang={lang} onToggleLang={toggleLang} onClose={closeWelcome} />}
        <div className="museum-toggles">
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
          <div className="curated-note-wrap">
            <button
              type="button"
              className={`curated-note-btn${curatedNoteOpen ? " open" : ""}`}
              aria-label={s.curatedNoteBtnAria}
              aria-expanded={curatedNoteOpen}
              onClick={() => setCuratedNoteOpen((v) => !v)}
            >
              i
            </button>
            {curatedNoteOpen && (
              <div className="curated-note">
                {s.curatedNoteText} {s.curatedNoteResearch} {s.curatedNoteBasemap}
                {timelineOpen && showTerritories && (
                  <>
                    {" "}{s.curatedNoteTerritoriesPrefix}{" "}
                    <a href="https://github.com/Seshat-Global-History-Databank/cliopatria" target="_blank" rel="noreferrer">
                      Cliopatria
                    </a>{" "}{s.curatedNoteTerritoriesLicense}
                  </>
                )}
                {timelineOpen && showRoutes && (
                  <>
                    {" "}{s.curatedNoteRoutesPrefix}{" "}
                    <a href="https://doi.org/10.1594/PANGAEA.611088" target="_blank" rel="noreferrer">
                      CLIWOC
                    </a>{" "}{s.curatedNoteRoutesSuffix}
                  </>
                )}
              </div>
            )}
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
          interactiveLayerIds={["origins", "museums"]}
          cursor={cursor}
          onLoad={handleMapLoad}
          onClick={handleClick}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { setTooltip(null); setCursor("grab"); }}
        >
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
              paint={{ "line-color": ["get", "color"], "line-width": 1.4, "line-opacity": 0.55 }}
            />
          </Source>
          <Source id="origins-src" type="geojson" data={originsGeoJSON}>
            <Layer
              id="origins"
              type="circle"
              paint={{
                "circle-color": ORIGIN_COLOR,
                "circle-opacity": 0.85,
                "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 5, 10, 14],
              }}
            />
          </Source>
          <Source id="museums-src" type="geojson" data={museumsGeoJSON}>
            <Layer
              id="museums"
              type="circle"
              paint={{ "circle-color": ["get", "color"], "circle-radius": 9, "circle-opacity": 1 }}
            />
          </Source>
          {tooltip && (
            <Popup
              longitude={tooltip.longitude}
              latitude={tooltip.latitude}
              closeButton={false}
              anchor="bottom"
              style={{ pointerEvents: "none" }}
            >
              {tooltip.text}
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
          onSelectObject={(object) => setPanel({ view: "object", cluster: panel.cluster, object })}
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
            onBack={() => setPanel({ view: "cluster", cluster: panel.cluster })}
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
