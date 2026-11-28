import { CalendarRange, Eye, MapPinOff, Repeat2, Scale, Shuffle } from "lucide-react";
import { Estado, Panel, Rotulo } from "../components/piezas";
import { Revelar } from "../components/Revelar";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

function Limitaciones() {
  const items = [
    { icono: Eye, t: "Se modela el registro, no la victimización", d: "El hurto que no se denuncia no está en la serie. Con estas fuentes el subregistro no se puede observar." },
    { icono: CalendarRange, t: "La evaluación no cubre noviembre a enero", d: "En los pliegues de esa temporada el MAE de los modelos sube hasta 44,61: cabe esperar errores mayores." },
    { icono: Repeat2, t: "El registro puede cambiar sin aviso", d: "Como en noviembre y diciembre de 2025. El modelo lo trasladaría al pronóstico como si fuera un cambio real." },
    { icono: Scale, t: "Sin intervalos de predicción", d: "Los residuos conservan autocorrelación (Ljung-Box, p < 0,001): un intervalo ingenuo sería demasiado estrecho." },
    { icono: MapPinOff, t: "Solo toda la ciudad, a un día", d: "No se traslada a localidades, a otros horizontes, a otros delitos ni a otras ciudades." },
    { icono: Shuffle, t: "Riesgo de retroalimentación", d: "Si se usara para patrullar, podría aumentar los hechos conocidos y reforzar lo aprendido (Ensign et al., 2018)." },
  ];
  return (
    <Marco
      seccion="Limitaciones"
      titulo="Lo que el resultado no permite afirmar"
      mensaje="Un buen pronóstico del conteo oficial no es un buen pronóstico del hurto ocurrido, ni una guía para asignar vigilancia."
    >
      <div className="grid grid-cols-3 gap-8">
        {items.map((it, i) => {
          const Icono = it.icono;
          return (
            <Revelar key={it.t} paso={i}>
              <div className="h-full rounded-[14px] border border-linea bg-white border-t-[5px] border-t-oxido p-8">
                <Icono size={44} strokeWidth={1.6} className="text-oxido" />
                <div className="mt-4 text-[29px] font-semibold leading-snug">{it.t}</div>
                <p className="mt-3 text-[23px] leading-[1.4] text-gris">{it.d}</p>
              </div>
            </Revelar>
          );
        })}
      </div>
    </Marco>
  );
}

function Conclusiones() {
  return (
    <Marco seccion="Conclusiones" titulo="Respuesta a la pregunta de investigación">
      <div className="grid grid-cols-2 gap-12">
        <Revelar>
          <Panel tono="azul" className="h-full p-9">
            <Rotulo className="text-azul">1 · Los patrones temporales se identifican con claridad</Rotulo>
            <ul className="mt-6 space-y-5 text-[26px] leading-snug">
              <li>Ciclo semanal marcado: el viernes, un 65 % más que el domingo.</li>
              <li>Un lunes festivo registra un 37,8 % menos que uno laborable.</li>
              <li>El nivel cambia de un año a otro: de 227,1 víctimas diarias en 2020 a 434,9 en 2023.</li>
              <li>La estacionalidad mensual es débil frente a la semanal.</li>
            </ul>
          </Panel>
        </Revelar>
        <Revelar paso={1}>
          <Panel tono="verde" className="h-full p-9">
            <Rotulo className="text-verde">2 · El pronóstico a un día supera la línea base</Rotulo>
            <ul className="mt-6 space-y-5 text-[26px] leading-snug">
              <li>Los cinco modelos bajan el MAE de 49,04 a entre 32,72 y 36,31: entre un 26 y un 33 % menos.</li>
              <li>La mejora se repite en los seis pliegues y no depende de cómo se trate 2020.</li>
              <li>Entre los cuatro mejores no hay un ganador.</li>
              <li>Los modelos usan las señales del análisis exploratorio y el nivel del día anterior.</li>
            </ul>
          </Panel>
        </Revelar>
      </div>
      <Revelar paso={2}>
        <div className="mt-10 grid grid-cols-[1fr_1fr] gap-12 text-[23px] leading-snug">
          <p>
            <b>Pregunta complementaria.</b> Las tres fuentes no son intercambiables: la Policía cuenta víctimas sin
            localidad, la Línea 123 da el territorio pero cuenta llamadas, y la Fiscalía cuenta pares proceso–delito.
          </p>
          <p>
            <b>Dos precisiones.</b> Lo que se pronostica es el <i>registro</i> de la Policía. Y el periodo es 2020–2025,
            porque la Policía solo publica a nivel de registro esos años.
          </p>
        </div>
      </Revelar>
    </Marco>
  );
}

function TrabajoFuturo() {
  const items: [string, string, string][] = [
    ["Calendario en los modelos de series", "SARIMA con festivos y puentes como regresores externos, con la misma barra y los mismos pliegues", "Sesgo de SARIMA y ETS en festivos"],
    ["Intervalos de predicción válidos", "Remuestreo por bloques semanales o predicción conforme calibrada en los pliegues", "Autocorrelación en los residuos"],
    ["Evaluar la temporada de fin de año", "Nueva descarga cuando la Policía consolide noviembre y diciembre de 2025", "La evaluación no cubre nov.–ene."],
    ["Retraso de publicación y horizontes mayores", "Medir el retraso real y pronosticar a 7 y 14 días", "Uso operativo"],
    ["El día del mes", "Análisis descriptivo para saber si es un patrón o un artefacto del ajuste", "Dependencia sin explicar en el gradiente"],
    ["Interacciones en la regresión", "Festivo × día de la semana, elegida en los mismos pliegues", "Sesgo de la regresión en festivos"],
    ["Escala de localidad", "Solo si la Policía publica la localidad, y con salvaguardas contra la retroalimentación", "Modelo de toda la ciudad"],
  ];
  return (
    <Marco
      seccion="Trabajo futuro"
      titulo="Cada propuesta responde a un límite concreto"
      mensaje="Ninguna de estas extensiones está implementada."
    >
      <div className="rounded-[14px] border border-linea bg-white px-8 py-2">
      <table className="w-full text-[23px]">
        <thead>
          <tr className="border-b-2 border-tinta text-left text-[15px] uppercase tracking-[0.08em] text-gris">
            <th className="w-[500px] py-2 font-semibold">Propuesta</th>
            <th className="py-2 font-semibold">Cómo</th>
            <th className="w-[420px] py-2 font-semibold">Límite que ataca</th>
          </tr>
        </thead>
        <tbody>
          {items.map(([t, c, l], i) => (
            <tr key={t} className="border-b border-linea align-top">
              <td className="py-[15px] pr-6">
                <Revelar paso={i} desde="izquierda">
                  <span className="font-semibold">{t}</span>
                </Revelar>
              </td>
              <td className="py-[15px] pr-6 leading-snug text-gris">{c}</td>
              <td className="py-[15px]">
                <Estado tipo="futuro">{l}</Estado>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </Marco>
  );
}

const REFERENCIAS = [
  "Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.",
  "Diebold, F. X., y Mariano, R. S. (1995). Comparing predictive accuracy. Journal of Business & Economic Statistics, 13(3), 253–263.",
  "Ensign, D., Friedler, S. A., Neville, S., Scheidegger, C., y Venkatasubramanian, S. (2018). Runaway feedback loops in predictive policing. Proceedings of the 1st Conference on Fairness, Accountability and Transparency (PMLR 81, pp. 160–171).",
  "Harvey, D., Leybourne, S., y Newbold, P. (1997). Testing the equality of prediction mean squared errors. International Journal of Forecasting, 13(2), 281–291.",
  "Hyndman, R. J., y Athanasopoulos, G. (2021). Forecasting: Principles and practice (3.ª ed.). OTexts.",
  "Hyndman, R. J., y Koehler, A. B. (2006). Another look at measures of forecast accuracy. International Journal of Forecasting, 22(4), 679–688.",
  "Martínez Chitiva, A. V. (2025). Análisis espacio-temporal para caracterización, predicción y mitigación del hurto a personas en Bogotá [Tesis de maestría]. Universidad de Manizales.",
  "Newey, W. K., y West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica, 55(3), 703–708.",
  "Provost, F., y Fawcett, T. (2013). Data science for business. O'Reilly Media.",
  "Riascos Villegas, Á. J., Ñungo, J. S., Gómez Tobón, L., Dulce Rubio, M., y Gómez, F. (2023). Modelling underreported spatio-temporal crime events. PLOS ONE, 18(7), e0287776.",
  "Policía Nacional de Colombia. (2026). Información de delitos a nivel de registro, 2020–2025 [Conjunto de datos].",
  "Secretaría Distrital de Seguridad, Convivencia y Justicia. (2026). Llamadas tramitadas C4 Bogotá NUSE Línea 123 [Conjunto de datos]. Datos Abiertos Bogotá.",
  "Fiscalía General de la Nación. (2026). Procesos Fiscalía V3 [Conjunto de datos]. Datos Abiertos de Colombia.",
  "Secretaría Distrital de Planeación. (2025). Proyecciones y retroproyecciones de población 2005–2035 [Conjunto de datos].",
];

function Referencias() {
  return (
    <Marco seccion="Referencias" titulo="Referencias citadas en la presentación">
      <div className="columns-2 gap-14 text-[20px] leading-[1.42]">
        {REFERENCIAS.map((r) => (
          <p key={r} className="mb-[14px] break-inside-avoid pl-6 -indent-6">
            {r}
          </p>
        ))}
      </div>
      <p className="mt-2 text-[16px] text-suave">La lista completa, en APA 7 y con DOI, está en la sección de referencias del informe.</p>
    </Marco>
  );
}

function Preguntas() {
  return (
    <div className="lienzo flex flex-col justify-between bg-azul px-24 py-20 text-white">
      <div className="text-[22px] font-semibold uppercase tracking-[0.2em] text-white/70">Analítica de Datos · Tercera entrega</div>
      <Revelar>
        <h1 className="font-serif text-[120px] leading-none font-semibold">Preguntas</h1>
        <p className="mt-8 max-w-[1300px] text-[32px] leading-[1.4] text-white/85">
          Cinco modelos superan a la regla ingenua entre un 26 y un 33 %, en todos los pliegues. Ninguno se distingue de los
          demás. Lo que se pronostica es el registro, no el hurto ocurrido.
        </p>
      </Revelar>
      <div className="flex justify-between text-[22px] text-white/80">
        <span>Juan Diego Rojas · Sara Albarracín</span>
        <span className="font-mono text-[20px]">github.com/SarAlbN1/AD-DelitosBog</span>
      </div>
    </div>
  );
}

export const CIERRE: Diapositiva[] = [
  {
    id: "limitaciones",
    seccion: "Limitaciones",
    titulo: "Limitaciones",
    expone: "Juan Diego",
    Contenido: Limitaciones,
    notas: {
      guion: [
        "Pronosticamos el registro, no la victimización: el hurto que no se denuncia no está. La evaluación no cubre la temporada de fin de año, no hay intervalos de predicción, y el pronóstico es de toda la ciudad y a un día. No sirve para decidir dónde patrullar.",
      ],
      enfatizar: ["Los resultados valen para Bogotá, 2020–2025, el registro de la Policía tal como se descargó y un horizonte de un día."],
      transicion: "Sara, ¿cuál es la respuesta a la pregunta?",
      preguntas: [
        {
          pregunta: "¿Qué es un bucle de retroalimentación en este contexto?",
          respuesta: "Ensign y colegas muestran que si un sistema asigna policía por zonas y se actualiza con los incidentes que esa misma policía descubre, puede enviarla una y otra vez a los mismos barrios con independencia de la tasa real. Nuestro modelo no asigna recursos entre zonas, pero un aumento de presencia en días previstos como altos podría elevar los hechos conocidos esos días.",
        },
      ],
    },
  },
  {
    id: "conclusiones",
    seccion: "Conclusiones",
    titulo: "Conclusiones",
    expone: "Sara",
    Contenido: Conclusiones,
    notas: {
      guion: [
        "La respuesta tiene dos partes. Los patrones se identifican con claridad: un ciclo semanal fuerte, un efecto festivo de casi el 38 % y un nivel que cambia de un año a otro.",
        "Y el pronóstico a un día supera la línea base entre un 26 y un 33 %, en todos los pliegues, aunque sin un modelo ganador. Como trabajo futuro: dar el calendario a SARIMA y calcular intervalos de predicción.",
      ],
      enfatizar: ["Que los modelos se apoyen en las mismas señales del análisis exploratorio da coherencia al resultado: no es una caja negra que acierta por casualidad."],
      transicion: "Ahora les muestro todo esto en el tablero de Power BI.",
    },
  },
  {
    id: "trabajo-futuro",
    anexo: true,
    seccion: "Trabajo futuro",
    titulo: "Trabajo futuro",
    expone: "Sara",
    Contenido: TrabajoFuturo,
    notas: {
      guion: [
        "Cada propuesta ataca un límite concreto de los que vimos.",
        "La más directa es darle a SARIMA los festivos como variables externas, porque es exactamente su debilidad. La más útil para un uso real son los intervalos de predicción y los horizontes de 7 y 14 días. Y la escala de localidad solo tendría sentido si la Policía publicara la localidad, y con salvaguardas.",
        "Ninguna de estas extensiones está implementada.",
      ],
      enfatizar: ["Nada de esto está implementado: son extensiones, no resultados."],
      transicion: "",
    },
  },
  {
    id: "referencias",
    anexo: true,
    seccion: "Referencias",
    titulo: "Referencias",
    expone: "Sara",
    Contenido: Referencias,
    notas: {
      guion: [
        { accion: "No se lee. Dejarla en pantalla unos segundos y pasar a la siguiente." },
      ],
      enfatizar: ["Las referencias metodológicas clave son Hyndman y Athanasopoulos (validación y MASE), Diebold y Mariano con Harvey et al. (comparación de pronósticos) y Breiman (bosques y permutación)."],
      transicion: "",
    },
  },
  {
    id: "preguntas",
    seccion: "Cierre",
    titulo: "Preguntas",
    expone: "Ambos",
    Contenido: Preguntas,
    notas: {
      guion: [
        { accion: "Alt + Tab de vuelta a la presentación, en la diapositiva de preguntas." },
        { accion: "Para responder: tecla O e ir a la diapositiva que corresponda, incluido el anexo." },
      ],
      enfatizar: ["Si una pregunta pide una cifra que no está en el informe, decirlo: no improvisar resultados."],
      transicion: "",
    },
  },
];
