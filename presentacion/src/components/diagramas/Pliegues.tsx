import { motion } from "framer-motion";
import { modelos } from "../../data/datos";
import { useModo } from "../../hooks/modo";

// Escala temporal: del 2020-01-01 al 2025-10-31.
const INICIO = Date.UTC(2020, 0, 1);
const FIN = Date.UTC(2025, 9, 31);
const ANCHO = 1460;
const X0 = 230;
const x = (iso: string) => {
  const [a, m, d] = iso.split("-").map(Number);
  return X0 + ((Date.UTC(a, m - 1, d) - INICIO) / (FIN - INICIO)) * ANCHO;
};

/** Seis pliegues de origen rodante dentro del entrenamiento y una evaluación final que se usa una vez. */
export function DiagramaPliegues() {
  const { impresion } = useModo();
  const filas = modelos.comparadores_pliegues;
  const alto = 64;
  const yFinal = 40 + filas.length * alto + 30;
  const anios = [2020, 2021, 2022, 2023, 2024, 2025];
  return (
    <svg width={1760} height={yFinal + 130} className="block">
      {anios.map((a) => (
        <g key={a}>
          <line x1={x(`${a}-01-01`)} x2={x(`${a}-01-01`)} y1={20} y2={yFinal + 70} stroke="#e3e1db" />
          <text x={x(`${a}-01-01`) + 6} y={16} fontSize={18} fill="#5b6472">
            {a}
          </text>
        </g>
      ))}
      {filas.map((f, i) => {
        const y = 40 + i * alto;
        const inicioEval = f.fin_entrenamiento;
        const contenido = (
          <>
            <text x={X0 - 18} y={y + 28} fontSize={20} textAnchor="end" fill="#14213d" fontWeight={600}>
              Pliegue {i + 1}
            </text>
            <rect x={X0} y={y + 8} width={x(inicioEval) - X0} height={30} rx={5} fill="#c9d5e4" />
            <rect x={x(inicioEval)} y={y + 8} width={x(f.fin_evaluacion) - x(inicioEval)} height={30} rx={5} fill="#174778" />
            <text x={x(inicioEval) - 12} y={y + 29} fontSize={17} fill="#14213d" textAnchor="end">
              entrena con {f.dias_entrenamiento.toLocaleString("es-CO")} días
            </text>
            <text x={x(f.fin_evaluacion) + 10} y={y + 29} fontSize={17} fill="#174778" fontWeight={600}>
              90 días
            </text>
          </>
        );
        return impresion ? (
          <g key={i}>{contenido}</g>
        ) : (
          <motion.g key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 + i * 0.12 }}>
            {contenido}
          </motion.g>
        );
      })}
      <g>
        <text x={X0 - 18} y={yFinal + 28} fontSize={20} textAnchor="end" fill="#14213d" fontWeight={700}>
          Evaluación final
        </text>
        <rect x={X0} y={yFinal + 8} width={x("2025-05-01") - X0} height={30} rx={5} fill="#c9d5e4" />
        <rect x={x("2025-05-01")} y={yFinal + 8} width={x("2025-10-31") - x("2025-05-01")} height={30} rx={5} fill="#b4441a" />
        <text x={x("2025-05-01") - 12} y={yFinal + 72} fontSize={18} fill="#b4441a" textAnchor="end">
          184 días, del 2025-05-01 al 2025-10-31: se calcula una sola vez
        </text>
      </g>
      <g transform={`translate(${X0}, ${yFinal + 100})`} fontSize={18} fill="#14213d">
        <rect width={26} height={16} rx={3} fill="#c9d5e4" y={-13} />
        <text x={36}>Entrenamiento: todo lo anterior al origen</text>
        <rect x={470} width={26} height={16} rx={3} fill="#174778" y={-13} />
        <text x={506}>Validación: elige hiperparámetros (540 fechas)</text>
        <rect x={1000} width={26} height={16} rx={3} fill="#b4441a" y={-13} />
        <text x={1036}>Evaluación final: solo se reporta</text>
      </g>
    </svg>
  );
}
