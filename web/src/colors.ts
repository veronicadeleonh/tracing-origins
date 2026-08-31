// Paleta de colores por museo, centralizada acá (18/08) porque dejó de ser
// solo cosmética de App.tsx: ObjectDetail.tsx y ClusterPanel.tsx también la
// necesitan para el tratamiento narrativo de context_flags — en vez de un
// color de acento genérico (violeta, probado y descartado el mismo día por
// feedback de la usuaria: "sugiere otra cosa"), se reusa el color del museo
// dueño de la pieza para marcar qué está documentado. La idea: el color ya
// significa "esta pieza es de este museo" en las líneas del mapa — que
// también signifique "conocemos su recorrido" refuerza el mismo mensaje en
// vez de competir con un color nuevo.
// FRANCE_COLOR es la base de la que salen los dos museos franceses (31/08) —
// antes de Quai Branly, este mismo teal ya identificaba "Louvre" en toda la
// app (líneas, toggle, capa de imperios coloniales vía COLONIAL_POWER_COLORS
// en App.tsx). En vez de darle a Quai Branly un color sin relación (el verde
// original, #5a8f5a, se sentía fuera de la paleta — feedback de la usuaria
// el 31/08), se lo deriva del mismo teal, más oscuro/desaturado para que
// siga siendo distinguible en el mapa de Louvre. El resultado: los dos
// museos franceses leen visualmente como familia (mismo tono, distinta
// luminosidad), y COLONIAL_POWER_COLORS.fr sigue apuntando al mismo valor de
// siempre pero ahora representa a ambos museos franceses, no solo al
// Louvre — sin cambiar un solo píxel de lo que ya existía para Louvre/UK.
const FRANCE_COLOR = "#3d7a8c";

export const MUSEUM_COLORS: Record<string, string> = {
  met: "#c9a227",
  louvre: FRANCE_COLOR,
  bm: "#b23a48",
  qb: "#2c5763", // mismo matiz que FRANCE_COLOR, ~15pp más oscuro -- ver comentario arriba
};

// País de origen de cada museo (31/08, pedido de la usuaria: agrupar los
// toggles de museo por país en vez de una fila plana) — mismos 3 países que
// ya identifica COLONIAL_POWER_COLORS en App.tsx (uk/fr), más EEUU para el
// Met (que no tiene territorio colonial sombreado en el mapa, ver
// MUSEUM_NOTES.met, pero igual es "de dónde es el museo" para esta
// agrupación). Claves de país fijas ("us"/"fr"/"uk") consumidas también por
// museumCountryNames en i18n.ts.
export const MUSEUM_COUNTRY: Record<string, string> = {
  met: "us",
  louvre: "fr",
  bm: "uk",
  qb: "fr",
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
