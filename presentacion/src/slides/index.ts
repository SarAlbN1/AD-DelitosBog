import { APERTURA } from "./s01_apertura";
import { DATOS } from "./s02_datos";
import { METODO } from "./s03_metodo";
import { IMPLEMENTACION } from "./s04_implementacion";
import { RESULTADOS } from "./s05_resultados";
import { CIERRE } from "./s06_cierre";
import { POWERBI } from "./s07_powerbi";
import type { Diapositiva } from "./tipos";

const TODAS = [...APERTURA, ...DATOS, ...METODO, ...IMPLEMENTACION, ...RESULTADOS, ...CIERRE, ...POWERBI];
const porId = (id: string): Diapositiva => {
  const d = TODAS.find((x) => x.id === id);
  if (!d) throw new Error(`Diapositiva desconocida: ${id}`);
  return d;
};

/**
 * Orden de la exposición de 10 minutos, seguida de la demo de Power BI (5 min) y las preguntas.
 * El resto va después como anexo: no se expone, pero queda a mano para responder (tecla O).
 */
const EXPOSICION = [
  "portada", "problema", "contexto", "auditoria", "serie", "patrones", "validacion", "metricas", "modelos",
  "resultados", "pliegues", "sin-ganador", "interpretacion", "limitaciones", "conclusiones", "powerbi", "preguntas",
];

const ANEXO = TODAS.filter((d) => !EXPOSICION.includes(d.id)).map((d) => {
  if (!d.anexo) throw new Error(`«${d.id}» no está en la exposición ni marcada como anexo`);
  return { ...d, seccion: `Anexo · ${d.seccion}` };
});

export const DIAPOSITIVAS: Diapositiva[] = [...EXPOSICION.map(porId), ...ANEXO];

/** Diapositivas que se exponen (sin el anexo). */
export const EXPUESTAS = DIAPOSITIVAS.filter((d) => !d.anexo);
