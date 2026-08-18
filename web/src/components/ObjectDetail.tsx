import type { MuseumDestination, MuseumObject, ProvenanceEvent } from "../types";
import { museumColor } from "../colors";
import { STRINGS, type Lang } from "../i18n";

interface ObjectDetailProps {
  object: MuseumObject;
  museums: Record<string, MuseumDestination>;
  lang: Lang;
  onBack: () => void;
  onClose: () => void;
  // Navegación entre piezas del mismo cluster de origen (18/08) — evita tener
  // que volver al ClusterPanel para pasar a la siguiente pieza del lugar.
  // Opcionales porque ObjectDetail no depende de tener un cluster para
  // funcionar (en teoría podría reusarse desde otro punto de entrada) — sin
  // ellos, o con clusterPosition.total <= 1, la barra de navegación no se
  // muestra.
  clusterPosition?: { index: number; total: number };
  onPrev?: () => void;
  onNext?: () => void;
}

function eventLabel(event: ProvenanceEvent, s: (typeof STRINGS)["es"]): string {
  if (!event.event_type) return s.eventFallback;
  return s.eventTypeLabels[event.event_type] ?? event.event_type;
}

export function ObjectDetail({
  object,
  museums,
  lang,
  onBack,
  onClose,
  clusterPosition,
  onPrev,
  onNext,
}: ObjectDetailProps) {
  const s = STRINGS[lang];
  const events = object.events;
  const flags = object.context?.context_flags ?? [];
  // Layer 3 (investigación propia) ahora tiene traducción EN además de la
  // ES original (17/08) — se elige según el toggle, con fallback al campo
  // base por si algún registro viejo todavía no tiene su par traducido.
  const notes = lang === "en" ? object.context?.notesEn || object.context?.notes : object.context?.notes;
  const hasResearch = events.length > 0 || flags.length > 0 || !!notes;
  const destMuseum = object.sourceMuseum ? museums[object.sourceMuseum] : undefined;
  // Tratamiento narrativo de context_flags (18/08, segunda vuelta): los
  // puntos "evento investigado" y "ahora, en el museo" usan el color del
  // museo dueño de la pieza (ver colors.ts) en vez de un acento genérico
  // (violeta) o un rojo fijo que no correspondía al museo real — mismo
  // lenguaje visual que el toggle de museo y las líneas del mapa.
  const accentColor = museumColor(object.sourceMuseum);
  const originLabel = lang === "en" ? object.originLabelEn || object.originLabel : object.originLabel;

  const subtitle = [object.culture, object.period, object.objectDate].filter(Boolean).join(" · ");
  const museumFields = [
    object.medium ? `${s.mediumPrefix}${object.medium}` : null,
    object.creditLine,
    object.accessionYear ? `${s.accessionYearPrefix}${object.accessionYear}` : null,
  ].filter(Boolean) as string[];

  return (
    <aside className="side-panel">
      <div className="panel-header">
        <button className="icon-btn" onClick={onBack} aria-label={s.backAria}>
          ‹
        </button>
        <button className="icon-btn" onClick={onClose} aria-label={s.closePanelAria}>
          ×
        </button>
      </div>

      <div className="object-header">
        {object.primaryImage && <img className="object-image" src={object.primaryImage} alt="" />}
        <div className="object-title">{object.title || s.untitled}</div>
        {subtitle && <div className="object-subtitle">{subtitle}</div>}
      </div>

      <div className="timeline">
        <div className="timeline-node">
          <span className="timeline-dot timeline-dot-muted" aria-hidden="true" />
          <div className="timeline-date">{object.objectDate || s.originFallbackDate}</div>
          <div className="timeline-label">{s.madeIn(originLabel || s.unknownPlace)}</div>
        </div>

        {hasResearch ? (
          <>
            {flags.length > 0 && (
              <div className="context-flags">
                {flags.map((flag) => (
                  <span key={flag} className="context-flag">
                    {flag}
                  </span>
                ))}
              </div>
            )}
            {notes && <div className="context-notes">{notes}</div>}
            {events.map((event, i) => {
              const description = lang === "en"
                ? event.descriptionEn || event.descriptionEs || event.description
                : event.descriptionEs || event.description;
              return (
                <div className="timeline-node" key={i}>
                  <span className="timeline-dot" style={{ background: accentColor }} aria-hidden="true" />
                  <div className="timeline-date">{event.event_date || ""}</div>
                  <div className="timeline-label">{eventLabel(event, s)}</div>
                  {description && <div className="timeline-desc">{description}</div>}
                </div>
              );
            })}
          </>
        ) : (
          <div className="timeline-note">
            <span className="timeline-note-dot" aria-hidden="true" />
            {s.noResearch}
          </div>
        )}

        <div className="timeline-node">
          <span className="timeline-dot" style={{ background: accentColor }} aria-hidden="true" />
          <div className="timeline-date">{s.now}</div>
          <div className="timeline-label">
            {destMuseum ? `${destMuseum.name}, ${destMuseum.city}` : s.unknownMuseum}
          </div>
        </div>
      </div>

      {(museumFields.length > 0 || object.objectURL) && (
        <div className="museum-record">
          <div className="museum-record-label">{s.museumRecordLabel}</div>
          {museumFields.map((field, i) => (
            <div className="museum-record-field" key={i}>
              {field}
            </div>
          ))}
          {object.objectURL && (
            <a className="met-link" href={object.objectURL} target="_blank" rel="noreferrer">
              {s.viewAt(destMuseum?.name ?? s.theMuseumWebsite)}
            </a>
          )}
        </div>
      )}

      {clusterPosition && clusterPosition.total > 1 && (
        <div className="piece-nav">
          <button
            type="button"
            className="piece-nav-btn"
            aria-label={s.prevPieceAria}
            disabled={clusterPosition.index <= 1}
            onClick={onPrev}
          >
            ‹ {s.piecePrevLabel}
          </button>
          <span className="piece-nav-position">
            {s.piecePosition(clusterPosition.index, clusterPosition.total)}
          </span>
          <button
            type="button"
            className="piece-nav-btn"
            aria-label={s.nextPieceAria}
            disabled={clusterPosition.index >= clusterPosition.total}
            onClick={onNext}
          >
            {s.pieceNextLabel} ›
          </button>
        </div>
      )}
    </aside>
  );
}
