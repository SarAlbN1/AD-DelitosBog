import type { ReactNode } from "react";
import { usePosicion } from "../hooks/posicion";

interface Props {
  seccion: string;
  titulo: ReactNode;
  /** Idea central de la diapositiva, en una frase. */
  mensaje?: ReactNode;
  children: ReactNode;
}

/**
 * Marco común de las diapositivas de contenido: sección, título con su mensaje y pie numerado.
 * El área de contenido mide 1760 × 700 px dentro de un lienzo de 1920 × 1080.
 */
export function Marco({ seccion, titulo, mensaje, children }: Props) {
  const { numero, total } = usePosicion();
  return (
    <div className="lienzo flex flex-col px-20 pt-16 pb-10">
      <header>
        <div className="flex items-center gap-4 text-[18px] font-semibold uppercase tracking-[0.16em] text-azul">
          <span className="h-[3px] w-10 bg-azul" />
          {seccion}
        </div>
        <h1 className="mt-5 font-serif text-[54px] leading-[1.08] font-semibold text-tinta">{titulo}</h1>
        {mensaje && <p className="mt-4 max-w-[1500px] text-[27px] leading-[1.35] text-gris">{mensaje}</p>}
      </header>
      <main className="relative mt-9 min-h-0 flex-1">{children}</main>
      <footer className="mt-6 flex items-center justify-between border-t border-linea pt-4 text-[16px] text-suave">
        <span>Hurto a personas en Bogotá, 2020–2025 · Analítica de Datos · Pontificia Universidad Javeriana</span>
        <span className="tabular font-semibold text-gris">
          {numero} / {total}
        </span>
      </footer>
    </div>
  );
}
