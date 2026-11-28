import { createContext, useContext } from "react";

export interface Posicion {
  numero: number;
  total: number;
}

export const PosicionContext = createContext<Posicion>({ numero: 1, total: 1 });
export const usePosicion = (): Posicion => useContext(PosicionContext);
