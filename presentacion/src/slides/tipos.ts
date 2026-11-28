import type { ComponentType } from "react";

export interface PreguntaProbable {
  pregunta: string;
  respuesta: string;
}

/** Guion del expositor. No aparece en la diapositiva ni en el PDF. */
export interface Notas {
  /** Qué decir, en el orden en que se dice. */
  guion: string[];
  /** Ideas que no pueden quedar sin decir. */
  enfatizar: string[];
  /** Frase para pasar a la siguiente diapositiva. */
  transicion: string;
  /** Preguntas que podría hacer el profesor, con la respuesta sostenida por el informe. */
  preguntas?: PreguntaProbable[];
}

export interface Diapositiva {
  id: string;
  /** Sección de la exposición, para el índice y la cabecera. */
  seccion: string;
  /** Título corto, para el índice y el pie. */
  titulo: string;
  /** Minutos sugeridos. */
  minutos: number;
  /** Quién la expone. */
  expone: "Juan Diego" | "Sara" | "Ambos";
  Contenido: ComponentType;
  notas: Notas;
}
