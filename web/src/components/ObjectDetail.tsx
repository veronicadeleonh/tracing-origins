import type { MuseumDestination, MuseumObject, ProvenanceEvent } from "../types";
import { STRINGS, type Lang } from "../i18n";

interface ObjectDetailProps {
  object: MuseumObject;
  museums: Record<string, MuseumDestination>;
  lang: Lang;
  onBack: () => void;
  onClose: () => void;
}

function eventLabel(event: ProvenanceEvent, s: (typeof STRINGS)["es"]): string {
  if (!event.event_type) return s.eventFallback;
  return s.eventTypeLabels[event.event_type] ?? event.event_type;
}

export function ObjectDetail({ object, museums, lang, onBack, onClose }: ObjectDetailProps) {
  const s = STRINGS[lang];
  const events = object.events;
  const flags = object.context?.context_flags ?? [];
  // Layer 3 (investigación propia) ahora tiene traducción EN además de la
  // ES original (17/08) — se elige según el toggle, con fallback al campo
  // base por si algún registro viejo todavía no tiene su par traducido.
  const notes = lang === "en" ? object.context?.notesEn || object.context?.notes : object.context?.notes;
  const hasResearch = events.length > 0 || flags.length > 0 || !!notes;
  const destMuseum = object.sourceMuseum ? museums[object.sourceMuseum] : undefined;
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
                  <span className="timeline-dot timeline-dot-accent" aria-hidden="true" />
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
          <span className="timeline-dot timeline-dot-met" aria-hidden="true" />
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
    </aside>
  );
}
