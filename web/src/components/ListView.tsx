import { useEffect, useMemo, useRef, useState } from "react";
import type { MuseumDestination, MuseumObject } from "../types";
import { objectHasResearch } from "../geo";
import { MUSEUM_COLORS, DEFAULT_COLOR } from "../colors";
import { STRINGS, type Lang } from "../i18n";

const PAGE_SIZE = 48;

export type GroupBy = "museum" | "country" | "none";

interface ListViewProps {
  objects: MuseumObject[];
  museums: Record<string, MuseumDestination>;
  lang: Lang;
  hidden: boolean;
  summary: string;
  groupBy: GroupBy;
  onGroupByChange: (g: GroupBy) => void;
  onSelectObject: (object: MuseumObject) => void;
}

interface Group {
  key: string;
  header: string | null;
  objects: MuseumObject[];
  total?: number;
}

// Vista de lista (08/10): alternativa al globo. Recibe las piezas ya
// filtradas (visibleObjects) para respetar los filtros del mapa. Se mantiene
// montada aun oculta, para conservar scroll y agrupación al alternar.
export function ListView({ objects, museums, lang, hidden, summary, groupBy, onGroupByChange, onSelectObject }: ListViewProps) {
  const s = STRINGS[lang];

  const groups = useMemo<Group[]>(() => {
    const title = (o: MuseumObject) => ((lang === "en" ? o.titleEn || o.title : o.title) || "").toLowerCase();
    const sorted = [...objects].sort((a, b) => title(a).localeCompare(title(b), lang));
    if (groupBy === "none") return [{ key: "all", header: null, objects: sorted }];
    if (groupBy === "museum") {
      return Object.keys(museums)
        .map((id) => ({
          key: id,
          header: museums[id].name,
          objects: sorted.filter((o) => o.sourceMuseum === id),
        }))
        .filter((g) => g.objects.length > 0);
    }
    const byCountry: Record<string, MuseumObject[]> = {};
    for (const o of sorted) {
      const c = (lang === "en" ? o.originCountryEn || o.originCountry : o.originCountry) || "";
      (byCountry[c] ??= []).push(o);
    }
    return Object.keys(byCountry)
      .sort((a, b) => (a === "" ? 1 : b === "" ? -1 : a.localeCompare(b, lang)))
      .map((c) => ({ key: c || "?", header: c || s.listUnknownCountry, objects: byCountry[c] }));
  }, [objects, museums, lang, groupBy, s]);

  // Render por tramos: se muestran PAGE_SIZE tarjetas y se suman más al
  // acercarse al final (centinela) o con el botón, que además es la vía para
  // teclado/lector de pantalla. El límite es sobre el total, no por grupo.
  const [limit, setLimit] = useState(PAGE_SIZE);
  useEffect(() => setLimit(PAGE_SIZE), [objects, groupBy, lang]);
  const total = objects.length;
  const sentinelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || hidden || limit >= total) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) setLimit((l) => l + PAGE_SIZE);
      },
      { rootMargin: "400px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [hidden, limit, total]);

  const visibleGroups = useMemo(() => {
    let left = limit;
    const out: Group[] = [];
    for (const g of groups) {
      if (left <= 0) break;
      out.push({ ...g, objects: g.objects.slice(0, left), total: g.objects.length });
      left -= g.objects.length;
    }
    return out;
  }, [groups, limit]);

  const renderedIndex = useMemo(() => {
    const m = new Map<string, number>();
    let i = 0;
    for (const g of visibleGroups) for (const o of g.objects) m.set(o.objectID, i++);
    return m;
  }, [visibleGroups]);

  const options: [GroupBy, string][] = [
    ["museum", s.listGroupMuseum],
    ["country", s.listGroupCountry],
    ["none", s.listGroupNone],
  ];

  return (
    <section id="list-content" tabIndex={-1} className={`list-view${hidden ? " hidden" : ""}`} aria-label={s.viewList} aria-hidden={hidden}>
      <div className="list-view-inner">
        <div className="list-view-toolbar">
          <p className="list-view-count" role="status">{summary}</p>
          <div className="list-group-control" role="group" aria-label={s.listGroupByLabel}>
            <span className="list-group-label">{s.listGroupByLabel}</span>
            {options.map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={`list-group-btn${groupBy === value ? " active" : ""}`}
                aria-pressed={groupBy === value}
                onClick={() => onGroupByChange(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {objects.length === 0 && <p className="list-empty">{s.listEmpty}</p>}

        {visibleGroups.map((group) => (
          <div key={group.key} className="list-group">
            <h2 className="list-group-header">
              {group.header ?? s.listAllPieces} <span className="list-group-count">({group.total ?? group.objects.length})</span>
            </h2>
            <ul className="list-grid">
              {group.objects.map((obj) => {
                const title = (lang === "en" ? obj.titleEn || obj.title : obj.title) || s.untitled;
                const origin = lang === "en" ? obj.originLabelEn || obj.originLabel : obj.originLabel;
                const museumName = obj.sourceMuseum ? museums[obj.sourceMuseum]?.name : null;
                const color = MUSEUM_COLORS[obj.sourceMuseum ?? ""] ?? DEFAULT_COLOR;
                return (
                  <li
                    key={obj.objectID}
                    className="list-card"
                  >
                    <button
                      type="button"
                      className="list-card-main"
                      onClick={() => onSelectObject(obj)}
                      onFocus={() => {
                        // Teclado: al llegar a las últimas tarjetas renderizadas se cargan
                        // más antes de que el próximo Tab salga de la lista.
                        if (limit < total && renderedIndex.get(obj.objectID)! >= limit - 4) {
                          setLimit((l) => l + PAGE_SIZE);
                        }
                      }}
                    >
                      <span className="list-card-image">
                        {obj.primaryImage && (
                          <img src={obj.primaryImage} alt="" loading="lazy" decoding="async" width={200} height={150} />
                        )}
                        {objectHasResearch(obj) && (
                          <span
                            className="research-badge research-badge-thumb"
                            style={{ background: color }}
                            role="img"
                            aria-label={s.hasResearchBadgeAria}
                            title={s.hasResearchBadgeAria}
                          />
                        )}
                      </span>
                      <span className="list-card-title">{title}</span>
                      <span className="list-card-sub">
                        {groupBy !== "museum" && museumName ? `${museumName} · ` : ""}
                        {origin ? s.madeIn(origin) : ""}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}

        {limit < total && <div ref={sentinelRef} className="list-sentinel" aria-hidden="true" />}
      </div>
    </section>
  );
}
