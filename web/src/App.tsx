import { useState, useCallback, useMemo, useEffect } from "react";
import Map, { Source, Layer, Popup } from "react-map-gl/mapbox";
import type { MapMouseEvent } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import data from "./data/objects.json";
import type { DataBundle, MuseumObject } from "./types";
import { groupByOrigin, jitteredPoint, type OriginCluster } from "./geo";
import { ClusterPanel } from "./components/ClusterPanel";
import { ObjectDetail } from "./components/ObjectDetail";
import { Timeline } from "./components/Timeline";
import "./App.css";

const TIMELINE_MIN_YEAR = 1700;
const TIMELINE_MAX_YEAR = 2020;
const TIMELINE_DEFAULT_YEAR = 1920;

// Se sirve desde public/ y se pide con fetch() recién cuando el usuario activa
// la capa (en vez de bundlearlo con ?raw) porque el geojson del timeline
// completo (todas las décadas) pesa varios MB — inlinearlo en el JS del build
// infla el bundle principal innecesariamente para quien nunca prende la capa.
const COLONIAL_OVERLAY_URL = `${import.meta.env.BASE_URL}colonial_overlay.geojson`;

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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- geojson global type no está disponible, ver nota de colonialOverlay más arriba
  const [colonialOverlay, setColonialOverlay] = useState<any>(null);

  useEffect(() => {
    if (!timelineOpen || colonialOverlay) return;
    fetch(COLONIAL_OVERLAY_URL)
      .then((res) => res.json())
      .then(setColonialOverlay)
      .catch((err) => console.error("No se pudo cargar colonial_overlay.geojson", err));
  }, [timelineOpen, colonialOverlay]);

  const toggleMuseum = useCallback((id: string) => {
    setVisibleMuseums((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  const visibleObjects = useMemo(
    () => bundle.objects.filter((obj) => obj.sourceMuseum && visibleMuseums[obj.sourceMuseum]),
    [visibleMuseums],
  );

  const clusters = useMemo(() => groupByOrigin(visibleObjects), [visibleObjects]);

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

  const handleMouseMove = useCallback((e: MapMouseEvent) => {
    if (e.features?.length) {
      const f = e.features[0] as unknown as { layer?: { id?: string }; properties?: Record<string, string | number | undefined> };
      const properties = f.properties ?? {};
      const text = f.layer?.id === "origins"
        ? `${properties.label} — ${properties.count} pieza(s) (click para el detalle)`
        : `${properties.name} (${properties.city})`;
      setTooltip({ longitude: e.lngLat.lng, latitude: e.lngLat.lat, text });
      setCursor("pointer");
    } else {
      setTooltip(null);
      setCursor("grab");
    }
  }, []);

  return (
    <div className="app-layout">
      <div className="map-pane">
        <div className="museum-toggles">
          {Object.entries(bundle.museums).map(([id, m]) => (
            <button
              key={id}
              type="button"
              className={`museum-toggle${visibleMuseums[id] ? " active" : " inactive"}`}
              onClick={() => toggleMuseum(id)}
            >
              <span
                className="museum-toggle-dot"
                style={{ background: MUSEUM_COLORS[id] ?? DEFAULT_COLOR }}
              />
              {m.name}
            </button>
          ))}
          <div className="piece-counter">
            {visibleObjects.length === bundle.objects.length
              ? `${visibleObjects.length} piezas`
              : `${visibleObjects.length} de ${bundle.objects.length} piezas`}
          </div>
        </div>
        <div className="curated-note" style={{ bottom: timelineOpen ? 92 : 12 }}>
          Muestra curada — no representa la colección completa de cada museo. Muchas piezas quedan fuera.
          {timelineOpen && (
            <>
              {" "}Territorios coloniales: Seshat Global History Databank —{" "}
              <a href="https://github.com/Seshat-Global-History-Databank/cliopatria" target="_blank" rel="noreferrer">
                Cliopatria
              </a>{" "}(CC-BY 4.0).
            </>
          )}
        </div>
        <Map
          mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
          initialViewState={{ longitude: 10, latitude: 20, zoom: 2 }}
          style={{ width: "100%", height: "100%" }}
          mapStyle="mapbox://styles/mapbox/light-v11"
          projection="globe"
          fog={{}}
          interactiveLayerIds={["origins", "museums"]}
          cursor={cursor}
          onClick={handleClick}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { setTooltip(null); setCursor("grab"); }}
        >
          {timelineOpen && colonialOverlay && (
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
            Territorios coloniales
          </button>
          {timelineOpen && (
            <Timeline
              minYear={TIMELINE_MIN_YEAR}
              maxYear={TIMELINE_MAX_YEAR}
              year={timelineYear}
              onChange={setTimelineYear}
              legend={[
                { label: "Imperio colonial británico", color: COLONIAL_POWER_COLORS.uk },
                { label: "Imperio colonial francés", color: COLONIAL_POWER_COLORS.fr },
              ]}
            />
          )}
        </div>
      </div>

      {panel?.view === "cluster" && (
        <ClusterPanel
          cluster={panel.cluster}
          onClose={() => setPanel(null)}
          onSelectObject={(object) => setPanel({ view: "object", cluster: panel.cluster, object })}
        />
      )}
      {panel?.view === "object" && (
        <ObjectDetail
          object={panel.object}
          museums={bundle.museums}
          onBack={() => setPanel({ view: "cluster", cluster: panel.cluster })}
          onClose={() => setPanel(null)}
        />
      )}
    </div>
  );
}

export default App;
