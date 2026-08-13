import { useEffect } from "react";
import { useMap } from "react-leaflet";

/** Leaflet mide su contenedor al montar; cuando el panel lateral abre/cierra
 * el mapa cambia de ancho vía flexbox y hay que avisarle con invalidateSize,
 * si no los tiles quedan mal recortados hasta el próximo pan/zoom manual. */
export function ResizeHandler({ trigger }: { trigger: unknown }) {
  const map = useMap();

  useEffect(() => {
    const id = window.setTimeout(() => map.invalidateSize(), 50);
    return () => window.clearTimeout(id);
  }, [trigger, map]);

  return null;
}
