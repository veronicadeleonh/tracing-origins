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
// Reescrito el 19/08 a pedido directo de la usuaria ("incómodo de navegar,
// las imágenes no aportan valor, el texto es difícil de leer"). Versión
// anterior: carrusel de 4 slides (Siguiente/Atrás/puntitos) con capturas de
// pantalla de la app y una caja de texto de alto fijo (340px, con su propio
// scroll interno) — el scroll doble (el del modal + el de la caja de texto)
// era justamente la fricción de navegación reportada. Reemplazado por una
// sola página que se lee de corrido: sin slides, sin imágenes, tipografía
// más grande y con más contraste, modal más ancho. Las capturas viejas
// (web/public/onboarding/*.png) quedan sin usar — no se borraron los
// archivos, solo se dejó de referenciarlas acá.
export function WelcomeModal({ lang, onToggleLang, onClose }: WelcomeModalProps) {
  const s = STRINGS[lang];

  return (
    <div className="welcome-modal-backdrop" onClick={onClose}>
      <div
        className="welcome-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="welcome-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="welcome-modal-header">
          <div className="welcome-modal-heading-group">
            <span className="welcome-modal-emoji" aria-hidden="true">🏛️</span>
            <div>
              <h1 id="welcome-modal-title" className="welcome-modal-appname">Tracing Origins</h1>
              <p className="welcome-modal-slogan">{s.welcomeSlogan}</p>
            </div>
          </div>
          <div className="welcome-modal-header-actions">
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
          </div>
        </div>

        <div className="welcome-modal-body">
          <section className="welcome-modal-section">
            <h2 className="welcome-modal-heading">{s.welcomeHowToUseHeading}</h2>
            <ol className="welcome-steps">
              {s.welcomeSteps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </section>

          <section className="welcome-modal-section">
            <h2 className="welcome-modal-heading">{s.welcomeDataModelHeading}</h2>
            <p>{s.welcomeDataModelIntro}</p>
            <ol className="welcome-steps">
              {s.welcomeDataModelSteps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </section>

          <section className="welcome-modal-section">
            <h2 className="welcome-modal-heading">{s.welcomeAboutHeading}</h2>
            <p>{s.welcomeAboutP1}</p>
            <p>{s.welcomeAboutP2}</p>
          </section>

          {/* Antes vivía en un popover aparte ("i" junto al contador de
              piezas, .curated-note) -- retirado el 19/08 a pedido de la
              usuaria por redundante con este mismo botón "?". El contenido
              único que tenía ese popover (disclaimer del basemap, atribución
              de licencias) se muda acá, sin condicionarlo a qué capa esté
              prendida en el mapa en este momento -- a diferencia del
              popover viejo, este modal no sabe (ni necesita saber) el
              estado actual del timeline. */}
          <section className="welcome-modal-section">
            <h2 className="welcome-modal-heading">{s.welcomeSourcesHeading}</h2>
            <p>{s.curatedNoteBasemap}</p>
            <p>
              {s.curatedNoteTerritoriesPrefix}{" "}
              <a href="https://github.com/Seshat-Global-History-Databank/cliopatria" target="_blank" rel="noreferrer">
                Cliopatria
              </a>{" "}{s.curatedNoteTerritoriesLicense}
            </p>
            <p>
              {s.curatedNoteRoutesPrefix}{" "}
              <a href="https://doi.org/10.1594/PANGAEA.611088" target="_blank" rel="noreferrer">
                CLIWOC
              </a>{" "}{s.curatedNoteRoutesSuffix}
            </p>
          </section>
        </div>

        <div className="welcome-modal-footer">
          <button type="button" className="welcome-modal-btn welcome-modal-btn-primary" onClick={onClose}>
            {s.welcomeFinish}
          </button>
        </div>
      </div>
    </div>
  );
}
