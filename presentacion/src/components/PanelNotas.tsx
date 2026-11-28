import { Clock, MessageCircleQuestion, ArrowRightCircle, Star, User } from "lucide-react";
import type { Diapositiva } from "../slides/tipos";

/** Guion del expositor. Solo existe en pantalla: no se imprime ni entra en el PDF. */
export function PanelNotas({ d, numero, total }: { d: Diapositiva; numero: number; total: number }) {
  const n = d.notas;
  return (
    <aside className="no-imprimir flex h-full w-[440px] shrink-0 flex-col overflow-y-auto border-l border-white/10 bg-[#121926] px-6 py-5 text-[14.5px] leading-relaxed text-slate-200">
      <div className="text-[12px] font-semibold uppercase tracking-[0.14em] text-sky-300/80">
        Notas · {numero} de {total}
      </div>
      <h2 className="mt-1 text-[19px] font-semibold text-white">{d.titulo}</h2>
      <div className="mt-2 flex gap-4 text-[13px] text-slate-400">
        <span className="inline-flex items-center gap-1">
          <Clock size={14} /> {d.minutos} min
        </span>
        <span className="inline-flex items-center gap-1">
          <User size={14} /> {d.expone}
        </span>
      </div>

      <section className="mt-4 space-y-2">
        {n.guion.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </section>

      <section className="mt-5">
        <h3 className="mb-1 inline-flex items-center gap-2 text-[13px] font-semibold uppercase tracking-wider text-amber-300">
          <Star size={14} /> Enfatizar
        </h3>
        <ul className="list-disc space-y-1 pl-5">
          {n.enfatizar.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
      </section>

      <section className="mt-5">
        <h3 className="mb-1 inline-flex items-center gap-2 text-[13px] font-semibold uppercase tracking-wider text-emerald-300">
          <ArrowRightCircle size={14} /> Transición
        </h3>
        <p className="italic text-slate-300">{n.transicion}</p>
      </section>

      {n.preguntas && n.preguntas.length > 0 && (
        <section className="mt-5 pb-6">
          <h3 className="mb-2 inline-flex items-center gap-2 text-[13px] font-semibold uppercase tracking-wider text-sky-300">
            <MessageCircleQuestion size={14} /> Preguntas probables
          </h3>
          <div className="space-y-3">
            {n.preguntas.map((q, i) => (
              <div key={i}>
                <p className="font-semibold text-white">{q.pregunta}</p>
                <p className="text-slate-300">{q.respuesta}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </aside>
  );
}
