import type { MuseumObject } from "../types";
import { objectHasResearch, type OriginCluster } from "../geo";
import { STRINGS, type Lang } from "../i18n";

interface ClusterPanelProps {
  cluster: OriginCluster;
  lang: Lang;
  onClose: () => void;
  onSelectObject: (object: MuseumObject) => void;
}

export function ClusterPanel({ cluster, lang, onClose, onSelectObject }: ClusterPanelProps) {
  const s = STRINGS[lang];
  // Tratamiento narrativo de context_flags (18/08): la leyenda del punto
  // dorado solo se muestra si al menos una pieza de este cluster lo tiene —
  // si ninguna tiene investigación, explicar el marcador no aporta nada acá.
  const anyResearch = cluster.objects.some(objectHasResearch);
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

      {anyResearch && (
        <div className="piece-list-legend">
          <span className="research-badge" aria-hidden="true" /> {s.hasResearchLegend}
        </div>
      )}

      <div className="piece-list">
        {cluster.objects.map((obj) => {
          const hasResearch = objectHasResearch(obj);
          return (
            <button
              key={obj.objectID}
              type="button"
              className="piece-row"
              onClick={() => onSelectObject(obj)}
            >
              <div
                className="piece-thumb"
                style={obj.primaryImage ? { backgroundImage: `url(${obj.primaryImage})` } : undefined}
              >
                {hasResearch && (
                  <span
                    className="research-badge research-badge-thumb"
                    role="img"
                    aria-label={s.hasResearchBadgeAria}
                    title={s.hasResearchBadgeAria}
                  />
                )}
              </div>
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
          );
        })}
      </div>
    </aside>
  );
}
