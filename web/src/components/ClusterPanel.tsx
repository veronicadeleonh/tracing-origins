import type { MuseumObject } from "../types";
import type { OriginCluster } from "../geo";
import { STRINGS, type Lang } from "../i18n";

interface ClusterPanelProps {
  cluster: OriginCluster;
  lang: Lang;
  onClose: () => void;
  onSelectObject: (object: MuseumObject) => void;
}

export function ClusterPanel({ cluster, lang, onClose, onSelectObject }: ClusterPanelProps) {
  const s = STRINGS[lang];
  return (
    <aside className="side-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">{cluster.label || s.clusterUnknownOrigin}</div>
          <div className="panel-subtitle">{s.clusterPieceCount(cluster.objects.length)}</div>
        </div>
        <button className="icon-btn" onClick={onClose} aria-label={s.closePanelAria}>
          ×
        </button>
      </div>

      <div className="piece-list">
        {cluster.objects.map((obj) => (
          <button
            key={obj.objectID}
            type="button"
            className="piece-row"
            onClick={() => onSelectObject(obj)}
          >
            <div
              className="piece-thumb"
              style={obj.primaryImage ? { backgroundImage: `url(${obj.primaryImage})` } : undefined}
            />
            <div className="piece-info">
              <div className="piece-title">{obj.title || s.untitled}</div>
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
