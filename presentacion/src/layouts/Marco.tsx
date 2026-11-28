import type { ReactNode } from "react";
import { usePosicion } from "../hooks/posicion";

interface Props {
  seccion: string;
  titulo: ReactNode;
  /** Idea central de la diapositiva, en una frase. */
  mensaje?: ReactNode;
  children: ReactNode;
}

/** Color de acento de cada bloque de la exposición: identifica en qué parte va la charla. */
export function acentoDe(seccion: string): string {
  const s = seccion.toLowerCase();
  if (/(contexto|planteamiento|justificación|objetivos)/.test(s)) return "#f2b950";
  if (/(datos|análisis exploratorio)/.test(s)) return "#5cc49a";
  if (/(fundamentos|metodología|modelos)/.test(s)) return "#9cc3f0";
  if (/(arquitectura|decisiones)/.test(s)) return "#c4a8f0";
  if (/(resultados|validación|interpretación)/.test(s)) return "#f28c5e";
  if (/(tablero|power bi)/.test(s)) return "#f7d154";
  return "#e8d27a";
}

/**
 * Marco común de las diapositivas de contenido: cabecera azul con sección, título y mensaje, cuerpo
 * sobre papel cálido y pie numerado. El área de contenido mide 1760 px de ancho.
 */
export function Marco({ seccion, titulo, mensaje, children }: Props) {
  const { numero, total, anexo } = usePosicion();
  const acento = acentoDe(seccion);
  const etiqueta = anexo ? `Anexo · ${seccion}` : seccion;
  return (
    <div className="lienzo flex flex-col">
      <header className="relative overflow-hidden bg-[#14325c] px-20 pt-12 pb-9 text-white">
        {/* Trama discreta en la esquina: da textura sin competir con el contenido. */}
        <svg className="pointer-events-none absolute top-0 right-0 opacity-[0.12]" width="520" height="100%" aria-hidden>
          <defs>
            <pattern id={`trama-${numero}`} width="26" height="26" patternUnits="userSpaceOnUse">
              <circle cx="3" cy="3" r="2" fill="#ffffff" />
            </pattern>
          </defs>
          <rect width="520" height="100%" fill={`url(#trama-${numero})`} />
        </svg>
        <div className="relative flex items-center gap-4 text-[18px] font-semibold uppercase tracking-[0.16em]" style={{ color: acento }}>
          <span className="h-[3px] w-10" style={{ background: acento }} />
          {etiqueta}
          <span className="ml-auto tabular text-white/55">
            {String(numero).padStart(2, "0")} / {total}
          </span>
        </div>
        <h1 className="relative mt-4 max-w-[1700px] font-serif text-[52px] leading-[1.08] font-semibold">{titulo}</h1>
        {mensaje && <p className="relative mt-3 max-w-[1560px] text-[25px] leading-[1.35] text-[#c9d8ec]">{mensaje}</p>}
        <div className="absolute right-0 bottom-0 left-0 h-[6px]" style={{ background: acento }} />
      </header>
      <main className="relative min-h-0 flex-1 px-20 pt-8">{children}</main>
      <footer className="mx-20 mt-4 mb-6 flex items-center justify-between border-t border-[#d9d2c3] pt-3 text-[16px] text-suave">
        <span>Hurto a personas en Bogotá, 2020–2025 · Analítica de Datos · Pontificia Universidad Javeriana</span>
        <span className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: acento }} />
          Juan Diego Rojas · Sara Albarracín
        </span>
      </footer>
    </div>
  );
}
