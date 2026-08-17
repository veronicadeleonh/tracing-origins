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
  // Agregado 17/08 a pedido del usuario: explica por qué el timeline arranca
  // en 1920 por default (TIMELINE_DEFAULT_YEAR en App.tsx) — no es un año
  // arbitrario, es el pico territorial de los dos imperios a la vez. A
  // diferencia de los 3 hitos del Met, este no pertenece a un museo
  // específico (aplica a UK y Francia por igual, o sea a BM y Louvre), así
  // que usa DEFAULT_COLOR (#928d82, el mismo gris neutro que ya se usa en
  // App.tsx para lo que no está ligado a un museo puntual) en vez del rojo
  // del BM o el teal del Louvre — cualquiera de los dos hubiera sido
  // engañoso. Fuentes: Statista/historia del Imperio Británico (13,71
  // millones de mi², 24% de la superficie terrestre, ~413 millones de
  // personas) y Wikipedia sobre el imperio colonial francés (12,5 millones
  // de km² a julio de 1920) — ambos citan 1920 como el pico, por absorber
  // los mandatos de la Sociedad de Naciones sobre territorio alemán y
  // otomano derrotado.
  {
    year: 1920,
    label: "Pico territorial simultáneo de ambos imperios coloniales — Reino Unido llega a ~13,7 millones de mi² (24% de la superficie terrestre) y Francia a ~12,5 millones de km², tras absorber los mandatos de la Sociedad de Naciones sobre territorio alemán y otomano (Irak, Palestina, Siria, Líbano, Camerún, Togo). Ambas potencias tenían asiento permanente en el Consejo de la Sociedad de Naciones recién fundada. Por esto el timeline arranca en este año por default.",
    color: "#928d82",
  },
];
