import { useEffect, useState, type RefObject } from "react";

/** Factor para que un lienzo de 1920 × 1080 quepa entero en el contenedor, sin recortes. */
export function useEscala(ref: RefObject<HTMLElement | null>, ancho = 1920, alto = 1080): number {
  const [escala, setEscala] = useState(0.5);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const medir = () => {
      const { width, height } = el.getBoundingClientRect();
      setEscala(Math.max(0.05, Math.min(width / ancho, height / alto)));
    };
    medir();
    const ro = new ResizeObserver(medir);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, ancho, alto]);
  return escala;
}
