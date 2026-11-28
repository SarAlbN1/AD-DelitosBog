/** Bloques de la exposición: qué diapositivas cubre cada uno. Quién habla y cuánto dura se calculan. */
export interface Bloque {
  numero: number;
  tema: string;
  /** Diapositivas, numeradas desde 1, ambas incluidas. */
  desde: number;
  hasta: number;
  /** La demo y las preguntas no cuentan en los 10 minutos de la presentación. */
  fueraDeLaPresentacion?: boolean;
}

/** Límites que fija el profesor: 15 minutos en total, de los que 5 son para el tablero. */
export const LIMITE_PRESENTACION = 10;
export const LIMITE_TOTAL = 15;

export const BLOQUES: Bloque[] = [
  { numero: 1, tema: "Introducción, pregunta y datos", desde: 1, hasta: 4 },
  { numero: 2, tema: "Serie, validación y modelos", desde: 5, hasta: 9 },
  { numero: 3, tema: "Resultados, validación, interpretación y límites", desde: 10, hasta: 14 },
  { numero: 4, tema: "Conclusiones", desde: 15, hasta: 15 },
  { numero: 5, tema: "Demo del tablero de Power BI", desde: 16, hasta: 16, fueraDeLaPresentacion: true },
  { numero: 6, tema: "Preguntas", desde: 17, hasta: 17, fueraDeLaPresentacion: true },
];
