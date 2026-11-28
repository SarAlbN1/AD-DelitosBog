import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import type { Diapositiva } from "../slides/tipos";
import { Lamina } from "./Lamina";

const ESCALA = 0.16;

/** Vista general: miniaturas de todas las diapositivas, agrupadas por sección. */
export function Indice({
  diapositivas,
  actual,
  ir,
  cerrar,
}: {
  diapositivas: Diapositiva[];
  actual: number;
  ir: (i: number) => void;
  cerrar: () => void;
}) {
  const ref = useRef<HTMLButtonElement | null>(null);
  useEffect(() => ref.current?.scrollIntoView({ block: "center" }), []);
  const total = diapositivas.length;
  return (
    <div className="no-imprimir fixed inset-0 z-50 overflow-y-auto bg-[#0d1320]/97 px-10 py-8 backdrop-blur">
      <div className="mx-auto flex max-w-[1700px] items-center justify-between text-white">
        <h2 className="text-[22px] font-semibold">Índice de diapositivas</h2>
        <button
          onClick={cerrar}
          className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-slate-300 hover:bg-white/10"
          aria-label="Cerrar índice"
        >
          <X size={18} /> Cerrar (Esc)
        </button>
      </div>
      <div className="mx-auto mt-6 grid max-w-[1700px] grid-cols-[repeat(auto-fill,minmax(310px,1fr))] gap-6">
        {diapositivas.map((d, i) => (
          <button
            key={d.id}
            ref={i === actual ? ref : undefined}
            onClick={() => ir(i)}
            className={`group text-left ${i === actual ? "ring-2 ring-sky-400" : ""} rounded-lg p-1 hover:bg-white/5`}
          >
            <div
              className="overflow-hidden rounded-md bg-white shadow-lg"
              style={{ width: 1920 * ESCALA, height: 1080 * ESCALA }}
            >
              <div style={{ transform: `scale(${ESCALA})`, transformOrigin: "top left", width: 1920, height: 1080 }}>
                <Lamina d={d} numero={i + 1} total={total} impresion />
              </div>
            </div>
            <div className="mt-2 flex gap-2 text-[13.5px] text-slate-300">
              <span className="tabular font-semibold text-sky-300">{i + 1}</span>
              <span className="truncate">
                <span className="text-slate-500">{d.seccion} · </span>
                {d.titulo}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
