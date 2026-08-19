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

  const renderPieceRow = (obj: MuseumObject) => {
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
              // Búsqueda por país: el museo ya queda identificado por el
              // encabezado del grupo (ver abajo), así que acá alcanza con
              // el sitio de origen puntual -- mostrar el museo dos veces
              // sería redundante.
              ? (lang === "en" ? obj.originLabelEn || obj.originLabel : obj.originLabel)
              : [obj.culture, obj.period, obj.objectDate].filter(Boolean).join(" · ")}
          </div>
        </div>
        <span className="chevron" aria-hidden="true">
          ›
        </span>
      </button>
    );
  };

  // Búsqueda por país (19/08, tercera vuelta: agrupar por museo a pedido de
  // la usuaria): a diferencia de un cluster de origen (todas las piezas del
  // mismo museo o mezcladas sin ningún orden temático), un resultado de país
  // agrupa mejor separado por museo -- el orden de los grupos sigue el orden
  // de `museums` (mismo orden que los toggles de museo en App.tsx: Met,
  // Louvre, BM), no el orden alfabético que da ordenar por objectID.
  const museumGroups = showOriginAndMuseum && museums
    ? Object.keys(museums)
        .map((id) => ({
          id,
          name: museums[id]?.name ?? id,
          objects: cluster.objects.filter((o) => o.sourceMuseum === id),
        }))
        .filter((g) => g.objects.length > 0)
    : null;

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

      {museumGroups ? (
        museumGroups.map((group) => (
          <div key={group.id} className="piece-list-museum-group">
            <div className="piece-list-museum-header">
              {s.countryGroupMuseumHeader(group.name, group.objects.length)}
            </div>
            <div className="piece-list">{group.objects.map(renderPieceRow)}</div>
          </div>
        ))
      ) : (
        <div className="piece-list">{cluster.objects.map(renderPieceRow)}</div>
      )}
    </aside>
  );
}
