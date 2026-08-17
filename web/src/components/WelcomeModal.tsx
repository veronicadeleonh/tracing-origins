import { useState } from "react";
import { STRINGS, type Lang } from "../i18n";

type WelcomeModalProps = {
  lang: Lang;
  onToggleLang: () => void;
  onClose: () => void;
};

// Nivel 1 de las "notas de contexto en la UI" (ver CLAUDE.md, decidido el
// 16/08, implementado el 17/08): a diferencia de MUSEUM_NOTES/LAYER_NOTES
// (nivel 2 y 3, popovers chicos ancladas a un botón "i"), esto es contenido
// de proyecto completo — se abre solo la primera visita (localStorage, ver
// App.tsx) y después queda accesible vía un botón persistente. No reemplaza
// el popover chico "Muestra curada" que ya vivía en .curated-note — ese se
// deja como acceso rápido, este modal repite/expande el mismo mensaje con
// más contexto (decidido con el usuario el 17/08).
//
// Dividido en slides cortas en vez de un solo bloque largo (reportado como
// "overwhelming" por el usuario el 17/08) — la primera es solo bienvenida +
// slogan, sin instrucciones todavía, para no recibir al visitante con un
// muro de texto. Textos traducidos vía i18n.ts (toggle ES/EN, 17/08) —
// el botón de idioma de App.tsx queda tapado por el backdrop (z-index más
// alto) mientras el modal está abierto, así que este modal necesita su
// propio botón de idioma adentro (mismo onToggleLang que el de afuera,
// no un estado propio) para que el onboarding en sí sea cambiable.
//
// Imágenes (17/08): capturas reales de la app (no mockups de Figma),
// recortadas y redimensionadas a mano a partir de screenshots que sacó el
// usuario. Viven en web/public/onboarding/ (mismo patrón que
// colonial_overlay.geojson: assets estáticos servidos tal cual, no
// bundleados). Dos tratamientos de CSS distintos según el contenido:
// - hero.png / how-to-use.png: fotos del globo, sin texto crítico —
//   .welcome-slide-image con object-fit:cover, se puede recortar el borde
//   sin perder sentido.
// - data-model.png / piece-list.png: capturas de UI con texto (el timeline
//   de una pieza, la lista de un cluster) — cover les cortaba contenido a
//   la mitad de una oración (reportado por el usuario el 17/08 con el
//   ejemplo de "Modelo de datos"). Llevan la clase extra
//   welcome-slide-image--contain (object-fit:contain, mismo fondo que la
//   tarjeta) para que se vean completas siempre, aunque quede algo de aire
//   a los costados — la caja (.welcome-slide-image) mide lo mismo en las 4
//   slides de cualquier forma.
export function WelcomeModal({ lang, onToggleLang, onClose }: WelcomeModalProps) {
  const s = STRINGS[lang];
  const [slide, setSlide] = useState(0);

  const slides = [
    (
      <div className="welcome-slide-hero" key="hero">
        <img className="welcome-slide-image" src={`${import.meta.env.BASE_URL}onboarding/hero.png`} alt="" />
        <div className="welcome-slide-emoji">🏛️</div>
        <h1 className="welcome-slide-appname">Tracing Origins</h1>
        <p className="welcome-slide-slogan">{s.welcomeSlogan}</p>
      </div>
    ),
    (
      <section className="welcome-modal-section" key="how">
        <img
          className="welcome-slide-image"
          src={`${import.meta.env.BASE_URL}onboarding/how-to-use.png`}
          alt={s.welcomeHowToUseHeading}
        />
        <h2 className="welcome-modal-heading">{s.welcomeHowToUseHeading}</h2>
        <ol className="welcome-steps">
          {s.welcomeSteps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </section>
    ),
    (
      <section className="welcome-modal-section" key="model">
        <img
          className="welcome-slide-image welcome-slide-image--contain"
          src={`${import.meta.env.BASE_URL}onboarding/data-model.png`}
          alt={s.welcomeDataModelHeading}
        />
        <h2 className="welcome-modal-heading">{s.welcomeDataModelHeading}</h2>
        <p>{s.welcomeDataModelIntro}</p>
        <ol className="welcome-steps">
          {s.welcomeDataModelSteps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </section>
    ),
    (
      <section className="welcome-modal-section" key="about">
        <img
          className="welcome-slide-image welcome-slide-image--contain"
          src={`${import.meta.env.BASE_URL}onboarding/piece-list.png`}
          alt=""
        />
        <h2 className="welcome-modal-heading">{s.welcomeAboutHeading}</h2>
        <p>{s.welcomeAboutP1}</p>
        <p>{s.welcomeAboutP2}</p>
      </section>
    ),
  ];

  const isLast = slide === slides.length - 1;
  const isFirst = slide === 0;

  return (
    <div className="welcome-modal-backdrop" onClick={onClose}>
      <div
        className="welcome-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="welcome-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="welcome-modal-lang-btn"
          aria-label={s.langToggleAria}
          onClick={onToggleLang}
        >
          {s.langToggleLabel}
        </button>
        <button
          type="button"
          className="icon-btn welcome-modal-close"
          aria-label={s.welcomeCloseAria}
          onClick={onClose}
        >
          ✕
        </button>

        <div id="welcome-modal-title" className="welcome-modal-body">
          {slides[slide]}
        </div>

        <div className="welcome-modal-footer">
          <div className="welcome-modal-dots">
            {slides.map((_, i) => (
              <span key={i} className={`welcome-modal-dot${i === slide ? " active" : ""}`} />
            ))}
          </div>
          <div className="welcome-modal-nav">
            {!isFirst && (
              <button
                type="button"
                className="welcome-modal-btn welcome-modal-btn-secondary"
                onClick={() => setSlide((prev) => prev - 1)}
              >
                {s.welcomeBack}
              </button>
            )}
            <button
              type="button"
              className="welcome-modal-btn welcome-modal-btn-primary"
              onClick={() => (isLast ? onClose() : setSlide((prev) => prev + 1))}
            >
              {isLast ? s.welcomeFinish : s.welcomeNext}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
