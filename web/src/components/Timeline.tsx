interface LegendItem {
  label: string;
  color: string;
}

interface TimelineProps {
  minYear: number;
  maxYear: number;
  year: number;
  onChange: (year: number) => void;
  legend: LegendItem[];
}

// Décadas marcadas en la barra, con año visible solo cada 50 para no
// amontonar texto — el resto son ticks mudos, solo de referencia visual.
export function Timeline({ minYear, maxYear, year, onChange, legend }: TimelineProps) {
  const span = maxYear - minYear;
  const firstDecade = Math.ceil(minYear / 10) * 10;
  const decades: number[] = [];
  for (let d = firstDecade; d <= maxYear; d += 10) decades.push(d);

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
    </div>
  );
}
