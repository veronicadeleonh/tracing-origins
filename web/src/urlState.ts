// Ruta + filtros en la URL (09/10). Sin librería de router: son 2 rutas
// ("/" mapa, "/list" lista) y los filtros viajan como query params.
import type { GroupBy } from "./components/ListView";

export type Research = "all" | "with" | "without";
export type FilterState = {
  visibleMuseums: Record<string, boolean>;
  research: Research;
  flags: Set<string>;
  types: Set<string>;
  groupBy: GroupBy;
};

export const LIST_PATH = "/list";
export const viewFromPath = (p: string): "map" | "list" =>
  p.replace(/\/+$/, "") === LIST_PATH ? "list" : "map";

const csv = (v: string | null) => (v ? v.split(",").filter(Boolean) : []);

export function parseFilters(search: string, museumIds: string[]): FilterState {
  const q = new URLSearchParams(search);
  const only = q.has("museums") ? new Set(csv(q.get("museums"))) : null;
  const r = q.get("research");
  const g = q.get("group");
  return {
    visibleMuseums: Object.fromEntries(museumIds.map((id) => [id, only ? only.has(id) : true])),
    research: r === "with" || r === "without" ? r : "all",
    flags: new Set(csv(q.get("mechanism"))),
    types: new Set(csv(q.get("type"))),
    groupBy: g === "country" || g === "none" ? g : "museum",
  };
}

export function buildSearch(f: FilterState, museumIds: string[], includeGroup: boolean): string {
  const q = new URLSearchParams();
  const on = museumIds.filter((id) => f.visibleMuseums[id]);
  if (on.length !== museumIds.length) q.set("museums", on.join(","));
  if (f.research !== "all") q.set("research", f.research);
  if (f.flags.size) q.set("mechanism", [...f.flags].sort().join(","));
  if (f.types.size) q.set("type", [...f.types].sort().join(","));
  if (includeGroup && f.groupBy !== "museum") q.set("group", f.groupBy);
  const s = q.toString();
  return s ? `?${s}` : "";
}
