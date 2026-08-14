import { useState } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import data from "./data/objects.json";
import type { DataBundle, MuseumObject } from "./types";
import { groupByOrigin, jitteredPoint, type OriginCluster } from "./geo";
import { ClusterPanel } from "./components/ClusterPanel";
import { ObjectDetail } from "./components/ObjectDetail";
import { ResizeHandler } from "./components/ResizeHandler";
import "./App.css";

const bundle = data as DataBundle;

const MUSEUM_COLOR = "#b23a48";
const LINE_COLOR = "#c9a227";

type PanelState =
  | { view: "cluster"; cluster: OriginCluster }
  | { view: "object"; cluster: OriginCluster; object: MuseumObject }
  | null;

function App() {
  const clusters = groupByOrigin(bundle.objects);
  const [panel, setPanel] = useState<PanelState>(null);

  return (
    <div className="app-layout">
      <div className="map-pane">
        <div className="curated-note">
          Muestra curada — no representa la colección completa de cada museo. Muchas piezas quedan fuera.
        </div>

        <MapContainer
          center={[20, 10]}
          zoom={2}
          minZoom={2}
          worldCopyJump
          style={{ height: "100%", width: "100%" }}
        >
          <ResizeHandler trigger={panel !== null} />

          <TileLayer
            url="https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png"
            attribution="&copy; OpenStreetMap contributors &copy; CARTO"
          />

          {Object.entries(bundle.museums).map(([museumId, museum]) => (
            <CircleMarker
              key={museumId}
              center={[museum.lat, museum.lon]}
              radius={9}
              pathOptions={{ color: MUSEUM_COLOR, fillColor: MUSEUM_COLOR, fillOpacity: 1 }}
            >
              <Tooltip>
                {museum.name} ({museum.city})
              </Tooltip>
            </CircleMarker>
          ))}

          {clusters.map((cluster) => {
            const key = `${cluster.lat}|${cluster.lon}|${cluster.label}`;
            return (
              <div key={key}>
                {cluster.objects.map((obj, i) => {
                  const [jLat, jLon] = jitteredPoint(cluster.lat, cluster.lon, i, cluster.objects.length);
                  const dest = obj.sourceMuseum ? bundle.museums[obj.sourceMuseum] : undefined;
                  if (!dest) return null;
                  return (
                    <Polyline
                      key={obj.objectID}
                      positions={[
                        [jLat, jLon],
                        [dest.lat, dest.lon],
                      ]}
                      pathOptions={{ color: LINE_COLOR, weight: 1.4, opacity: 0.55 }}
                    />
                  );
                })}

                <CircleMarker
                  center={[cluster.lat, cluster.lon]}
                  radius={4 + Math.min(cluster.objects.length, 10)}
                  pathOptions={{ color: LINE_COLOR, fillColor: LINE_COLOR, fillOpacity: 0.85 }}
                  eventHandlers={{ click: () => setPanel({ view: "cluster", cluster }) }}
                >
                  <Tooltip>
                    {cluster.label} — {cluster.objects.length} pieza(s) (click para el detalle)
                  </Tooltip>
                </CircleMarker>
              </div>
            );
          })}
        </MapContainer>
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
