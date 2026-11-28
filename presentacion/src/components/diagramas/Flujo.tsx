import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { useModo } from "../../hooks/modo";

interface Caja {
  x: number;
  y: number;
  w: number;
  h: number;
  titulo: string;
  detalle: string;
  tono: "dato" | "script" | "salida" | "producto";
}

const TONO = {
  dato: { fondo: "#fbf8f2", borde: "#cfc6b4", texto: "#14213d" },
  script: { fondo: "#e8eef6", borde: "#9fb6d3", texto: "#174778" },
  salida: { fondo: "#ffffff", borde: "#cfcac0", texto: "#14213d" },
  producto: { fondo: "#174778", borde: "#174778", texto: "#ffffff" },
};

// Etapas en el orden en que se ejecutan (docs/REPRODUCIBILIDAD.md, secciones 4 a 6).
const CAJAS: Caja[] = [
  { x: 0, y: 40, w: 270, h: 96, titulo: "data/raw/", detalle: "las cuatro fuentes originales", tono: "dato" },
  { x: 0, y: 200, w: 270, h: 96, titulo: "config/", detalle: "fuentes y protocolo", tono: "dato" },
  { x: 340, y: 40, w: 300, h: 96, titulo: "auditoria_datasets.py", detalle: "embudo, nulos, SHA-256", tono: "script" },
  { x: 340, y: 200, w: 300, h: 96, titulo: "preprocesamiento.py", detalle: "serie diaria y limpieza", tono: "script" },
  { x: 340, y: 360, w: 300, h: 96, titulo: "features.py · eda.py", detalle: "21 predictoras y EDA", tono: "script" },
  { x: 710, y: 40, w: 300, h: 96, titulo: "baselines.py", detalle: "4 comparadores y la barra", tono: "script" },
  { x: 710, y: 200, w: 300, h: 96, titulo: "evaluacion.py", detalle: "un solo arnés de evaluación", tono: "script" },
  { x: 710, y: 360, w: 300, h: 96, titulo: "estadisticos.py", detalle: "+ arboles.py, regresion.py", tono: "script" },
  { x: 1080, y: 120, w: 290, h: 96, titulo: "ajuste.py", detalle: "selección en 540 fechas", tono: "script" },
  { x: 1080, y: 280, w: 290, h: 96, titulo: "comparacion.py", detalle: "+ interpretacion.py", tono: "script" },
  { x: 1440, y: 200, w: 320, h: 96, titulo: "outputs/", detalle: "cada cifra, versionada", tono: "salida" },
  { x: 1440, y: 40, w: 320, h: 96, titulo: "Informe en LaTeX", detalle: "82 páginas y 4 apéndices", tono: "producto" },
  { x: 1440, y: 360, w: 320, h: 96, titulo: "Tablero de Power BI", detalle: "4 páginas", tono: "producto" },
];

const FLECHAS: [number, number][] = [
  [0, 2], [0, 3], [3, 4], [3, 5], [1, 6], [6, 7], [4, 7], [7, 8], [8, 9], [9, 10], [10, 11], [10, 12],
];

function centro(c: Caja, lado: "der" | "izq") {
  return { x: lado === "der" ? c.x + c.w : c.x, y: c.y + c.h / 2 };
}

/** Flujo de datos y scripts, de los archivos originales al informe y al tablero. */
export function DiagramaFlujo() {
  const { impresion } = useModo();
  const envolver = (k: number, hijo: ReactNode) =>
    impresion ? (
      <g key={k}>{hijo}</g>
    ) : (
      <motion.g key={k} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 + (CAJAS[k].x / 1440) * 0.8 }}>
        {hijo}
      </motion.g>
    );
  return (
    <svg width={1762} height={470} className="block" fontFamily="Inter Variable, sans-serif">
      <defs>
        <marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#8a919c" />
        </marker>
      </defs>
      {FLECHAS.map(([a, b], i) => {
        const A = CAJAS[a];
        const B = CAJAS[b];
        let p1 = centro(A, "der");
        let p2 = centro(B, "izq");
        if (A.x === B.x) {
          // Misma columna: flecha vertical.
          const abajo = B.y > A.y;
          p1 = { x: A.x + A.w / 2, y: abajo ? A.y + A.h : A.y };
          p2 = { x: B.x + B.w / 2, y: abajo ? B.y - 2 : B.y + B.h + 2 };
          return <line key={i} x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="#8a919c" strokeWidth={2} markerEnd="url(#punta)" />;
        }
        const mx = (p1.x + p2.x) / 2;
        return (
          <path key={i} d={`M${p1.x},${p1.y} C${mx},${p1.y} ${mx},${p2.y} ${p2.x - 3},${p2.y}`} fill="none" stroke="#8a919c" strokeWidth={2} markerEnd="url(#punta)" />
        );
      })}
      {CAJAS.map((c, k) =>
        envolver(
          k,
          <>
            <rect x={c.x} y={c.y} width={c.w} height={c.h} rx={12} fill={TONO[c.tono].fondo} stroke={TONO[c.tono].borde} strokeWidth={1.5} />
            <text x={c.x + 18} y={c.y + 38} fontSize={c.tono === "script" ? 18.5 : 21} fontWeight={700} fill={TONO[c.tono].texto} fontFamily={c.tono === "script" || c.tono === "dato" ? "JetBrains Mono Variable, monospace" : undefined}>
              {c.titulo}
            </text>
            <text x={c.x + 18} y={c.y + 68} fontSize={16.5} fill={c.tono === "producto" ? "#dbe5f2" : "#5b6472"}>
              {c.detalle}
            </text>
          </>,
        ),
      )}
    </svg>
  );
}
