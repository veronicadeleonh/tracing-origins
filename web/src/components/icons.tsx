// Íconos SVG inline para botones solo-ícono. Decorativos (aria-hidden): el
// nombre accesible va en el aria-label del botón. Usan currentColor, así que
// heredan el color (y el hover) del botón que los contiene.
const BASE_PROPS = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  focusable: false,
} as const;

export function CloseIcon() {
  return (
    <svg {...BASE_PROPS}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

export function BackIcon() {
  return (
    <svg {...BASE_PROPS}>
      <path d="M15 5l-7 7 7 7" />
    </svg>
  );
}
