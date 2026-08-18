// Paleta de colores por museo, centralizada acá (18/08) porque dejó de ser
// solo cosmética de App.tsx: ObjectDetail.tsx y ClusterPanel.tsx también la
// necesitan para el tratamiento narrativo de context_flags — en vez de un
// color de acento genérico (violeta, probado y descartado el mismo día por
// feedback de la usuaria: "sugiere otra cosa"), se reusa el color del museo
// dueño de la pieza para marcar qué está documentado. La idea: el color ya
// significa "esta pieza es de este museo" en las líneas del mapa — que
// también signifique "conocemos su recorrido" refuerza el mismo mensaje en
// vez de competir con un color nuevo.
export const MUSEUM_COLORS: Record<string, string> = {
  met: "#c9a227",
  louvre: "#3d7a8c",
  bm: "#b23a48",
};

export const DEFAULT_COLOR = "#928d82";

// Puntos de origen sin ninguna pieza investigada — gris neutro a propósito,
// para que el contraste con los colores de museo lea como "no sabemos el
// recorrido de acá todavía", no como una cuarta categoría con su propio
// significado.
export const ORIGIN_COLOR = "#8a8478";

export function museumColor(sourceMuseum: string | null | undefined): string {
  return (sourceMuseum && MUSEUM_COLORS[sourceMuseum]) || DEFAULT_COLOR;
}
