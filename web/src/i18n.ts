// Traducción de la interfaz (ES/EN) — primera vuelta, alcance acordado con
// el usuario el 17/08: solo texto de interfaz (nuestro, no de los museos).
// La metadata cruda de cada pieza (título/cultura/medio/crédito) sigue tal
// cual la da cada fuente —inglés para Met/BM, francés para Louvre— y
// origin_label sigue en español (viene ya resuelto desde geocode.py,
// ES_NAMES) sin importar el idioma elegido acá; ambas cosas quedan
// anotadas como próximo paso en CLAUDE.md/README, no en este alcance.
export type Lang = "es" | "en";

export interface I18nStrings {
  museumInfoAria: (name: string) => string;
  museumNotes: Record<string, string>;
  pieceCounterAll: (n: number) => string;
  pieceCounterFiltered: (visible: number, total: number) => string;
  curatedNoteBtnAria: string;
  curatedNoteText: string;
  curatedNoteTerritoriesPrefix: string;
  curatedNoteTerritoriesLicense: string;
  curatedNoteRoutesPrefix: string;
  curatedNoteRoutesSuffix: string;
  welcomeTriggerAria: string;
  langToggleAria: string;
  contextDockLabel: string;
  legendUK: string;
  legendFR: string;
  layerToggleTerritories: string;
  layerToggleRoutes: string;
  layerNotes: Record<string, string>;
  historicalEvents: string[];
  timelineNoteAria: (label: string) => string;
  timelineSliderAria: string;
  timelineCaption: string;

  clusterUnknownOrigin: string;
  clusterPieceCount: (n: number) => string;
  closePanelAria: string;
  untitled: string;

  backAria: string;
  eventTypeLabels: Record<string, string>;
  eventFallback: string;
  madeIn: (place: string) => string;
  unknownPlace: string;
  originFallbackDate: string;
  noResearch: string;
  now: string;
  unknownMuseum: string;
  museumRecordLabel: string;
  mediumPrefix: string;
  accessionYearPrefix: string;
  viewAt: (name: string) => string;
  theMuseumWebsite: string;

  welcomeSlogan: string;
  welcomeHowToUseHeading: string;
  welcomeSteps: string[];
  welcomeDataModelHeading: string;
  welcomeDataModelIntro: string;
  welcomeDataModelSteps: string[];
  welcomeAboutHeading: string;
  welcomeAboutP1: string;
  welcomeAboutP2: string;
  welcomeCloseAria: string;
  welcomeBack: string;
  welcomeNext: string;
  welcomeFinish: string;

  tooltipOrigin: (label: string, count: number) => string;
  langToggleLabel: string;

  prevPieceAria: string;
  nextPieceAria: string;
  piecePosition: (index: number, total: number) => string;
  piecePrevLabel: string;
  pieceNextLabel: string;
}

export const STRINGS: Record<Lang, I18nStrings> = {
  es: {
    museumInfoAria: (name) => `Sobre la procedencia de las piezas de ${name}`,
    museumNotes: {
      met: "El Met no adquirió estas piezas porque EEUU controlara territorialmente sus lugares de origen. Llegaron por el mercado internacional de antigüedades, misiones de excavación autorizadas por la potencia colonial de turno y donantes ricos — poder económico y político ganado en años recientes, no expansión territorial.",
      louvre: "Los 4 departamentos del Louvre representados acá (Antigüedades Egipcias, Orientales, Griegas-Etruscas-Romanas, Arte Islámico) cubren sobre todo Egipto, Medio Oriente y el Mediterráneo. El fondo de África Subsahariana y América no está en el Louvre: se transfirió al Musée du Quai Branly cuando abrió en 2006.",
      bm: "El caso más directo de administración colonial territorial de los tres museos, con mecanismos que van desde la conquista militar (la Piedra de Rosetta, las Placas de Benín) hasta excavaciones bajo permiso del gobierno otomano.",
    },
    pieceCounterAll: (n) => `${n} piezas`,
    pieceCounterFiltered: (visible, total) => `${visible} de ${total} piezas`,
    curatedNoteBtnAria: "Sobre esta muestra",
    curatedNoteText: "Muestra curada — no representa la colección completa de cada museo. Muchas piezas quedan fuera.",
    curatedNoteTerritoriesPrefix: "Territorios coloniales: Seshat Global History Databank —",
    curatedNoteTerritoriesLicense: "(CC-BY 4.0).",
    curatedNoteRoutesPrefix: "Rutas navales: Jones et al. (2007),",
    curatedNoteRoutesSuffix: "(CC-BY 3.0) — muestra curada de 50 cruceros, no todas las rutas del período.",
    welcomeTriggerAria: "Sobre este proyecto",
    langToggleAria: "Cambiar a inglés",
    contextDockLabel: "Contexto histórico",
    legendUK: "Reino Unido",
    legendFR: "Francia",
    layerToggleTerritories: "Imperios",
    layerToggleRoutes: "Rutas navales",
    layerNotes: {
      territories: "Sombrea las regiones que fueron territorio colonial de UK o Francia en el año seleccionado (Cliopatria, Seshat Global History Databank). EEUU no aparece — el Met no adquirió piezas por control territorial, ver la nota del Met arriba. Los mandatos británicos de Irak y Palestina (1920-1932) tampoco están: la fuente no los modela como entidad propia.",
      routes: "50 rutas curadas de barcos británicos y franceses entre 1700-1900, de un archivo real de bitácoras de navegación (CLIWOC/PANGAEA). No son las únicas rutas de la época ni viajes de exploradores famosos (Cook, Bougainville, etc. no están en este dataset) — es una muestra priorizada por nación y densidad de datos registrados.",
    },
    historicalEvents: [
      "Se funda el Met — adquiere su primer objeto ese mismo año (un sarcófago romano). Colección inicial vía donaciones y compras en el mercado, no expansión territorial.",
      "Compra la Colección Cesnola (antigüedades de Chipre) — establece la reputación del Met como repositorio serio de antigüedades. Cesnola era cónsul de EEUU en Chipre; sus métodos de excavación fueron polémicos incluso en su época.",
      "El Met arranca su propia Expedición Egipcia (hasta 1935) — pasa de financiar excavaciones ajenas (Egypt Exploration Fund, 1897-1906) a excavar directamente, bajo autorización del gobierno egipcio de la época. El núcleo de sus ~30.000 piezas egipcias viene de este período.",
      "Pico territorial simultáneo de ambos imperios coloniales — Reino Unido llega a ~13,7 millones de mi² (24% de la superficie terrestre) y Francia a ~12,5 millones de km², tras absorber los mandatos de la Sociedad de Naciones sobre territorio alemán y otomano (Irak, Palestina, Siria, Líbano, Camerún, Togo). Ambas potencias tenían asiento permanente en el Consejo de la Sociedad de Naciones recién fundada. Por esto el timeline arranca en este año por default.",
    ],
    timelineNoteAria: (label) => `Sobre la capa de ${label}`,
    timelineSliderAria: "Año del mapa de territorios coloniales",
    timelineCaption: "Estas capas cambian con el año. Las líneas pieza→museo no: son fijas, no representan un momento puntual.",

    clusterUnknownOrigin: "Origen sin identificar",
    clusterPieceCount: (n) => `${n} pieza${n === 1 ? "" : "s"} de este lugar`,
    closePanelAria: "Cerrar panel",
    untitled: "(sin título)",

    backAria: "Volver a la lista",
    eventTypeLabels: {
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
    },
    eventFallback: "Evento",
    madeIn: (place) => `Hecho en ${place}`,
    unknownPlace: "lugar desconocido",
    originFallbackDate: "Origen",
    noResearch: "Recorrido no investigado todavía",
    now: "Ahora",
    unknownMuseum: "Museo desconocido",
    museumRecordLabel: "Registro del museo",
    mediumPrefix: "Medio: ",
    accessionYearPrefix: "Año de ingreso: ",
    viewAt: (name) => `Ver en ${name} ↗`,
    theMuseumWebsite: "el sitio del museo",

    welcomeSlogan: "El recorrido de una pieza, desde su origen hasta la vitrina.",
    welcomeHowToUseHeading: "Cómo usar el mapa",
    welcomeSteps: [
      "Click en un punto de origen para ver las piezas de ese lugar.",
      "Click en una pieza para ver su ficha y su recorrido documentado.",
      'Los toggles arriba a la izquierda prenden o apagan cada museo — el botón "i" explica su lógica de adquisición.',
      '"Contexto histórico", al pie del mapa, agrega territorios coloniales y rutas navales en un timeline 1700–2020.',
    ],
    welcomeDataModelHeading: "Modelo de datos — 3 capas",
    welcomeDataModelIntro: "Cada pieza separa siempre tres cosas, para que quede claro qué dice cada fuente:",
    welcomeDataModelSteps: [
      "Lo que dice el museo (metadata original).",
      "Lo que inferimos nosotros (origen geográfico, no un dato oficial).",
      "Lo que investigamos nosotros (recorrido histórico, cuando existe).",
    ],
    welcomeAboutHeading: "Sobre esta muestra",
    welcomeAboutP1: "Proyecto curado para portfolio personal, no un dataset exhaustivo — no representa la colección completa de ningún museo.",
    welcomeAboutP2: 'No clasifica piezas como "robadas" o "no robadas": documenta el recorrido con fuentes, no emite un veredicto. La mayoría de las piezas todavía no tiene esa investigación cargada — es el estado por defecto, no una excepción.',
    welcomeCloseAria: "Cerrar",
    welcomeBack: "Atrás",
    welcomeNext: "Siguiente",
    welcomeFinish: "Entendido, ver el mapa",

    tooltipOrigin: (label, count) => `${label} — ${count} pieza(s) (click para el detalle)`,
    langToggleLabel: "EN",

    prevPieceAria: "Pieza anterior de este lugar",
    nextPieceAria: "Pieza siguiente de este lugar",
    piecePosition: (index, total) => `${index} de ${total}`,
    piecePrevLabel: "Anterior",
    pieceNextLabel: "Siguiente",
  },
  en: {
    museumInfoAria: (name) => `About the provenance of ${name}'s pieces`,
    museumNotes: {
      met: "The Met didn't acquire these pieces because the US held territorial control over their places of origin. They arrived through the international antiquities market, excavation missions authorized by whichever colonial power held the territory, and wealthy donors — recent economic and political power, not territorial expansion.",
      louvre: "The 4 Louvre departments represented here (Egyptian Antiquities, Near Eastern Antiquities, Greek/Etruscan/Roman Antiquities, Islamic Art) cover mostly Egypt, the Middle East, and the Mediterranean. The Louvre's Sub-Saharan Africa and Americas holdings aren't here — they were transferred to the Musée du Quai Branly when it opened in 2006.",
      bm: "The most direct case of territorial colonial administration of the three museums, with mechanisms ranging from military conquest (the Rosetta Stone, the Benin Bronzes) to excavations permitted by the Ottoman government.",
    },
    pieceCounterAll: (n) => `${n} pieces`,
    pieceCounterFiltered: (visible, total) => `${visible} of ${total} pieces`,
    curatedNoteBtnAria: "About this sample",
    curatedNoteText: "Curated sample — doesn't represent each museum's full collection. Many pieces are left out.",
    curatedNoteTerritoriesPrefix: "Colonial territories: Seshat Global History Databank —",
    curatedNoteTerritoriesLicense: "(CC-BY 4.0).",
    curatedNoteRoutesPrefix: "Naval routes: Jones et al. (2007),",
    curatedNoteRoutesSuffix: "(CC-BY 3.0) — curated sample of 50 voyages, not every route from the period.",
    welcomeTriggerAria: "About this project",
    langToggleAria: "Switch to Spanish",
    contextDockLabel: "Historical context",
    legendUK: "United Kingdom",
    legendFR: "France",
    layerToggleTerritories: "Empires",
    layerToggleRoutes: "Naval routes",
    layerNotes: {
      territories: "Shades the regions that were UK or French colonial territory in the selected year (Cliopatria, Seshat Global History Databank). The US doesn't appear — the Met didn't acquire pieces through territorial control, see the Met's note above. The British mandates of Iraq and Palestine (1920-1932) aren't shown either: the source doesn't model them as their own entity.",
      routes: "50 curated routes of British and French ships between 1700-1900, from a real archive of navigation logbooks (CLIWOC/PANGAEA). These aren't the only routes of the period, nor famous explorers' voyages (Cook, Bougainville, etc. aren't in this dataset) — it's a sample prioritized by nation and how much data each logbook recorded.",
    },
    historicalEvents: [
      "The Met is founded — it acquires its first object that same year (a Roman sarcophagus). Early collection built through donations and market purchases, not territorial expansion.",
      "Purchases the Cesnola Collection (antiquities from Cyprus) — establishes the Met's reputation as a serious antiquities repository. Cesnola was the US consul in Cyprus; his excavation methods were controversial even at the time.",
      "The Met starts its own Egyptian Expedition (through 1935) — moves from funding other institutions' excavations (Egypt Exploration Fund, 1897-1906) to excavating directly, authorized by the Egyptian government of the time. The core of its ~30,000 Egyptian pieces comes from this period.",
      "Simultaneous territorial peak of both colonial empires — the UK reaches ~13.7 million sq mi (24% of the world's land area) and France ~12.5 million km², after absorbing League of Nations mandates over former German and Ottoman territory (Iraq, Palestine, Syria, Lebanon, Cameroon, Togo). Both powers held permanent seats on the newly founded League of Nations Council. This is why the timeline defaults to this year.",
    ],
    timelineNoteAria: (label) => `About the ${label} layer`,
    timelineSliderAria: "Year of the colonial-territories map",
    timelineCaption: "These layers change with the year. The piece→museum lines don't: they're fixed, they don't represent a single point in time.",

    clusterUnknownOrigin: "Unidentified origin",
    clusterPieceCount: (n) => `${n} piece${n === 1 ? "" : "s"} from this location`,
    closePanelAria: "Close panel",
    untitled: "(untitled)",

    backAria: "Back to list",
    eventTypeLabels: {
      creation: "Creation",
      excavation: "Excavation",
      transfer: "Transfer",
      sale: "Sale",
      gift: "Gift",
      bequest: "Bequest",
      exchange: "Exchange",
      acquisition: "Acquisition",
      loan: "Loan",
      restitution: "Restitution",
      other: "Other",
    },
    eventFallback: "Event",
    madeIn: (place) => `Made in ${place}`,
    unknownPlace: "unknown place",
    originFallbackDate: "Origin",
    noResearch: "Journey not researched yet",
    now: "Now",
    unknownMuseum: "Unknown museum",
    museumRecordLabel: "Museum record",
    mediumPrefix: "Medium: ",
    accessionYearPrefix: "Accession year: ",
    viewAt: (name) => `View at ${name} ↗`,
    theMuseumWebsite: "the museum's website",

    welcomeSlogan: "A piece's journey, from its origin to the display case.",
    welcomeHowToUseHeading: "How to use the map",
    welcomeSteps: [
      "Click an origin point to see the pieces from that place.",
      "Click a piece to see its record and documented journey.",
      'The toggles in the top left turn each museum on or off — the "i" button explains its acquisition pattern.',
      '"Historical context", at the bottom of the map, adds colonial territories and naval routes on a 1700–2020 timeline.',
    ],
    welcomeDataModelHeading: "Data model — 3 layers",
    welcomeDataModelIntro: "Each piece always keeps three things separate, so it's clear what each source says:",
    welcomeDataModelSteps: [
      "What the museum states (original metadata).",
      "What we infer (geographic origin, not an official data point).",
      "What we researched ourselves (historical journey, when it exists).",
    ],
    welcomeAboutHeading: "About this sample",
    welcomeAboutP1: "A curated personal-portfolio project, not an exhaustive dataset — it doesn't represent any museum's full collection.",
    welcomeAboutP2: 'It doesn\'t classify pieces as "stolen" or "not stolen": it documents the journey with sources, it doesn\'t issue a verdict. Most pieces don\'t have that research loaded yet — that\'s the default state, not an exception.',
    welcomeCloseAria: "Close",
    welcomeBack: "Back",
    welcomeNext: "Next",
    welcomeFinish: "Got it, see the map",

    tooltipOrigin: (label, count) => `${label} — ${count} piece(s) (click for details)`,
    langToggleLabel: "ES",

    prevPieceAria: "Previous piece from this location",
    nextPieceAria: "Next piece from this location",
    piecePosition: (index, total) => `${index} of ${total}`,
    piecePrevLabel: "Previous",
    pieceNextLabel: "Next",
  },
};
