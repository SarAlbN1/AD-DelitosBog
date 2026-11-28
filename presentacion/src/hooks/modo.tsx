import { createContext, useContext, type ReactNode } from "react";

/** En modo impresión no hay animaciones: todo se dibuja en su estado final. */
interface Modo {
  impresion: boolean;
}

const ModoContext = createContext<Modo>({ impresion: false });

export function ProveedorModo({ impresion, children }: { impresion: boolean; children: ReactNode }) {
  return <ModoContext.Provider value={{ impresion }}>{children}</ModoContext.Provider>;
}

export const useModo = (): Modo => useContext(ModoContext);

/** Las gráficas animan su entrada solo en pantalla. */
export const useAnimar = (): boolean => !useModo().impresion;
