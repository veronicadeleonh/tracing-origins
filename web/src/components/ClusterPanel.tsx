import type { MuseumObject } from "../types";
import type { OriginCluster } from "../geo";

interface ClusterPanelProps {
  cluster: OriginCluster;
  onClose: () => void;
  // TODO(siguiente paso): wire esto al estado "object" del panel para pasar
  // al detalle/timeline de la pieza. Por ahora las filas todavía no navegan.
  onSelectObject?: (object: MuseumObject) => void;
}

export function ClusterPanel({ cluster, onClose, onSelectObject }: ClusterPanelProps) {
  return (
    <aside className="side-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">{cluster.label || "Origen sin identificar"}</div>
          <div className="panel-subtitle">
            {cluster.objects.length} pieza{cluster.objects.length === 1 ? "" : "s"} de este lugar
          </div>
        </div>
        <button className="icon-btn" onClick={onClose} aria-label="Cerrar panel">
          ×
        </button>
      </div>

      <div className="piece-list">
        {cluster.objects.map((obj) => (
          <button
            key={obj.objectID}
            type="button"
            className="piece-row"
            onClick={() => onSelectObject?.(obj)}
          >
            <div
              className="piece-thumb"
              style={obj.primaryImage ? { backgroundImage: `url(${obj.primaryImage})` } : undefined}
            />
            <div className="piece-info">
              <div className="piece-title">{obj.title || "(sin título)"}</div>
              <div className="piece-sub">
                {[obj.culture, obj.period, obj.objectDate].filter(Boolean).join(" · ")}
              </div>
            </div>
            <span className="chevron" aria-hidden="true">
              ›
            </span>
          </button>
        ))}
      </div>
    </aside>
  );
}
