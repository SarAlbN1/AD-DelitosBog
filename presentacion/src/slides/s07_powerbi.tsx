import { CalendarDays, Gauge, LineChart, MapPinned, MonitorPlay } from "lucide-react";
import { Panel, Rotulo } from "../components/piezas";
import { Revelar } from "../components/Revelar";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

// Páginas del tablero (powerbi/Tablero-DelitosBOG.Report, #106 y #159). Cada una responde una pregunta
// y trae una nota de hallazgo calculada por medida DAX: no hay cifras escritas a mano.
const PAGINAS = [
  {
    icono: Gauge,
    nombre: "Panorama",
    pregunta: "¿Cuánto hurto hay y hacia dónde va?",
    muestra: ["Víctimas por día, mes a mes", "Media diaria por año, con 2020 atípico y 2025 hasta octubre"],
  },
  {
    icono: CalendarDays,
    nombre: "¿Cuándo?",
    pregunta: "¿Qué días se concentra?",
    muestra: ["Reparto por día de la semana", "Mapa de calor día × mes", "Efecto del lunes festivo"],
  },
  {
    icono: MapPinned,
    nombre: "¿Dónde?",
    pregunta: "¿Qué localidades piden más atención?",
    muestra: ["Llamadas a la Línea 123: volumen frente a tasa", "Mapa de calor de la tasa por localidad"],
  },
  {
    icono: LineChart,
    nombre: "Pronóstico",
    pregunta: "¿Se puede anticipar el hurto?",
    muestra: ["Observado frente al mejor modelo, 184 días", "Error medio de cada modelo frente a la barra"],
  },
];

function Tablero() {
  return (
    <Marco
      seccion="Tablero de Power BI · demo en vivo"
      titulo="El tablero: las mismas cifras, para explorarlas"
      mensaje="Cuatro páginas que leen las salidas del proyecto (outputs/powerbi/), con un filtro de año común. Lo recorremos en vivo durante 5 minutos."
    >
      <div className="grid grid-cols-4 gap-7">
        {PAGINAS.map((p, i) => {
          const Icono = p.icono;
          return (
            <Revelar key={p.nombre} paso={i}>
              <div className="h-full rounded-[14px] border border-linea border-t-[6px] border-t-[#e2b52f] bg-white p-7">
                <div className="flex items-center justify-between">
                  <span className="font-serif text-[44px] leading-none font-semibold text-[#c4951a] tabular">{i + 1}</span>
                  <Icono size={34} strokeWidth={1.6} className="text-azul" />
                </div>
                <div className="mt-4 font-serif text-[32px] font-semibold">{p.nombre}</div>
                <div className="mt-1 text-[21px] leading-snug text-azul">{p.pregunta}</div>
                <ul className="mt-5 space-y-3 border-t border-linea pt-4 text-[20px] leading-snug">
                  {p.muestra.map((m) => (
                    <li key={m} className="flex gap-2">
                      <span className="mt-[9px] h-2 w-2 shrink-0 rounded-full bg-[#e2b52f]" />
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            </Revelar>
          );
        })}
      </div>
      <Revelar paso={4}>
        <Panel tono="azul" className="mt-8 flex items-center gap-6 px-8 py-6">
          <MonitorPlay size={40} strokeWidth={1.6} className="shrink-0 text-azul" />
          <div>
            <Rotulo className="text-azul">Cómo se alimenta</Rotulo>
            <p className="mt-1 text-[21px] leading-snug">
              Scripts del proyecto → <span className="font-mono text-[18px]">outputs/powerbi/*.csv</span> → Power Query →
              modelo en estrella con medidas DAX → cuatro páginas. Cada página trae una nota de hallazgo calculada por
              medida, que cambia con el filtro.
            </p>
          </div>
        </Panel>
      </Revelar>
    </Marco>
  );
}

export const POWERBI: Diapositiva[] = [
  {
    id: "powerbi",
    seccion: "Tablero de Power BI",
    titulo: "Demo del tablero de Power BI",
    minutosFijos: 5,
    expone: "Sara",
    Contenido: Tablero,
    notas: {
      guion: [
        { accion: "Sara: Alt + Tab a Power BI Desktop, ya abierto y actualizado, en la página Panorama." },
        "El tablero lee las mismas salidas del proyecto, así que sus cifras son las del informe. Tiene cuatro páginas y un filtro de año común.",
        { accion: "Panorama: señalar la serie mes a mes y la media diaria por año." },
        "Panorama responde cuánto hurto hay y hacia dónde va: la serie mensual, la media diaria por año y la nota que advierte que 2020 es atípico y que 2025 llega hasta octubre.",
        { accion: "Cambiar el filtro de año a 2023 y volver a todos los años." },
        "Con el filtro de año, las cifras y la nota de hallazgo se recalculan.",
        { accion: "Página ¿Cuándo?: señalar el reparto por día y el mapa de calor día × mes." },
        "La página ¿Cuándo? muestra el ciclo semanal, el mapa de calor por día y mes, y el efecto del lunes festivo.",
        { accion: "Página ¿Dónde?: señalar volumen frente a tasa y el mapa." },
        "¿Dónde? es la parte territorial, con la Línea 123. El orden por número de llamadas y por tasa cambia por completo: Kennedy es la primera por número y la decimotercera por tasa. Las tasas altas se concentran en el centro, que recibe mucha población flotante.",
        { accion: "Página Pronóstico: señalar lo observado frente al mejor modelo y el error por modelo." },
        "Y Pronóstico compara lo observado con el mejor modelo en los 184 días de evaluación, y el error medio de cada modelo frente a la barra.",
      ],
      enfatizar: [
        "El tablero no calcula cifras propias: lee outputs/powerbi/, así que coincide con el informe.",
        "La parte territorial es de la Línea 123: describe llamadas, no hechos, y ningún orden mide peligrosidad.",
      ],
      transicion: "Con esto terminamos. Muchas gracias; quedamos atentos a sus preguntas.",
      preguntas: [
        {
          pregunta: "¿Por qué el tablero no pronostica por localidad?",
          respuesta: "Porque el registro de la Policía no trae la localidad. Lo territorial sale de la Línea 123, que cuenta llamadas tramitadas, y no se usa para modelar.",
        },
      ],
    },
  },
];
