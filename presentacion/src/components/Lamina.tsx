import { PosicionContext } from "../hooks/posicion";
import { ProveedorModo } from "../hooks/modo";
import type { Diapositiva } from "../slides/tipos";

/** Una diapositiva a tamaño nativo (1920 × 1080), con su número y su modo. */
export function Lamina({
  d,
  numero,
  total,
  impresion = false,
}: {
  d: Diapositiva;
  numero: number;
  total: number;
  impresion?: boolean;
}) {
  const { Contenido } = d;
  return (
    <ProveedorModo impresion={impresion}>
      <PosicionContext.Provider value={{ numero, total, anexo: d.anexo }}>
        <Contenido />
      </PosicionContext.Provider>
    </ProveedorModo>
  );
}
