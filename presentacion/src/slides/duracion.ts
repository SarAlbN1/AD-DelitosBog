import type { Diapositiva, Linea } from "./tipos";

/** Palabras por minuto de una exposición pausada en español. */
export const PALABRAS_POR_MINUTO = 135;

export const esAccion = (l: Linea): l is { accion: string } => typeof l !== "string";

/** Texto que se dice en voz alta en una diapositiva: el guion sin acotaciones, más la transición. */
export function textoHablado(d: Diapositiva): string[] {
  return [...d.notas.guion.filter((l): l is string => !esAccion(l)), d.notas.transicion].filter(Boolean);
}

/**
 * Minutos estimados de una diapositiva: palabras habladas a 135 por minuto, más 5 s para cambiar de
 * diapositiva y 3 s por acotación (se señala mientras se habla). Se redondea al cuarto de minuto.
 */
export function minutos(d: Diapositiva): number {
  if (d.anexo) return 0;
  if (d.minutosFijos !== undefined) return d.minutosFijos;
  const palabras = textoHablado(d).join(" ").split(/\s+/).filter(Boolean).length;
  const acciones = d.notas.guion.filter(esAccion).length;
  const bruto = palabras / PALABRAS_POR_MINUTO + 5 / 60 + (acciones * 3) / 60;
  return Math.max(0.25, Math.round(bruto * 4) / 4);
}
