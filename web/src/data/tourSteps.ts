// Onboarding interactivo con spotlight (01/09, pedido de la usuaria a partir
// de feedback de usuarios de prueba: "el usuario se espera más un onboarding
// guiado que señale los diferentes filtros" en vez del modal largo de texto
// -- ver CLAUDE.md). Reemplaza la apertura automática del modal en la
// primera visita (`WelcomeModal.tsx` se mantiene intacto, accesible vía el
// botón "?", ver App.tsx).
//
// `selector` es un CSS selector sobre un elemento YA en el DOM -- `null`
// marca un paso "centrado" (intro/cierre), sin resaltar nada puntual. Solo
// viven acá los selectores (no traducibles); el texto de cada paso vive en
// `i18n.ts` (`tourSteps`), indexado por posición en este array -- mismo
// patrón que `HISTORICAL_EVENTS`/`historicalEventLabels`.
export interface TourStep {
  selector: string | null;
}

export const TOUR_STEPS: TourStep[] = [
  { selector: null }, // 0: intro
  { selector: ".museum-toggles" }, // 1
  { selector: ".research-filter-row" }, // 2
  { selector: ".piece-counter" }, // 3
  { selector: ".country-click-panel" }, // 4
  { selector: ".year-timeline-handle" }, // 5
  { selector: ".welcome-trigger-btn" }, // 6
  { selector: null }, // 7: cierre
];
