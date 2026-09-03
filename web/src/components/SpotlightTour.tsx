import { useCallback, useEffect, useLayoutEffect, useState, type CSSProperties } from "react";
import { STRINGS, type Lang } from "../i18n";
import { TOUR_STEPS } from "../data/tourSteps";

type SpotlightTourProps = {
  lang: Lang;
  onClose: () => void;
  onOpenInfo: () => void;
};

// Radio de esquinas del "agujero" del spotlight y margen alrededor del
// elemento resaltado -- separados de CALLOUT_WIDTH/MARGIN porque cambian por
// motivos distintos (uno es estético, el otro es "que no tape el elemento").
const HOLE_PADDING = 8;
const HOLE_RADIUS = 10;
const CALLOUT_WIDTH = 300;
// Alto estimado del callout, usado solo para decidir si entra arriba/abajo
// del elemento resaltado -- no es el alto real (varía según el texto), es
// una aproximación conservadora para la decisión de posicionamiento.
const CALLOUT_HEIGHT_ESTIMATE = 170;
const VIEWPORT_MARGIN = 16;

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

function measure(selector: string | null): Rect | null {
  if (!selector) return null;
  // querySelector solo devolvería el primer match en orden de DOM, sin
  // importar si está visible -- rompía el paso del contador de piezas
  // (`.piece-counter`, ver tourSteps.ts): esa clase la comparten
  // `.piece-counter-top` (primero en el DOM, pero `display:none` fuera de
  // mobile) y `.piece-counter-inline` (la que de verdad se ve en desktop),
  // así que el spotlight terminaba midiendo un elemento de tamaño cero y no
  // resaltaba nada. Recorremos todos los matches y usamos el primero con
  // tamaño real -- más robusto que apuntar el selector a una clase
  // específica, porque sigue funcionando si el orden del DOM cambia.
  const candidates = document.querySelectorAll(selector);
  for (const el of candidates) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) {
      return { top: r.top, left: r.left, width: r.width, height: r.height };
    }
  }
  return null;
}

// Onboarding interactivo con spotlight (01/09) -- reemplaza la apertura
// automática de WelcomeModal en la primera visita (ver CLAUDE.md, feedback
// de usuarios de prueba: "se espera más un onboarding guiado que señale los
// diferentes filtros" en vez de un modal largo de texto). WelcomeModal se
// mantiene intacto, accesible vía el botón "?" (bienvenida + fuentes/
// licencias + créditos, para quien quiera leer todo con calma) -- decisión
// explícita de la usuaria, no un reemplazo total.
//
// Técnica del "agujero" (spotlight): un div posicionado exactamente sobre el
// elemento a resaltar, con `box-shadow: 0 0 0 9999px <oscuro>` -- el propio
// box-shadow, al ser tan grande, cubre el resto de la pantalla, dejando solo
// el área del div (transparente) sin oscurecer. Más simple que un SVG mask
// y no necesita conocer el tamaño del viewport de antemano. El overlay
// completo intercepta todos los clicks (pointer-events auto) para que no se
// pueda interactuar con la página de fondo mientras el tour está abierto --
// el spotlight es puramente visual, no vuelve clickeable al elemento
// resaltado durante el tour.
export function SpotlightTour({ lang, onClose, onOpenInfo }: SpotlightTourProps) {
  const s = STRINGS[lang];
  const [stepIndex, setStepIndex] = useState(0);
  const [rect, setRect] = useState<Rect | null>(null);
  // Ancho de viewport en estado propio (01/09, fix mobile) -- separado de
  // `rect` a propósito: los pasos sin elemento resaltado (intro/cierre,
  // rect=null) no dispararían un re-render en resize si solo dependiéramos
  // de `recompute()`, dejando el ancho del callout desactualizado tras
  // rotar el teléfono en esos 2 pasos.
  const [viewportWidth, setViewportWidth] = useState(() => window.innerWidth);

  const step = TOUR_STEPS[stepIndex];
  const stepText = s.tourSteps[stepIndex];
  const isFirst = stepIndex === 0;
  const isLast = stepIndex === TOUR_STEPS.length - 1;
  // CALLOUT_WIDTH (300px) es un máximo, no un tamaño fijo -- en un teléfono
  // angosto (ej. 320px de ancho) 300px + 2*VIEWPORT_MARGIN se pasaría del
  // viewport. Como el ancho se pasa como inline style, un @media query en
  // App.css no alcanza para pisarlo (el inline style siempre gana) -- tiene
  // que calcularse acá.
  const calloutWidth = Math.min(CALLOUT_WIDTH, viewportWidth - VIEWPORT_MARGIN * 2);

  const recompute = useCallback(() => {
    setRect(measure(step.selector));
  }, [step.selector]);

  useLayoutEffect(() => {
    recompute();
  }, [recompute]);

  useEffect(() => {
    const onResize = () => {
      recompute();
      setViewportWidth(window.innerWidth);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [recompute]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const goNext = useCallback(() => {
    if (isLast) {
      onClose();
    } else {
      setStepIndex((i) => i + 1);
    }
  }, [isLast, onClose]);

  const goBack = useCallback(() => {
    setStepIndex((i) => Math.max(0, i - 1));
  }, []);

  // Posición del callout: centrado si no hay elemento resaltado (intro/
  // cierre); si hay, debajo del elemento por default, o arriba si no entra
  // debajo (ej. .year-timeline-handle, pegado al piso del mapa). Clamp
  // horizontal para que nunca quede recortado contra un borde del viewport
  // (ej. .welcome-trigger-btn, pegado a la esquina superior derecha).
  let calloutStyle: CSSProperties;
  if (!rect) {
    calloutStyle = { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
  } else {
    const spaceBelow = window.innerHeight - (rect.top + rect.height);
    const placeBelow = spaceBelow >= CALLOUT_HEIGHT_ESTIMATE + VIEWPORT_MARGIN || rect.top < CALLOUT_HEIGHT_ESTIMATE;
    const top = placeBelow
      ? rect.top + rect.height + HOLE_PADDING + 10
      : rect.top - HOLE_PADDING - 10 - CALLOUT_HEIGHT_ESTIMATE;
    const left = Math.min(
      Math.max(rect.left, VIEWPORT_MARGIN),
      window.innerWidth - calloutWidth - VIEWPORT_MARGIN,
    );
    calloutStyle = { top: Math.max(VIEWPORT_MARGIN, top), left };
  }

  return (
    <div className="spotlight-overlay" role="dialog" aria-modal="true" aria-label={s.tourAria}>
      {rect && (
        <div
          className="spotlight-hole"
          style={{
            top: rect.top - HOLE_PADDING,
            left: rect.left - HOLE_PADDING,
            width: rect.width + HOLE_PADDING * 2,
            height: rect.height + HOLE_PADDING * 2,
            borderRadius: HOLE_RADIUS,
          }}
        />
      )}
      <div className="spotlight-callout" style={{ ...calloutStyle, width: calloutWidth }}>
        <div className="spotlight-callout-progress">{s.tourStepOf(stepIndex + 1, TOUR_STEPS.length)}</div>
        <h2 className="spotlight-callout-title">{stepText.title}</h2>
        <p className="spotlight-callout-text">{stepText.text}</p>
        {isLast && (
          <button type="button" className="spotlight-callout-link" onClick={onOpenInfo}>
            {s.welcomeTriggerAria}
          </button>
        )}
        <div className={`spotlight-callout-footer${isLast ? " spotlight-callout-footer-solo" : ""}`}>
          {!isLast && (
            <button type="button" className="spotlight-callout-skip" onClick={onClose}>
              {s.tourSkip}
            </button>
          )}
          <div className="spotlight-callout-nav">
            {!isFirst && (
              <button type="button" className="spotlight-callout-btn" onClick={goBack}>
                {s.tourBack}
              </button>
            )}
            <button type="button" className="spotlight-callout-btn spotlight-callout-btn-primary" onClick={goNext}>
              {isLast ? s.welcomeFinish : isFirst ? s.tourStart : s.tourNext}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
