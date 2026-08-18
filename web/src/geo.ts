import type { MuseumObject } from "./types";
import type { Lang } from "./i18n";

// ~2km — mismo valor y misma lógica que jittered_point en src/make_map.py.
// Puramente visual: nunca se escribe de vuelta a los datos, solo se usa para
// calcular el punto de arranque de cada línea dibujada.
export const JITTER_RADIUS_DEG = 0.02;

export function jitteredPoint(
  lat: number,
  lon: number,
  index: number,
  count: number,
  radiusDeg: number = JITTER_RADIUS_DEG,
): [number, number] {
  if (count <= 1) return [lat, lon];
  const angle = (2 * Math.PI * index) / count;
  const dlat = radiusDeg * Math.sin(angle);
  const lonScale = Math.cos((lat * Math.PI) / 180) || 1.0;
  const dlon = (radiusDeg * Math.cos(angle)) / lonScale;
  return [lat + dlat, lon + dlon];
}

// Tratamiento narrativo de context_flags (18/08, decidido con la usuaria):
// en vez de mostrar la diferencia "patrón completo / detalle investigado
// parcial" solo en texto (curated-note, welcome modal), se marca también
// visualmente qué piezas tienen layer 3 cargada — un punto de origen en el
// mapa con al menos una pieza así, y cada fila en ClusterPanel. Mismo
// criterio que hasResearch en ObjectDetail.tsx (eventos citados, flags o
// notas), pero simplificado a "tiene fila en context.csv o al menos un
// evento" porque acá no depende del idioma (a diferencia de ObjectDetail,
// que elige notes/notesEn según lang).
export function objectHasResearch(obj: MuseumObject): boolean {
  return !!obj.context || obj.events.length > 0;
}

export interface OriginCluster {
  lat: number;
  lon: number;
  label: string;
  objects: MuseumObject[];
}

/** Agrupa objetos por punto de origen (redondeado a 3 decimales, como en
 * make_map.py) para tener un único marker/click-target por lugar, aunque
 * cada objeto siga dibujando su propia línea. `lang` (agregado 17/08, toggle
 * ES/EN ampliado a originLabel) decide si el label del cluster usa
 * originLabel o originLabelEn — la clave de agrupación sigue basada en
 * originLabel (ES) a propósito, para que cambiar el idioma no reparta un
 * mismo punto geográfico en dos clusters distintos. */
export function groupByOrigin(objects: MuseumObject[], lang: Lang = "es"): OriginCluster[] {
  const groups = new Map<string, OriginCluster>();

  for (const obj of objects) {
    const lat = Math.round(obj.originLat * 1000) / 1000;
    const lon = Math.round(obj.originLon * 1000) / 1000;
    const groupingLabel = obj.originLabel ?? "";
    const label = (lang === "en" ? obj.originLabelEn || obj.originLabel : obj.originLabel) ?? "";
    const key = `${lat}|${lon}|${groupingLabel}`;

    if (!groups.has(key)) {
      groups.set(key, { lat, lon, label, objects: [] });
    }
    groups.get(key)!.objects.push(obj);
  }

  for (const cluster of groups.values()) {
    // objectID ahora es "met:96404" etc. (namespaceado por museo) — orden
    // lexicográfico alcanza, lo único que importa es que sea determinístico.
    cluster.objects.sort((a, b) => a.objectID.localeCompare(b.objectID));
  }

  return [...groups.values()];
}
