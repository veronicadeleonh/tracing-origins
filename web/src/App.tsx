import { useState, useCallback, useMemo } from "react";
import Map, { Source, Layer, Popup } from "react-map-gl/mapbox";
import type { MapMouseEvent } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import data from "./data/objects.json";
import type { DataBundle, MuseumObject } from "./types";
import { groupByOrigin, jitteredPoint, type OriginCluster } from "./geo";
import { ClusterPanel } from "./components/ClusterPanel";
import { ObjectDetail } from "./components/ObjectDetail";
import "./App.css";

const bundle = data as DataBundle;

const MUSEUM_COLOR = "#b23a48";
const LINE_COLOR = "#c9a227";

type PanelState =
  | { view: "cluster"; cluster: OriginCluster }
  | { view: "object"; cluster: OriginCluster; object: MuseumObject }
  | null;

type TooltipState = { longitude: number; latitude: number; text: string } | null;

function App() {
  const clusters = useMemo(() => groupByOrigin(bundle.objects), []);
  const [panel, setPanel] = useState<PanelState>(null);
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const [cursor, setCursor] = useState("grab");

  const linesGeoJSON = useMemo(() => ({
    type: "FeatureCollection" as const,
    features: clusters.flatMap((cluster) =>
      cluster.objects.flatMap((obj, i) => {
        const dest = obj.sourceMuseum ? bundle.museums[obj.sourceMuseum] : undefined;
        if (!dest) return [];
        const [jLat, jLon] = jitteredPoint(cluster.lat, cluster.lon, i, cluster.objects.length);
        return [{
          type: "Feature" as const,
          geometry: { type: "LineString" as const, coordinates: [[jLon, jLat], [dest.lon, dest.lat]] },
          properties: { objectID: obj.objectID },
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
    features: Object.entries(bundle.museums).map(([id, m]) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [m.lon, m.lat] },
      properties: { id, name: m.name, city: m.city },
    })),
  }), []);

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
        <div className="curated-note">
          Muestra curada — no representa la colección completa de cada museo. Muchas piezas quedan fuera.
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
          <Source id="lines" type="geojson" data={linesGeoJSON}>
            <Layer
              id="lines"
              type="line"
              paint={{ "line-color": LINE_COLOR, "line-width": 1.4, "line-opacity": 0.55 }}
            />
          </Source>
          <Source id="origins-src" type="geojson" data={originsGeoJSON}>
            <Layer
              id="origins"
              type="circle"
              paint={{
                "circle-color": LINE_COLOR,
                "circle-opacity": 0.85,
                "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 5, 10, 14],
              }}
            />
          </Source>
          <Source id="museums-src" type="geojson" data={museumsGeoJSON}>
            <Layer
              id="museums"
              type="circle"
              paint={{ "circle-color": MUSEUM_COLOR, "circle-radius": 9, "circle-opacity": 1 }}
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
          onBack={() => setPanel({ view: "cluster", cluster: panel.cluster })}
          onClose={() => setPanel(null)}
        />
      )}
    </div>
  );
}

export default App;
