import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronFirst,
  ChevronLast,
  ChevronLeft,
  ChevronRight,
  FileDown,
  LayoutGrid,
  Maximize,
  Minimize,
  NotebookText,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useEscala } from "../hooks/useEscala";
import { useTeclado } from "../hooks/useTeclado";
import type { Diapositiva } from "../slides/tipos";
import { Indice } from "./Indice";
import { Lamina } from "./Lamina";
import { PanelNotas } from "./PanelNotas";

const leerHash = (total: number): number => {
  const n = Number(window.location.hash.replace(/^#\/?/, ""));
  return Number.isInteger(n) && n >= 1 && n <= total ? n - 1 : 0;
};

function Boton({
  onClick,
  titulo,
  children,
  activo = false,
  deshabilitado = false,
}: {
  onClick: () => void;
  titulo: string;
  children: ReactNode;
  activo?: boolean;
  deshabilitado?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={titulo}
      aria-label={titulo}
      disabled={deshabilitado}
      className={`inline-flex h-9 items-center gap-2 rounded-md px-2.5 text-[13.5px] transition-colors disabled:opacity-30 ${
        activo ? "bg-sky-500/20 text-sky-200" : "text-slate-300 hover:bg-white/10 hover:text-white"
      }`}
    >
      {children}
    </button>
  );
}

/** Modo presentación: escala el lienzo, navega, muestra notas, índice y pantalla completa. */
export function Presentador({ diapositivas }: { diapositivas: Diapositiva[] }) {
  const total = diapositivas.length;
  const [i, setI] = useState(() => leerHash(total));
  const [notas, setNotas] = useState(false);
  const [indice, setIndice] = useState(false);
  const [completa, setCompleta] = useState(false);
  const [direccion, setDireccion] = useState(1);
  const escenario = useRef<HTMLDivElement | null>(null);
  const escala = useEscala(escenario);

  const ir = useCallback(
    (n: number) => {
      const destino = Math.max(0, Math.min(total - 1, n));
      setDireccion(destino >= i ? 1 : -1);
      setI(destino);
    },
    [i, total],
  );

  useEffect(() => {
    const h = `#/${i + 1}`;
    if (window.location.hash !== h) history.replaceState(null, "", h);
  }, [i]);

  useEffect(() => {
    const cambio = () => setCompleta(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", cambio);
    return () => document.removeEventListener("fullscreenchange", cambio);
  }, []);

  const pantallaCompleta = useCallback(() => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen();
  }, []);

  const exportar = useCallback(() => {
    window.open(`${window.location.pathname}?modo=impresion&imprimir=1`, "_blank");
  }, []);

  const acciones = useMemo(
    () => ({
      siguiente: () => !indice && ir(i + 1),
      anterior: () => !indice && ir(i - 1),
      primera: () => !indice && ir(0),
      ultima: () => !indice && ir(total - 1),
      pantallaCompleta,
      notas: () => setNotas((v) => !v),
      indice: () => setIndice((v) => !v),
      cerrar: () => setIndice(false),
    }),
    [i, indice, ir, total, pantallaCompleta],
  );
  useTeclado(acciones);

  const d = diapositivas[i];
  const progreso = ((i + 1) / total) * 100;

  return (
    <div className="flex h-full flex-col bg-[#1b2333]">
      <div className="no-imprimir h-[3px] w-full bg-white/5">
        <div className="h-full bg-sky-400 transition-[width] duration-300" style={{ width: `${progreso}%` }} />
      </div>

      <div className="flex min-h-0 flex-1">
        <div ref={escenario} className="relative min-w-0 flex-1 overflow-hidden" onClick={() => ir(i + 1)}>
          <div
            className="absolute top-1/2 left-1/2 shadow-[0_20px_60px_rgba(0,0,0,0.45)]"
            style={{
              width: 1920,
              height: 1080,
              transform: `translate(-50%, -50%) scale(${escala})`,
              transformOrigin: "center center",
            }}
          >
            <AnimatePresence mode="wait" initial={false} custom={direccion}>
              <motion.div
                key={d.id}
                custom={direccion}
                initial={{ opacity: 0, x: 24 * direccion }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -24 * direccion }}
                transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                style={{ width: 1920, height: 1080 }}
              >
                <Lamina d={d} numero={i + 1} total={total} />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
        {notas && <PanelNotas d={d} numero={i + 1} total={total} />}
      </div>

      <nav className="no-imprimir flex h-12 shrink-0 items-center justify-between border-t border-white/10 bg-[#121926] px-3">
        <div className="flex items-center gap-1">
          <Boton onClick={() => ir(0)} titulo="Primera diapositiva (Inicio)" deshabilitado={i === 0}>
            <ChevronFirst size={18} />
          </Boton>
          <Boton onClick={() => ir(i - 1)} titulo="Anterior (←)" deshabilitado={i === 0}>
            <ChevronLeft size={18} />
          </Boton>
          <span className="tabular min-w-[84px] text-center text-[14px] text-slate-200">
            {i + 1} / {total}
          </span>
          <Boton onClick={() => ir(i + 1)} titulo="Siguiente (→)" deshabilitado={i === total - 1}>
            <ChevronRight size={18} />
          </Boton>
          <Boton onClick={() => ir(total - 1)} titulo="Última diapositiva (Fin)" deshabilitado={i === total - 1}>
            <ChevronLast size={18} />
          </Boton>
          <span className="ml-3 hidden truncate text-[13.5px] text-slate-400 md:inline">
            {d.seccion} · {d.titulo}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Boton onClick={() => setIndice(true)} titulo="Índice (O)" activo={indice}>
            <LayoutGrid size={17} /> <span className="hidden lg:inline">Índice</span>
          </Boton>
          <Boton onClick={() => setNotas((v) => !v)} titulo="Notas del expositor (N)" activo={notas}>
            <NotebookText size={17} /> <span className="hidden lg:inline">Notas</span>
          </Boton>
          <Boton onClick={exportar} titulo="Exportar a PDF">
            <FileDown size={17} /> <span className="hidden lg:inline">PDF</span>
          </Boton>
          <Boton onClick={pantallaCompleta} titulo="Pantalla completa (F)" activo={completa}>
            {completa ? <Minimize size={17} /> : <Maximize size={17} />}
          </Boton>
        </div>
      </nav>

      {indice && (
        <Indice
          diapositivas={diapositivas}
          actual={i}
          ir={(n) => {
            ir(n);
            setIndice(false);
          }}
          cerrar={() => setIndice(false)}
        />
      )}
    </div>
  );
}
