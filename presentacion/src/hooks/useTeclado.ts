import { useEffect } from "react";

export interface Acciones {
  siguiente: () => void;
  anterior: () => void;
  primera: () => void;
  ultima: () => void;
  pantallaCompleta: () => void;
  notas: () => void;
  indice: () => void;
  cerrar: () => void;
}

/** Atajos: → ↓ Espacio AvPág siguiente; ← ↑ RePág anterior; Inicio/Fin; F pantalla completa; N notas; O índice. */
export function useTeclado(a: Acciones): void {
  useEffect(() => {
    const manejar = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return;
      const k = e.key;
      const mapa: Record<string, () => void> = {
        ArrowRight: a.siguiente,
        ArrowDown: a.siguiente,
        PageDown: a.siguiente,
        " ": a.siguiente,
        ArrowLeft: a.anterior,
        ArrowUp: a.anterior,
        PageUp: a.anterior,
        Home: a.primera,
        End: a.ultima,
        f: a.pantallaCompleta,
        F: a.pantallaCompleta,
        n: a.notas,
        N: a.notas,
        o: a.indice,
        O: a.indice,
        Escape: a.cerrar,
      };
      const accion = mapa[k];
      if (accion) {
        e.preventDefault();
        accion();
      }
    };
    window.addEventListener("keydown", manejar);
    return () => window.removeEventListener("keydown", manejar);
  }, [a]);
}
