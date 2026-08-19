import type { MuseumDestination, MuseumObject } from "../types";
import { objectHasResearch, type OriginCluster } from "../geo";
import { MUSEUM_COLORS, DEFAULT_COLOR } from "../colors";
import { STRINGS, type Lang } from "../i18n";

interface ClusterPanelProps {
  cluster: OriginCluster;
  lang: Lang;
  onClose: () => void;
  onSelectObject: (object: MuseumObject) => void;
  // Búsqueda por país (19/08): a diferencia de un cluster de origen (todas
  // las piezas comparten el mismo punto, ya mostrado en el título), un
  // resultado de país puede mezclar sitios/museos distintos — estas dos
  // props opcionales activan una segunda línea por fila con el origen
  // puntual y el museo, y permiten pisar el subtítulo default ("N piezas de
  // este lugar", que no aplica acá). Sin ellas el componente se comporta
  // exactamente igual que antes.
  showOriginAndMuseum?: boolean;
  museums?: Record<string, MuseumDestination>;
  subtitleOverride?: string;
}

export function ClusterPanel({ cluster, lang, onClose, onSelectObject, showOriginAndMuseum, museums, subtitleOverride }: ClusterPanelProps) {
  const s = STRINGS[lang];
  // Tratamiento narrativo de context_flags (18/08, segunda vuelta): la
  // leyenda solo se muestra si al menos una pieza de este cluster tiene
  // investigación — si ninguna la tiene, explicar el marcador no aporta
  // nada acá. El badge ya no usa un color de acento fijo: reusa el color
  // del museo dueño de cada pieza (ver colors.ts) para reforzar el mismo
  // lenguaje visual que el toggle de museo y las líneas del mapa, en vez de
  // competir con un color nuevo (feedback de la usuaria sobre la primera
  // versión, que usaba un violeta genérico).
  const anyResearch = cluster.objects.some(objectHasResearch);
  return (
    <aside className="side-panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">{cluster.label || s.clusterUnknownOrigin}</div>
          <div className="panel-subtitle">{subtitleOverride ?? s.clusterPieceCount(cluster.objects.length)}</div>
        </div>
        <button className="icon-btn" onClick={onClose} aria-label={s.closePanelAria}>
          ×
        </button>
      </div>

      {anyResearch && (
        <div className="piece-list-legend">
          <span className="piece-list-legend-dot" aria-hidden="true">●</span> {s.hasResearchLegend}
        </div>
      )}

      <div className="piece-list">
        {cluster.objects.map((obj) => {
          const hasResearch = objectHasResearch(obj);
          const badgeColor = MUSEUM_COLORS[obj.sourceMuseum ?? ""] ?? DEFAULT_COLOR;
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
                    style={{ background: badgeColor }}
                    role="img"
                    aria-label={s.hasResearchBadgeAria}
                    title={s.hasResearchBadgeAria}
                  />
                )}
              </div>
              <div className="piece-info">
                <div className="piece-title">{obj.title || s.untitled}</div>
                <div className="piece-sub">
                  {showOriginAndMuseum
                    ? [
                        lang === "en" ? obj.originLabelEn || obj.originLabel : obj.originLabel,
                        obj.sourceMuseum ? museums?.[obj.sourceMuseum]?.name : undefined,
                      ].filter(Boolean).join(" · ")
                    : [obj.culture, obj.period, obj.objectDate].filter(Boolean).join(" · ")}
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
