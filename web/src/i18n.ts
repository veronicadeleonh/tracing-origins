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
  curatedNoteBasemap: string;
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
  hasResearchBadgeAria: string;
  hasResearchLegend: string;
  museumFilterRowLabel: string;
  // Drawer de filtros para mobile/tablet (01/09) -- botón pull-tab que
  // colapsa/expande museos + investigación + switch de país en pantallas
  // angostas, ver .mobile-filters-toggle en App.css.
  mobileFiltersToggleLabel: string;
  mobileFiltersToggleAria: string;
  // Agrupación de toggles de museo por país (31/08, pedido de la usuaria) --
  // claves fijas "us"/"fr"/"uk" (los 3 países de origen de los 4 museos),
  // ver MUSEUM_COUNTRY en colors.ts.
  museumCountryNames: Record<string, string>;
  researchFilterAria: string;
  researchFilterRowLabel: string;
  researchFilterLabels: Record<"all" | "with" | "without", string>;
  // Filtro por mecanismo (context_flags), agregado 23/08 a pedido de la
  // usuaria al retomar el ítem "tratamiento narrativo de context_flags"
  // del backlog -- ver CLAUDE.md. Vocabulario cerrado de 21 flags,
  // mostrados tal cual (sin agrupar) en un dropdown multi-select.
  mechanismFilterLabel: string;
  mechanismFilterLabelActive: (n: number) => string;
  mechanismFilterAria: string;
  mechanismClearLabel: string;
  contextFlagLabels: Record<string, string>;
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
  welcomeSourcesHeading: string;
  welcomeCreditsHeading: string;
  welcomeCreditsRepoPrefix: string;
  welcomeCreditsSitePrefix: string;
  welcomeCloseAria: string;
  welcomeFinish: string;

  // Tooltip de 2 líneas sobre el mapa (19/08) -- título en negrita + una
  // segunda línea con el dato secundario. tooltipPieceCount es la segunda
  // línea compartida por origins/country-hit (museums usa la ciudad
  // directamente, sin traducción).
  tooltipPieceCount: (count: number) => string;
  langToggleLabel: string;

  prevPieceAria: string;
  nextPieceAria: string;
  piecePosition: (index: number, total: number) => string;
  piecePrevLabel: string;
  pieceNextLabel: string;

  imageExpandAria: string;
  imageCollapseAria: string;

  countryResultsSubtitle: (n: number) => string;
  countryClickToggleLabel: string;
  countryClickToggleAria: string;
  countryClickNoteAria: string;
  countryClickNoteText: string;
  tooltipCountryEmptySub: string;
  countryGroupMuseumHeader: (name: string, n: number) => string;

  // Onboarding interactivo con spotlight (01/09) -- ver data/tourSteps.ts
  // para los selectores (posición, no traducible); acá solo título+texto de
  // cada paso, indexado por posición en TOUR_STEPS (mismo patrón que
  // historicalEvents/historicalEventLabels).
  tourSteps: { title: string; text: string }[];
  tourStepOf: (current: number, total: number) => string;
  tourBack: string;
  tourNext: string;
  tourStart: string;
  tourSkip: string;
  tourAria: string;
}

export const STRINGS: Record<Lang, I18nStrings> = {
  es: {
    museumInfoAria: (name) => `Sobre la procedencia de las piezas de ${name}`,
    museumNotes: {
      met: "El Met no controló territorialmente sus lugares de origen — llegaron por el mercado de antigüedades, excavaciones autorizadas por la potencia colonial de turno y donantes ricos.",
      louvre: "Sus departamentos cubren sobre todo Egipto, Medio Oriente y el Mediterráneo. África Subsahariana y América pasaron al Musée du Quai Branly en 2006.",
      bm: "El caso más directo de administración colonial: desde la conquista militar (Piedra de Rosetta, Placas de Benín) hasta excavaciones bajo permiso otomano.",
      qb: "Museo etnográfico, no de antigüedades — cubre África, América, Asia y Oceanía (transferido del Louvre en 2006). Llegó vía coleccionistas privados y funcionarios coloniales, no excavación.",
    },
    pieceCounterAll: (n) => `${n} piezas`,
    pieceCounterFiltered: (visible, total) => `${visible} de ${total} piezas`,
    curatedNoteBasemap: "Los límites y nombres del mapa base son la convención por default de Mapbox, no una postura editorial de este proyecto.",
    curatedNoteTerritoriesPrefix: "Territorios coloniales: Seshat Global History Databank —",
    curatedNoteTerritoriesLicense: "(CC-BY 4.0).",
    curatedNoteRoutesPrefix: "Rutas navales: Jones et al. (2007),",
    curatedNoteRoutesSuffix: "(CC-BY 3.0) — muestra curada de 50 cruceros, no todas las rutas del período.",
    welcomeTriggerAria: "Sobre este proyecto",
    langToggleAria: "Cambiar a inglés",
    contextDockLabel: "Contexto histórico",
    legendUK: "Reino Unido",
    legendFR: "Francia",
    layerToggleTerritories: "Colonias",
    layerToggleRoutes: "Rutas navales",
    layerNotes: {
      territories: "Sombrea el territorio colonial de UK y Francia en el año seleccionado. EEUU no aparece (ver la nota del Met) ni los mandatos británicos de Irak/Palestina — la fuente no los modela.",
      routes: "50 rutas curadas de barcos británicos y franceses, 1700-1900, de bitácoras reales de navegación (CLIWOC). No incluye viajes de exploradores famosos como Cook o Bougainville.",
    },
    historicalEvents: [
      "Se funda el Met — adquiere su primer objeto ese mismo año (un sarcófago romano). Colección inicial vía donaciones y compras en el mercado, no expansión territorial.",
      "Compra la Colección Cesnola (antigüedades de Chipre) — establece la reputación del Met como repositorio serio de antigüedades. Cesnola era cónsul de EEUU en Chipre; sus métodos de excavación fueron polémicos incluso en su época.",
      "El Met arranca su propia Expedición Egipcia (hasta 1935) — pasa de financiar excavaciones ajenas (Egypt Exploration Fund, 1897-1906) a excavar directamente, bajo autorización del gobierno egipcio de la época. El núcleo de sus ~30.000 piezas egipcias viene de este período.",
      "Pico territorial simultáneo de ambos imperios coloniales — Reino Unido llega a ~13,7 millones de mi² (24% de la superficie terrestre) y Francia a ~12,5 millones de km², tras absorber los mandatos de la Sociedad de Naciones sobre territorio alemán y otomano (Irak, Palestina, Siria, Líbano, Camerún, Togo). Ambas potencias tenían asiento permanente en el Consejo de la Sociedad de Naciones recién fundada. Por esto el timeline arranca en este año por default.",
      "Se inaugura el Musée du Quai Branly — el fondo de África Subsahariana, América, Asia y Oceanía del Louvre (que nunca tuvo un departamento curatorial propio para esas regiones) se transfiere al museo nuevo. Desde entonces el Louvre queda concentrado en Egipto, Medio Oriente, el Mediterráneo y Europa, y Quai Branly cubre el resto del mundo — por eso las líneas de ambos museos en el mapa se leen como dos mitades de una misma colección francesa.",
    ],
    timelineNoteAria: (label) => `Sobre la capa de ${label}`,
    timelineSliderAria: "Año del mapa de territorios coloniales",
    timelineCaption: "Estas capas cambian con el año. Las líneas pieza→museo no: son fijas, no representan un momento puntual.",

    clusterUnknownOrigin: "Origen sin identificar",
    clusterPieceCount: (n) => `${n} pieza${n === 1 ? "" : "s"} de este lugar`,
    hasResearchBadgeAria: "Tiene recorrido investigado y citado",
    hasResearchLegend: "recorrido investigado y citado (color = museo)",
    museumFilterRowLabel: "Museos:",
    mobileFiltersToggleLabel: "Filtros",
    mobileFiltersToggleAria: "Mostrar u ocultar los filtros de museo e investigación",
    museumCountryNames: { us: "Estados Unidos", fr: "Francia", uk: "Reino Unido" },
    researchFilterAria: "Filtrar por estado de investigación",
    researchFilterRowLabel: "Investigación:",
    researchFilterLabels: { all: "Todas", with: "Con investigación", without: "Sin investigación" },
    mechanismFilterLabel: "Mecanismo",
    mechanismFilterLabelActive: (n) => `Mecanismo (${n})`,
    mechanismFilterAria: "Filtrar por mecanismo de adquisición",
    mechanismClearLabel: "Limpiar selección",
    contextFlagLabels: {
      antiquarian_travel: "Viaje anticuario",
      art_market: "Mercado de arte",
      colonial_administration: "Administración colonial",
      french_colonial_context: "Contexto colonial francés",
      french_mandate: "Mandato francés",
      institutional_transfer: "Transferencia institucional",
      mariette_administration: "Administración de Mariette",
      military_seizure: "Confiscación militar",
      museum_funded_excavation: "Excavación financiada por el museo",
      napoleonic_transfer: "Transferencia napoleónica",
      non_colonial_context: "Sin mecanismo colonial",
      ottoman_authorization: "Autorización otomana",
      partage: "Partage (reparto de hallazgos)",
      private_collection: "Colección privada",
      private_excavation: "Excavación privada",
      punitive_expedition: "Expedición punitiva",
      settler_collection: "Colección de colonos",
      state_mission: "Misión estatal",
      state_sale: "Venta estatal",
      treaty_transfer: "Transferencia por tratado",
      undocumented_early_chain: "Cadena temprana sin documentar",
    },
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
    welcomeAboutP2: 'El patrón del mapa —de dónde viene cada pieza, a qué museo llegó— está completo en las 641 piezas. El detalle investigado es distinto: existe solo para un subconjunto, y no clasifica piezas como "robadas"; documenta el recorrido con fuentes, sin veredicto. La mayoría todavía no tiene esa investigación — es el estado por defecto, no una excepción.',
    welcomeSourcesHeading: "Fuentes y licencias",
    welcomeCreditsHeading: "Créditos",
    welcomeCreditsRepoPrefix: "Código fuente en",
    welcomeCreditsSitePrefix: "Más proyectos en",
    welcomeCloseAria: "Cerrar",
    welcomeFinish: "Entendido, ver el mapa",

    tooltipPieceCount: (count) => `${count} pieza${count === 1 ? "" : "s"}`,
    langToggleLabel: "EN",

    prevPieceAria: "Pieza anterior de este lugar",
    nextPieceAria: "Pieza siguiente de este lugar",
    piecePosition: (index, total) => `${index} de ${total}`,
    piecePrevLabel: "Anterior",
    pieceNextLabel: "Siguiente",

    imageExpandAria: "Ver imagen completa",
    imageCollapseAria: "Volver al tamaño recortado",

    countryResultsSubtitle: (n) => `${n} pieza${n === 1 ? "" : "s"} en los 3 museos, sin importar los filtros de arriba`,
    countryClickToggleLabel: "Click en el mapa",
    countryClickToggleAria: "Activar búsqueda por países haciendo click en el mapa",
    countryClickNoteAria: "Sobre la búsqueda por país",
    countryClickNoteText: "Con esto prendido, click en cualquier país del globo muestra todas sus piezas en los 3 museos y atenúa el resto de las líneas del mapa para resaltar solo las de ese país. Pasar el mouse por encima antes de clickear muestra cuántas piezas hay (o si no hay ninguna).",
    tooltipCountryEmptySub: "Sin piezas en esta muestra",
    countryGroupMuseumHeader: (name, n) => `${name} (${n})`,

    tourSteps: [
      {
        title: "Bienvenida a Tracing Origins",
        text: "Un recorrido de 30 segundos por los controles del mapa, antes de explorar.",
      },
      {
        title: "Museos",
        text: "Prendé o apagá cada museo para filtrar sus piezas. El botón \"i\" explica cómo llegó su colección.",
      },
      {
        title: "Investigación",
        text: "Filtrá piezas con recorrido investigado, o por el mecanismo puntual de adquisición.",
      },
      {
        title: "Contador de piezas",
        text: "Cuántas piezas ves ahora mismo — es solo informativo, no un botón.",
      },
      {
        title: "Búsqueda por país",
        text: "Activá esto y clickeá cualquier país del globo para ver todas sus piezas.",
      },
      {
        title: "Contexto histórico",
        text: "Abrí esto para sumar territorios coloniales y rutas navales en un timeline de 1700 a 2020.",
      },
      {
        title: "¿Necesitás más info?",
        text: "Este botón vuelve a mostrar este tour, o abre el detalle completo del proyecto (fuentes, modelo de datos, créditos).",
      },
      {
        title: "Listo para explorar",
        text: "Clickeá un punto de origen para ver sus piezas, o una línea para seguir su recorrido hasta el museo.",
      },
    ],
    tourStepOf: (current, total) => `${current} de ${total}`,
    tourBack: "Atrás",
    tourNext: "Siguiente",
    tourStart: "Empezar",
    tourSkip: "Saltar tour",
    tourAria: "Tour guiado de la interfaz",
  },
  en: {
    museumInfoAria: (name) => `About the provenance of ${name}'s pieces`,
    museumNotes: {
      met: "The Met didn't hold territorial control over these pieces' places of origin — they arrived via the antiquities market, colonial-authorized excavations, and wealthy donors.",
      louvre: "Its departments cover mostly Egypt, the Middle East, and the Mediterranean. Sub-Saharan Africa and the Americas moved to the Musée du Quai Branly in 2006.",
      bm: "The most direct case of colonial administration: from military conquest (Rosetta Stone, Benin Bronzes) to excavations under Ottoman permit.",
      qb: "An ethnographic museum, not antiquities — covers Africa, the Americas, Asia, and Oceania (transferred from the Louvre in 2006). Arrived via private collectors and colonial officials, not excavation.",
    },
    pieceCounterAll: (n) => `${n} pieces`,
    pieceCounterFiltered: (visible, total) => `${visible} of ${total} pieces`,
    curatedNoteBasemap: "The basemap's borders and labels are Mapbox's default convention, not an editorial stance from this project.",
    curatedNoteTerritoriesPrefix: "Colonial territories: Seshat Global History Databank —",
    curatedNoteTerritoriesLicense: "(CC-BY 4.0).",
    curatedNoteRoutesPrefix: "Naval routes: Jones et al. (2007),",
    curatedNoteRoutesSuffix: "(CC-BY 3.0) — curated sample of 50 voyages, not every route from the period.",
    welcomeTriggerAria: "About this project",
    langToggleAria: "Switch to Spanish",
    contextDockLabel: "Historical context",
    legendUK: "United Kingdom",
    legendFR: "France",
    layerToggleTerritories: "Colonies",
    layerToggleRoutes: "Naval routes",
    layerNotes: {
      territories: "Shades UK and French colonial territory in the selected year. The US doesn't appear (see the Met's note) nor the British mandates of Iraq/Palestine — the source doesn't model them.",
      routes: "50 curated British and French ship routes, 1700-1900, from real navigation logbooks (CLIWOC). Doesn't include famous explorers' voyages like Cook or Bougainville.",
    },
    historicalEvents: [
      "The Met is founded — it acquires its first object that same year (a Roman sarcophagus). Early collection built through donations and market purchases, not territorial expansion.",
      "Purchases the Cesnola Collection (antiquities from Cyprus) — establishes the Met's reputation as a serious antiquities repository. Cesnola was the US consul in Cyprus; his excavation methods were controversial even at the time.",
      "The Met starts its own Egyptian Expedition (through 1935) — moves from funding other institutions' excavations (Egypt Exploration Fund, 1897-1906) to excavating directly, authorized by the Egyptian government of the time. The core of its ~30,000 Egyptian pieces comes from this period.",
      "Simultaneous territorial peak of both colonial empires — the UK reaches ~13.7 million sq mi (24% of the world's land area) and France ~12.5 million km², after absorbing League of Nations mandates over former German and Ottoman territory (Iraq, Palestine, Syria, Lebanon, Cameroon, Togo). Both powers held permanent seats on the newly founded League of Nations Council. This is why the timeline defaults to this year.",
      "The Musée du Quai Branly opens — the Louvre's Sub-Saharan Africa, Americas, Asia, and Oceania holdings (which never had their own curatorial department there) transfer to the new museum. Since then the Louvre stays concentrated on Egypt, the Middle East, the Mediterranean, and Europe, while Quai Branly covers the rest of the world — which is why both museums' lines on the map read as two halves of a single French collection.",
    ],
    timelineNoteAria: (label) => `About the ${label} layer`,
    timelineSliderAria: "Year of the colonial-territories map",
    timelineCaption: "These layers change with the year. The piece→museum lines don't: they're fixed, they don't represent a single point in time.",

    clusterUnknownOrigin: "Unidentified origin",
    clusterPieceCount: (n) => `${n} piece${n === 1 ? "" : "s"} from this location`,
    hasResearchBadgeAria: "Has a researched, cited journey",
    hasResearchLegend: "researched, cited journey (colored by museum)",
    museumFilterRowLabel: "Museums:",
    mobileFiltersToggleLabel: "Filters",
    mobileFiltersToggleAria: "Show or hide the museum and research filters",
    museumCountryNames: { us: "United States", fr: "France", uk: "United Kingdom" },
    researchFilterAria: "Filter by research status",
    researchFilterRowLabel: "Research:",
    researchFilterLabels: { all: "All", with: "With research", without: "Without research" },
    mechanismFilterLabel: "Mechanism",
    mechanismFilterLabelActive: (n) => `Mechanism (${n})`,
    mechanismFilterAria: "Filter by acquisition mechanism",
    mechanismClearLabel: "Clear selection",
    contextFlagLabels: {
      antiquarian_travel: "Antiquarian travel",
      art_market: "Art market",
      colonial_administration: "Colonial administration",
      french_colonial_context: "French colonial context",
      french_mandate: "French Mandate",
      institutional_transfer: "Institutional transfer",
      mariette_administration: "Mariette administration",
      military_seizure: "Military seizure",
      museum_funded_excavation: "Museum-funded excavation",
      napoleonic_transfer: "Napoleonic-era transfer",
      non_colonial_context: "No colonial mechanism",
      ottoman_authorization: "Ottoman authorization",
      partage: "Partage (division of finds)",
      private_collection: "Private collection",
      private_excavation: "Private excavation",
      punitive_expedition: "Punitive expedition",
      settler_collection: "Settler collection",
      state_mission: "State mission",
      state_sale: "State sale",
      treaty_transfer: "Treaty transfer",
      undocumented_early_chain: "Undocumented early chain",
    },
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
    welcomeAboutP2: 'The map\'s pattern —where each piece comes from, which museum it reached— is complete across all 641 pieces. The researched detail is different: it exists only for a subset, and doesn\'t classify pieces as "stolen"; it documents the journey with sources, no verdict. Most pieces don\'t have that research yet — that\'s the default state, not an exception.',
    welcomeSourcesHeading: "Sources & licenses",
    welcomeCreditsHeading: "Credits",
    welcomeCreditsRepoPrefix: "Source code on",
    welcomeCreditsSitePrefix: "More projects at",
    welcomeCloseAria: "Close",
    welcomeFinish: "Got it, see the map",

    tooltipPieceCount: (count) => `${count} piece${count === 1 ? "" : "s"}`,
    langToggleLabel: "ES",

    prevPieceAria: "Previous piece from this location",
    nextPieceAria: "Next piece from this location",
    piecePosition: (index, total) => `${index} of ${total}`,
    piecePrevLabel: "Previous",
    pieceNextLabel: "Next",

    imageExpandAria: "View full image",
    imageCollapseAria: "Back to cropped size",

    countryResultsSubtitle: (n) => `${n} piece${n === 1 ? "" : "s"} across all 3 museums, regardless of the filters above`,
    countryClickToggleLabel: "Click on the map",
    countryClickToggleAria: "Enable searching by country by clicking the map",
    countryClickNoteAria: "About searching by country",
    countryClickNoteText: "With this on, clicking any country on the globe shows all its pieces across the 3 museums and dims the rest of the map's lines to highlight only that country's. Hovering before you click shows how many pieces there are (or whether there are none).",
    tooltipCountryEmptySub: "No pieces in this sample",
    countryGroupMuseumHeader: (name, n) => `${name} (${n})`,

    tourSteps: [
      {
        title: "Welcome to Tracing Origins",
        text: "A 30-second walkthrough of the map's controls before you dive in.",
      },
      {
        title: "Museums",
        text: "Turn each museum on or off to filter its pieces. The \"i\" button explains how its collection got here.",
      },
      {
        title: "Research",
        text: "Filter pieces with a documented journey, or by the specific acquisition mechanism.",
      },
      {
        title: "Piece counter",
        text: "How many pieces you're seeing right now — it's informational only, not a button.",
      },
      {
        title: "Search by country",
        text: "Turn this on and click any country on the globe to see all its pieces.",
      },
      {
        title: "Historical context",
        text: "Open this to add colonial territories and naval routes on a 1700–2020 timeline.",
      },
      {
        title: "Need more info?",
        text: "This button brings this tour back, or opens the project's full detail (sources, data model, credits).",
      },
      {
        title: "Ready to explore",
        text: "Click an origin point to see its pieces, or a line to follow its journey to the museum.",
      },
    ],
    tourStepOf: (current, total) => `${current} of ${total}`,
    tourBack: "Back",
    tourNext: "Next",
    tourStart: "Start",
    tourSkip: "Skip tour",
    tourAria: "Guided interface tour",
  },
};
