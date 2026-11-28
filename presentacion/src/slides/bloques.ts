/** Bloques de la exposición: qué diapositivas cubre cada uno. Quién habla y cuánto dura se calculan. */
export interface Bloque {
  numero: number;
  tema: string;
  /** Diapositivas, numeradas desde 1, ambas incluidas. */
  desde: number;
  hasta: number;
}

export const BLOQUES: Bloque[] = [
  { numero: 1, tema: "Introducción, pregunta y datos", desde: 1, hasta: 6 },
  { numero: 2, tema: "Serie y análisis exploratorio", desde: 7, hasta: 10 },
  { numero: 3, tema: "Método: validación, métricas y modelos", desde: 11, hasta: 14 },
  { numero: 4, tema: "Implementación y decisiones", desde: 15, hasta: 16 },
  { numero: 5, tema: "Resultados e interpretación", desde: 17, hasta: 22 },
  { numero: 6, tema: "Limitaciones, conclusiones y cierre", desde: 23, hasta: 27 },
];
