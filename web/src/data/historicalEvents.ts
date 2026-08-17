// Eventos puntuales marcados en el timeline del mapa — no son piezas ni
// líneas, son hitos institucionales que ayudan a leer por qué las otras 2
// capas (territorios coloniales, rutas navales) se mueven como se mueven.
// Arranca con el Met porque es el caso menos obvio de los 3 museos (no hubo
// control territorial de EEUU sobre los orígenes de sus piezas, así que el
// mecanismo necesita más contexto que "fue territorio colonial de X" — ver
// MUSEUM_NOTES.met en App.tsx). Investigado 17/08, fuentes: metmuseum.org
// ("History of The Met", "The History of the Department of Egyptian Art") y
// Wikipedia.
export interface HistoricalEvent {
  year: number;
  label: string;
  color: string; // mismo color que el museo asociado (MUSEUM_COLORS en App.tsx)
}

export const HISTORICAL_EVENTS: HistoricalEvent[] = [
  {
    year: 1870,
    label: "Se funda el Met — adquiere su primer objeto ese mismo año (un sarcófago romano). Colección inicial vía donaciones y compras en el mercado, no expansión territorial.",
    color: "#c9a227",
  },
  {
    year: 1876,
    label: "Compra la Colección Cesnola (antigüedades de Chipre) — establece la reputación del Met como repositorio serio de antigüedades. Cesnola era cónsul de EEUU en Chipre; sus métodos de excavación fueron polémicos incluso en su época.",
    color: "#c9a227",
  },
  {
    year: 1906,
    label: "El Met arranca su propia Expedición Egipcia (hasta 1935) — pasa de financiar excavaciones ajenas (Egypt Exploration Fund, 1897-1906) a excavar directamente, bajo autorización del gobierno egipcio de la época. El núcleo de sus ~30.000 piezas egipcias viene de este período.",
    color: "#c9a227",
  },
];
