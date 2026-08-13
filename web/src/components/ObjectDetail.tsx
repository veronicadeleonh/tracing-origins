import type { MuseumObject, ProvenanceEvent } from "../types";

interface ObjectDetailProps {
  object: MuseumObject;
  onBack: () => void;
  onClose: () => void;
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  creation: "Creación",
  excavation: "Excavación",
  transfer: "Transferencia",
  sale: "Venta",
  gift: "Donación",
  bequest: "Legado",
  exchange: "Intercambio",
  acquisition: "Adquisición",
  loan: "Préstamo",
  restitution: "Restitución",
  other: "Otro",
};

function eventLabel(event: ProvenanceEvent): string {
  if (!event.event_type) return "Evento";
  return EVENT_TYPE_LABELS[event.event_type] ?? event.event_type;
}

export function ObjectDetail({ object, onBack, onClose }: ObjectDetailProps) {
  const events = object.events;
  const flags = object.context?.context_flags ?? [];
  const notes = object.context?.notes;
  const hasResearch = events.length > 0 || flags.length > 0 || !!notes;

  const subtitle = [object.culture, object.period, object.objectDate].filter(Boolean).join(" · ");
  const museumFields = [
    object.medium ? `Medio: ${object.medium}` : null,
    object.creditLine,
    object.accessionYear ? `Año de ingreso: ${object.accessionYear}` : null,
  ].filter(Boolean) as string[];

  return (
    <aside className="side-panel">
      <div className="panel-header">
        <button className="icon-btn" onClick={onBack} aria-label="Volver a la lista">
          ‹
        </button>
        <button className="icon-btn" onClick={onClose} aria-label="Cerrar panel">
          ×
        </button>
      </div>

      <div className="object-header">
        {object.primaryImage && <img className="object-image" src={object.primaryImage} alt="" />}
        <div className="object-title">{object.title || "(sin título)"}</div>
        {subtitle && <div className="object-subtitle">{subtitle}</div>}
      </div>

      <div className="timeline">
        <div className="timeline-node">
          <span className="timeline-dot timeline-dot-muted" aria-hidden="true" />
          <div className="timeline-date">{object.objectDate || "Origen"}</div>
          <div className="timeline-label">Hecho en {object.originLabel || "lugar desconocido"}</div>
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
            {events.map((event, i) => (
              <div className="timeline-node" key={i}>
                <span className="timeline-dot timeline-dot-accent" aria-hidden="true" />
                <div className="timeline-date">{event.event_date || ""}</div>
                <div className="timeline-label">{eventLabel(event)}</div>
                {event.description && <div className="timeline-desc">{event.description}</div>}
              </div>
            ))}
          </>
        ) : (
          <div className="timeline-note">
            <span className="timeline-note-dot" aria-hidden="true" />
            Recorrido no investigado todavía
          </div>
        )}

        <div className="timeline-node">
          <span className="timeline-dot timeline-dot-met" aria-hidden="true" />
          <div className="timeline-date">Ahora</div>
          <div className="timeline-label">The Metropolitan Museum of Art, Nueva York</div>
        </div>
      </div>

      {(museumFields.length > 0 || object.objectURL) && (
        <div className="museum-record">
          <div className="museum-record-label">Registro del museo</div>
          {museumFields.map((field, i) => (
            <div className="museum-record-field" key={i}>
              {field}
            </div>
          ))}
          {object.objectURL && (
            <a className="met-link" href={object.objectURL} target="_blank" rel="noreferrer">
              Ver en el sitio del Met ↗
            </a>
          )}
        </div>
      )}
    </aside>
  );
}
