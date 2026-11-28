import { createContext, useContext } from "react";

export interface Posicion {
  numero: number;
  total: number;
  /** Diapositiva de respaldo, después de «Preguntas». */
  anexo?: boolean;
}

export const PosicionContext = createContext<Posicion>({ numero: 1, total: 1 });
export const usePosicion = (): Posicion => useContext(PosicionContext);
