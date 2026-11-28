import { useEffect } from "react";
import type { Diapositiva } from "../slides/tipos";
import { Lamina } from "./Lamina";

declare global {
  interface Window {
    __PRESENTACION_LISTA__?: boolean;
  }
}

/** Todas las diapositivas, una por página de 1920 × 1080, sin controles, notas ni animaciones. */
export function VistaImpresion({ diapositivas, imprimir }: { diapositivas: Diapositiva[]; imprimir: boolean }) {
  useEffect(() => {
    let cancelado = false;
    const esperarImagenes = () =>
      Promise.all(
        Array.from(document.images).map((img) =>
          img.complete ? Promise.resolve() : new Promise<void>((ok) => {
            img.onload = () => ok();
            img.onerror = () => ok();
          }),
        ),
      );
    void (async () => {
      await document.fonts.ready;
      await esperarImagenes();
      await new Promise((ok) => requestAnimationFrame(() => requestAnimationFrame(ok)));
      if (cancelado) return;
      window.__PRESENTACION_LISTA__ = true;
      if (imprimir) window.print();
    })();
    return () => {
      cancelado = true;
    };
  }, [imprimir]);

  const total = diapositivas.length;
  return (
    <div className="bg-papel">
      {diapositivas.map((d, i) => (
        <section key={d.id} className="pagina-impresa" data-diapositiva={i + 1}>
          <Lamina d={d} numero={i + 1} total={total} impresion />
        </section>
      ))}
    </div>
  );
}
