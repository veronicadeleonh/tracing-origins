import type { Lang } from "../i18n";

const OPTIONS: { value: Lang; label: string; name: string }[] = [
  { value: "es", label: "ES", name: "Español" },
  { value: "en", label: "EN", name: "English" },
];

interface LangSwitchProps {
  lang: Lang;
  onSelect: (lang: Lang) => void;
  ariaLabel: string;
  className?: string;
}

// Control segmentado ES | EN: muestra siempre los dos idiomas con el activo
// resaltado (antes el botón mostraba el idioma AL QUE se cambiaba, lo que
// confundía). Cada opción lleva su propio `lang` para que el lector de
// pantalla pronuncie "Español"/"English" con la voz correcta.
export function LangSwitch({ lang, onSelect, ariaLabel, className = "" }: LangSwitchProps) {
  return (
    <div className={`lang-switch ${className}`.trim()} role="group" aria-label={ariaLabel}>
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          type="button"
          lang={o.value}
          className={`lang-switch-btn${lang === o.value ? " active" : ""}`}
          aria-pressed={lang === o.value}
          aria-label={o.name}
          onClick={() => lang !== o.value && onSelect(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
