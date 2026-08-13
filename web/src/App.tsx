import { useState } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import data from "./data/objects.json";
import type { DataBundle } from "./types";
import { groupByOrigin, jitteredPoint, type OriginCluster } from "./geo";
import { ClusterPanel } from "./components/ClusterPanel";
import { ResizeHandler } from "./components/ResizeHandler";
import "./App.css";

const bundle = data as DataBundle;

const MET_COLOR = "#b23a48";
const LINE_COLOR = "#c9a227";

function App() {
  const clusters = groupByOrigin(bundle.objects);
  const [selectedCluster, setSelectedCluster] = useState<OriginCluster | null>(null);

  return (
    <div className="app-layout">
      <div className="map-pane">
        <MapContainer
          center={[20, 10]}
          zoom={2}
          minZoom={2}
          worldCopyJump
          style={{ height: "100%", width: "100%" }}
        >
          <ResizeHandler trigger={selectedCluster} />

          <TileLayer
            url="https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png"
            attribution="&copy; OpenStreetMap contributors &copy; CARTO"
          />

          <CircleMarker
            center={[bundle.met.lat, bundle.met.lon]}
            radius={9}
            pathOptions={{ color: MET_COLOR, fillColor: MET_COLOR, fillOpacity: 1 }}
          >
            <Tooltip>
              {bundle.met.name} ({bundle.met.city})
            </Tooltip>
          </CircleMarker>

          {clusters.map((cluster) => {
            const key = `${cluster.lat}|${cluster.lon}|${cluster.label}`;
            return (
              <div key={key}>
                {cluster.objects.map((obj, i) => {
                  const [jLat, jLon] = jitteredPoint(cluster.lat, cluster.lon, i, cluster.objects.length);
                  return (
                    <Polyline
                      key={obj.objectID}
                      positions={[
                        [jLat, jLon],
                        [bundle.met.lat, bundle.met.lon],
                      ]}
                      pathOptions={{ color: LINE_COLOR, weight: 1.4, opacity: 0.55 }}
                    />
                  );
                })}

                <CircleMarker
                  center={[cluster.lat, cluster.lon]}
                  radius={4 + Math.min(cluster.objects.length, 10)}
                  pathOptions={{ color: LINE_COLOR, fillColor: LINE_COLOR, fillOpacity: 0.85 }}
                  eventHandlers={{ click: () => setSelectedCluster(cluster) }}
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

      {selectedCluster && (
        <ClusterPanel cluster={selectedCluster} onClose={() => setSelectedCluster(null)} />
      )}
    </div>
  );
}

export default App;
