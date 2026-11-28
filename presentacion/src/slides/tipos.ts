import type { ComponentType } from "react";

export interface PreguntaProbable {
  pregunta: string;
  respuesta: string;
}

/** Una línea del guion: texto que se dice o una acotación de lo que se hace en pantalla. */
export type Linea = string | { accion: string };

/** Guion del expositor. No aparece en la diapositiva ni en el PDF de la presentación. */
export interface Notas {
  /** Qué decir y qué hacer, en orden. Las cadenas se dicen en voz alta; `accion` es una acotación. */
  guion: Linea[];
  /** Ideas que no pueden quedar sin decir. */
  enfatizar: string[];
  /** Última frase que se dice: enlaza con la siguiente diapositiva o pasa la palabra. */
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
  /** Quién la expone. */
  expone: "Juan Diego" | "Sara" | "Ambos";
  Contenido: ComponentType;
  notas: Notas;
}
