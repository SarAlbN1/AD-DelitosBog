import { Boxes, FlaskConical, Fingerprint, ShieldCheck } from "lucide-react";
import { DiagramaFlujo } from "../components/diagramas/Flujo";
import { Revelar } from "../components/Revelar";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

function Arquitectura() {
  const garantias = [
    { icono: ShieldCheck, t: "Un solo arnés", d: "Comparadores y modelos se evalúan con la misma función, en los mismos días." },
    { icono: FlaskConical, t: "216 pruebas automáticas", d: "152 del modelado, con datos sintéticos: fuga, pliegues, selección y métricas." },
    { icono: Fingerprint, t: "Huella de cada corrida", d: "SHA-256 de configuración, modelo, semilla, datos y versión: misma huella, mismas cifras." },
    { icono: Boxes, t: "Imagen de Docker", d: "Python 3.12.8 y versiones exactas: las cifras del informe salen de ese entorno." },
  ];
  return (
    <Marco
      seccion="Arquitectura e implementación"
      titulo="Del archivo original a la cifra del informe, sin pasos a mano"
      mensaje="Cada etapa es un script que lee la etapa anterior y escribe en outputs/. El informe y el tablero solo leen de ahí."
    >
      <Revelar>
        <DiagramaFlujo />
      </Revelar>
      <div className="mt-4 grid grid-cols-4 gap-8">
        {garantias.map((g, i) => {
          const Icono = g.icono;
          return (
            <Revelar key={g.t} paso={i + 2}>
              <div className="border-t-[3px] border-azul pt-3">
                <div className="flex items-center gap-2 text-[21px] font-semibold">
                  <Icono size={22} className="text-azul" /> {g.t}
                </div>
                <p className="mt-1 text-[18px] leading-snug text-gris">{g.d}</p>
              </div>
            </Revelar>
          );
        })}
      </div>
      <div className="mt-4 text-[17px] text-suave">
        Python · pandas · statsmodels · scikit-learn · matplotlib · GeoPandas · pytest · Docker · LaTeX · Power BI · GitHub
      </div>
    </Marco>
  );
}

const DECISIONES: [string, string, string, string][] = [
  ["Fuente de la variable objetivo (D-01)", "Registro de la Policía, 2020–2025", "Una víctima por fila, resolución diaria, 741.986 registros", "Agregado de MinDefensa 2018–2025: 2.922 filas, una por día"],
  ["Fin de la serie", "2025-10-31", "Noviembre y diciembre caen a la mitad sin que baje la Línea 123", "Evaluar sobre una caída que no es del fenómeno"],
  ["Barra a superar (D-04)", "El mejor de 4 comparadores en la evaluación", "El orden de los comparadores cambia con la ventana", "Fijar un comparador de antemano"],
  ["Horizonte (D-04)", "Un día", "Todas las predictoras disponibles sin suponer retrasos de publicación", "7 o 14 días: queda como trabajo futuro"],
  ["Tratamiento de 2020", "Marcado y con prueba de sensibilidad", "No se puede separar menos hechos de menos registro", "Eliminar el año"],
  ["Entorno de las cifras", "Una imagen de Docker", "El gradiente cambia hasta 0,7 de MAE entre sistemas", "Cifras de cualquier equipo"],
  ["Interpretación", "Importancia por permutación agrupada", "Variables sustitutas, como los rezagos 7 y 14, se suplen entre sí", "Permutar cada variable por separado"],
];

function Decisiones() {
  return (
    <Marco
      seccion="Decisiones técnicas"
      titulo="Cada decisión tiene una razón y una alternativa descartada"
      mensaje="Las decisiones de datos y de evaluación están registradas en docs/decisiones.md y en sus issues, antes de ver los resultados."
    >
      <div className="rounded-[14px] border border-linea bg-white px-8 py-2">
      <table className="w-full text-[22px]">
        <thead>
          <tr className="border-b-2 border-tinta text-left text-[15px] uppercase tracking-[0.08em] text-gris">
            <th className="w-[330px] py-2 font-semibold">Decisión</th>
            <th className="w-[380px] py-2 font-semibold">Qué se eligió</th>
            <th className="py-2 font-semibold">Por qué</th>
            <th className="w-[420px] py-2 font-semibold">Alternativa descartada</th>
          </tr>
        </thead>
        <tbody>
          {DECISIONES.map(([d, q, p, a]) => (
            <tr key={d} className="border-b border-linea align-top">
              <td className="py-[14px] pr-5 font-semibold">{d}</td>
              <td className="py-[14px] pr-5 text-azul">{q}</td>
              <td className="py-[14px] pr-5 leading-snug">{p}</td>
              <td className="py-[14px] leading-snug text-gris">{a}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </Marco>
  );
}

export const IMPLEMENTACION: Diapositiva[] = [
  {
    id: "arquitectura",
    seccion: "Implementación",
    titulo: "Arquitectura y reproducibilidad",
    expone: "Juan Diego",
    Contenido: Arquitectura,
    notas: {
      guion: [
        "Gracias, Sara. De izquierda a derecha: los datos, los scripts en el orden en que se ejecutan y los productos, el informe y el tablero de Power BI.",
        "Lo importante es que no hay pasos a mano. Cada cifra del informe sale de un archivo de outputs que produce un script.",
        { accion: "Señalar las cuatro garantías de abajo." },
        "Cuatro garantías: un solo arnés de evaluación, 216 pruebas automáticas, una huella por corrida y una imagen de Docker, porque el gradiente cambia hasta 0,7 de MAE entre sistemas operativos.",
      ],
      enfatizar: [
        "Antes de escribir sus tablas, comparacion.py recalcula cada métrica desde las predicciones guardadas y se detiene si alguna no coincide: así se cotejaron 616 cifras.",
      ],
      transicion: "Detrás de esto hay decisiones que conviene justificar.",
      preguntas: [
        {
          pregunta: "Si las cifras cambian entre sistemas, ¿son fiables?",
          respuesta: "Las diferencias son de centésimas o décimas de MAE y no cambian ninguna conclusión. Lo que se fija con Docker es que cualquiera que use la imagen obtenga exactamente las cifras del informe.",
        },
      ],
    },
  },
  {
    id: "decisiones",
    seccion: "Decisiones",
    titulo: "Decisiones y justificaciones",
    expone: "Juan Diego",
    Contenido: Decisiones,
    notas: {
      guion: [
        "Siete decisiones condicionan los resultados, y todas se tomaron antes de ver la evaluación final.",
        "La fuente es la Policía, la única diaria y por víctima. La barra se elige en la evaluación porque el mejor comparador cambia con la ventana. Y el horizonte es de un día, el único con todas las predictoras disponibles.",
        { accion: "Señalar la última fila." },
        "Y en la interpretación permutamos grupos de variables, porque los rezagos de 7 y 14 días se suplen entre sí.",
      ],
      enfatizar: ["Ninguna decisión se tomó después de ver la evaluación final."],
      transicion: "Con todo esto fijado, vamos a los resultados.",
      preguntas: [
        {
          pregunta: "¿No habría sido mejor usar 2018–2025 para tener más datos?",
          respuesta: "2018 y 2019 no existen a nivel de registro: la Policía solo los publica agregados. Mezclar microdato y agregado en la misma serie cambiaría la unidad de observación. Se usan solo como contexto.",
        },
      ],
    },
  },
];
