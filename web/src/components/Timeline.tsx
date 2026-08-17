import { useState, type ReactNode } from "react";
import type { HistoricalEvent } from "../data/historicalEvents";

interface LegendItem {
  label: string;
  color: string;
}

interface LayerToggle {
  id: string;
  label: string;
  active: boolean;
  icon?: ReactNode;
  note?: string;
}

interface TimelineProps {
  minYear: number;
  maxYear: number;
  year: number;
  onChange: (year: number) => void;
  legend: LegendItem[];
  layerToggles: LayerToggle[];
  onToggleLayer: (id: string) => void;
  events: HistoricalEvent[];
}

// Décadas marcadas en la barra, con año visible solo cada 50 para no
// amontonar texto — el resto son ticks mudos, solo de referencia visual.
export function Timeline({
  minYear,
  maxYear,
  year,
  onChange,
  legend,
  layerToggles,
  onToggleLayer,
  events,
}: TimelineProps) {
  const span = maxYear - minYear;
  const firstDecade = Math.ceil(minYear / 10) * 10;
  const decades: number[] = [];
  for (let d = firstDecade; d <= maxYear; d += 10) decades.push(d);
  const [hoveredEvent, setHoveredEvent] = useState<number | null>(null);
  // Nota por capa (nivel 3 de "notas de contexto en la UI", ver CLAUDE.md) —
  // qué muestra y qué NO muestra cada capa (ej. por qué solo UK/Francia).
  // Mismo patrón que el botón "i" de cada museo, pero acá vive local al
  // componente en vez de en App.tsx porque es puramente informativo, no
  // afecta ningún otro estado de la app.
  const [openNote, setOpenNote] = useState<string | null>(null);

  return (
    <div className="year-timeline">
      <div className="year-timeline-header">
        <div className="year-timeline-legend">
          {legend.map((item) => (
            <span key={item.label} className="year-timeline-legend-item">
              <span className="year-timeline-legend-dot" style={{ background: item.color }} />
              {item.label}
            </span>
          ))}
        </div>
        <div className="year-timeline-year">{year}</div>
        <div className="year-timeline-layers">
          {layerToggles.map((toggle) => (
            <div
              key={toggle.id}
              className={`year-timeline-layer-toggle-wrap${toggle.active ? " active" : " inactive"}`}
            >
              <button
                type="button"
                className="year-timeline-layer-toggle"
                aria-pressed={toggle.active}
                onClick={() => onToggleLayer(toggle.id)}
              >
                {toggle.icon && (
                  <span className="year-timeline-layer-toggle-icon" aria-hidden="true">
                    {toggle.icon}
                  </span>
                )}
                {toggle.label}
              </button>
              {toggle.note && (
                <button
                  type="button"
                  className={`year-timeline-note-btn${openNote === toggle.id ? " open" : ""}`}
                  aria-label={`Sobre la capa de ${toggle.label}`}
                  aria-expanded={openNote === toggle.id}
                  onClick={() => setOpenNote((cur) => (cur === toggle.id ? null : toggle.id))}
                >
                  i
                </button>
              )}
              {openNote === toggle.id && (
                <div className="year-timeline-note">{toggle.note}</div>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="year-timeline-track">
        <div className="year-timeline-ticks">
          {decades.map((d) => (
            <div
              key={d}
              className={`year-timeline-tick${d % 50 === 0 ? " year-timeline-tick-major" : ""}`}
              style={{ left: `${((d - minYear) / span) * 100}%` }}
            >
              {d % 50 === 0 && <span className="year-timeline-tick-label">{d}</span>}
            </div>
          ))}
        </div>
        <div className="year-timeline-events">
          {events
            .filter((ev) => ev.year >= minYear && ev.year <= maxYear)
            .map((ev) => (
              <div
                key={ev.year}
                className="year-timeline-event-wrap"
                style={{ left: `${((ev.year - minYear) / span) * 100}%` }}
              >
                <button
                  type="button"
                  className="year-timeline-event"
                  style={{ background: ev.color }}
                  aria-label={`${ev.year}: ${ev.label}`}
                  onClick={() => onChange(ev.year)}
                  onMouseEnter={() => setHoveredEvent(ev.year)}
                  onMouseLeave={() => setHoveredEvent((cur) => (cur === ev.year ? null : cur))}
                  onFocus={() => setHoveredEvent(ev.year)}
                  onBlur={() => setHoveredEvent((cur) => (cur === ev.year ? null : cur))}
                />
                {(hoveredEvent === ev.year || year === ev.year) && (
                  <div className="year-timeline-event-tooltip">
                    <strong>{ev.year}</strong> — {ev.label}
                  </div>
                )}
              </div>
            ))}
        </div>
        <input
          type="range"
          className="year-timeline-slider"
          min={minYear}
          max={maxYear}
          step={1}
          value={year}
          onChange={(e) => onChange(Number(e.target.value))}
          aria-label="Año del mapa de territorios coloniales"
        />
      </div>
      <div className="year-timeline-caption">
        Estas capas cambian con el año. Las líneas pieza→museo no: son fijas, no representan un momento puntual.
      </div>
    </div>
  );
}
