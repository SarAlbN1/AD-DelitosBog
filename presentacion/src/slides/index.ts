import { APERTURA } from "./s01_apertura";
import { DATOS } from "./s02_datos";
import { METODO } from "./s03_metodo";
import { IMPLEMENTACION } from "./s04_implementacion";
import { RESULTADOS } from "./s05_resultados";
import { CIERRE } from "./s06_cierre";
import type { Diapositiva } from "./tipos";

/** Orden de la exposición. Cada bloque vive en su propio archivo. */
export const DIAPOSITIVAS: Diapositiva[] = [...APERTURA, ...DATOS, ...METODO, ...IMPLEMENTACION, ...RESULTADOS, ...CIERRE];
