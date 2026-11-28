import { CheckCircle2, CircleSlash } from "lucide-react";
import { DiagramaFuentes } from "../components/diagramas/Fuentes";
import { Estado, Panel, Rotulo } from "../components/piezas";
import { Revelar } from "../components/Revelar";
import { num } from "../data/formato";
import { serie } from "../data/datos";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

function Portada() {
  return (
    <div className="lienzo flex">
      <div className="flex w-[1180px] flex-col justify-between px-24 py-20">
        <div>
          <div className="text-[22px] font-semibold uppercase tracking-[0.2em] text-azul">
            Pontificia Universidad Javeriana
          </div>
          <div className="mt-2 text-[22px] text-gris">Ingeniería de Sistemas · Analítica de Datos</div>
        </div>
        <Revelar>
          <h1 className="font-serif text-[68px] leading-[1.06] font-semibold text-tinta">
            ¿Se puede anticipar el hurto a personas en Bogotá?
          </h1>
          <p className="mt-7 max-w-[960px] text-[28px] leading-[1.4] text-gris">
            Análisis multifuente y pronóstico diario de las víctimas registradas por la Policía Nacional, 2020–2025,
            con minería de datos y aprendizaje automático.
          </p>
        </Revelar>
        <div className="flex items-end gap-14 whitespace-nowrap text-[22px]">
          <div>
            <Rotulo>Presentan</Rotulo>
            <div className="mt-2 leading-snug">
              Juan Diego Rojas
              <br />
              Sara Albarracín
            </div>
          </div>
          <div>
            <Rotulo>Profesor</Rotulo>
            <div className="mt-2">Ferney Maldonado López</div>
          </div>
          <div>
            <Rotulo>Entrega</Rotulo>
            <div className="mt-2">Tercera entrega · noviembre de 2026</div>
          </div>
        </div>
      </div>
      <div className="relative flex flex-1 flex-col justify-center bg-azul px-16 text-white">
        <Revelar paso={2}>
          <div className="text-[20px] font-semibold uppercase tracking-[0.16em] text-white/70">La serie que se pronostica</div>
          <div className="mt-6 font-serif text-[104px] leading-none font-semibold tabular">{num(serie.victimas)}</div>
          <div className="mt-3 text-[26px] text-white/85">víctimas de hurto a personas registradas</div>
          <div className="mt-12 font-serif text-[104px] leading-none font-semibold tabular">{num(serie.dias)}</div>
          <div className="mt-3 text-[26px] text-white/85">días, del 1 de enero de 2020 al 31 de octubre de 2025</div>
        </Revelar>
      </div>
    </div>
  );
}

function Contexto() {
  return (
    <Marco
      seccion="Contexto"
      titulo="Tres fuentes oficiales miran el mismo fenómeno con unidades distintas"
      mensaje="Una víctima registrada, una llamada tramitada y un proceso judicial pueden referirse al mismo hecho. Por eso las fuentes se comparan, pero nunca se suman."
    >
      <DiagramaFuentes />
    </Marco>
  );
}

function Problema() {
  return (
    <Marco seccion="Planteamiento" titulo="La pregunta que guía el proyecto">
      <div className="grid h-full grid-cols-[1.35fr_1fr] gap-14">
        <Revelar>
          <div className="border-l-[6px] border-azul pl-10">
            <Rotulo>Pregunta principal</Rotulo>
            <p className="mt-4 font-serif text-[40px] leading-[1.3] text-tinta">
              ¿En qué medida las fuentes oficiales permiten identificar patrones temporales del hurto a personas en
              Bogotá entre 2020 y 2025 y <span className="text-azul">pronosticar el número diario de víctimas
              registradas con menor error que una línea base ingenua</span>?
            </p>
          </div>
          <div className="mt-12 pl-[46px]">
            <Rotulo>Pregunta complementaria</Rotulo>
            <p className="mt-3 text-[26px] leading-[1.4] text-gris">
              ¿Qué diferencias de cobertura, granularidad y registro condicionan la comparación entre la Línea 123, la
              Policía y la Fiscalía?
            </p>
          </div>
        </Revelar>
        <div className="flex flex-col gap-6">
          <Revelar paso={1}>
            <Panel tono="azul" className="p-8">
              <Rotulo className="text-azul">Qué se pronostica</Rotulo>
              <p className="mt-3 text-[25px] leading-[1.4]">
                Cuántas víctimas registrará la Policía <b>mañana</b> en toda Bogotá, usando solo lo conocido al cerrar
                hoy.
              </p>
            </Panel>
          </Revelar>
          <Revelar paso={2}>
            <Panel tono="oxido" className="p-8">
              <Rotulo className="text-oxido">Qué no se pronostica</Rotulo>
              <p className="mt-3 text-[25px] leading-[1.4]">
                El hurto <b>ocurrido</b>. El que no se denuncia ni llega a la autoridad no está en la serie: se modela
                el registro, no la victimización.
              </p>
            </Panel>
          </Revelar>
          <Revelar paso={3}>
            <Panel className="p-8">
              <Rotulo>La vara de medir</Rotulo>
              <p className="mt-3 text-[25px] leading-[1.4]">
                Un modelo solo aporta si se equivoca menos que repetir lo ocurrido el mismo día de la semana anterior.
              </p>
            </Panel>
          </Revelar>
        </div>
      </div>
    </Marco>
  );
}

function Justificacion() {
  const si = [
    "Cuantificar cuánto se puede anticipar un conteo agregado de toda la ciudad",
    "Comparar métodos con un protocolo reproducible y una barra explícita",
    "Describir el territorio con la única fuente que lo permite: la Línea 123",
  ];
  const no = [
    "Anticipar delitos individuales ni identificar a personas",
    "Pronosticar por localidad: el registro de la Policía no la trae",
    "Recomendar dónde patrullar ni leer importancias como causas",
  ];
  return (
    <Marco
      seccion="Justificación y alcance"
      titulo="El valor está en medir la capacidad predictiva, no en prometer anticipar delitos"
      mensaje="Un buen resultado estadístico no es evidencia causal ni una justificación automática para decidir sobre comunidades concretas."
    >
      <div className="grid grid-cols-3 gap-8">
        {[
          ["Social", "Evidencia sobre cómo varía el hurto registrado, para comprender la seguridad urbana."],
          ["Tecnológica", "Series de tiempo, preparación de datos, visualización y aprendizaje automático sobre datos públicos."],
          ["Académica", "Un problema reproducible donde comparar métodos y discutir abiertamente sus límites."],
        ].map(([t, d], i) => (
          <Revelar key={t} paso={i}>
            <div className="border-t-[3px] border-azul pt-5">
              <div className="font-serif text-[30px] font-semibold">{t}</div>
              <p className="mt-2 text-[24px] leading-[1.4] text-gris">{d}</p>
            </div>
          </Revelar>
        ))}
      </div>
      <div className="mt-14 grid grid-cols-2 gap-10">
        <Revelar paso={3}>
          <Panel tono="verde" className="p-8">
            <Rotulo className="text-verde">Dentro del alcance</Rotulo>
            <ul className="mt-5 space-y-4 text-[25px] leading-snug">
              {si.map((t) => (
                <li key={t} className="flex gap-3">
                  <CheckCircle2 className="mt-1 shrink-0 text-verde" size={24} />
                  {t}
                </li>
              ))}
            </ul>
          </Panel>
        </Revelar>
        <Revelar paso={4}>
          <Panel tono="oxido" className="p-8">
            <Rotulo className="text-oxido">Fuera del alcance</Rotulo>
            <ul className="mt-5 space-y-4 text-[25px] leading-snug">
              {no.map((t) => (
                <li key={t} className="flex gap-3">
                  <CircleSlash className="mt-1 shrink-0 text-oxido" size={24} />
                  {t}
                </li>
              ))}
            </ul>
          </Panel>
        </Revelar>
      </div>
    </Marco>
  );
}

function Objetivos() {
  const objetivos: [string, string, "hecho"][] = [
    ["Recolectar y auditar las tres fuentes: variables, cobertura, unidad de observación y limitaciones", "Embudo, nulos, duplicados y SHA-256 de cada archivo", "hecho"],
    ["Construir la serie diaria de víctimas y describir tendencia, estacionalidad y atípicos", "2.131 días que suman 730.870 víctimas", "hecho"],
    ["Comparar las tendencias mensuales sin sumar conteos y describir la Línea 123 por localidad", "70 meses comunes; conteos y tasas por localidad y UPZ", "hecho"],
    ["Implementar y comparar modelos con una línea base y validación temporal", "4 comparadores y 5 modelos en 6 pliegues de origen rodante", "hecho"],
    ["Evaluar con MAE y RMSE frente a la línea base y discutir utilidad, sesgos y límites", "MAE, RMSE, MAPE, MASE y Diebold-Mariano; sin intervalos de predicción", "hecho"],
  ];
  return (
    <Marco seccion="Objetivos" titulo="Objetivo general y objetivos específicos">
      <Revelar>
        <p className="max-w-[1560px] font-serif text-[29px] leading-[1.4] text-tinta">
          Analizar de manera multifuente el hurto a personas en Bogotá para identificar sus patrones temporales y
          territoriales y evaluar modelos que pronostiquen el número diario de víctimas registradas.
        </p>
      </Revelar>
      <div className="mt-8 divide-y divide-linea rounded-[14px] border border-linea bg-white px-8">
        {objetivos.map(([o, ev, est], i) => (
          <Revelar key={o} paso={i + 1} desde="izquierda">
            <div className="grid grid-cols-[60px_1fr_560px_150px] items-center gap-6 py-[19px]">
              <span className="font-serif text-[34px] font-semibold text-azul tabular">{i + 1}</span>
              <span className="text-[25px] leading-snug">{o}</span>
              <span className="text-[21px] leading-snug text-gris">{ev}</span>
              <span className="text-right">
                <Estado tipo={est}>Cumplido</Estado>
              </span>
            </div>
          </Revelar>
        ))}
      </div>
    </Marco>
  );
}

export const APERTURA: Diapositiva[] = [
  {
    id: "portada",
    seccion: "Apertura",
    titulo: "Portada",
    expone: "Juan Diego",
    Contenido: Portada,
    notas: {
      guion: [
        { accion: "Juan Diego: presentación en pantalla completa (tecla F) en la diapositiva 1." },
        "Buenos días, profesor. Somos Juan Diego Rojas y Sara Albarracín, y venimos a presentar la tercera entrega del proyecto de Analítica de Datos.",
        "Queremos saber si la historia del hurto a personas en Bogotá permite anticipar cuántas víctimas registrará la Policía al día siguiente, mejor que una regla sencilla.",
        "Trabajamos con 730.870 víctimas registradas en 2.131 días, de enero de 2020 a octubre de 2025.",
      ],
      enfatizar: [
        "Se pronostica el registro de la Policía, no el hurto ocurrido.",
        "La serie termina el 31 de octubre de 2025, y más adelante explicamos por qué.",
      ],
      transicion: "Antes de hablar de modelos, hay que entender de dónde salen esos datos.",
    },
  },
  {
    id: "contexto",
    seccion: "Contexto",
    titulo: "Tres fuentes, tres unidades",
    expone: "Juan Diego",
    Contenido: Contexto,
    notas: {
      guion: [
        "En Bogotá hay tres fuentes oficiales y públicas sobre hurto, y cada una cuenta una cosa distinta.",
        { accion: "Señalar la tarjeta de la Policía." },
        "La Policía publica una fila por víctima con la fecha del hecho, pero sin la localidad. Es la única fuente diaria, y sus 741.986 registros cumplen por sí solos el requisito de 500.000.",
        { accion: "Señalar las tarjetas de la Línea 123 y de la Fiscalía." },
        "La Línea 123 publica llamadas mensuales por localidad: permite mirar el territorio, pero mide demanda de atención, no hechos. Y la Fiscalía publica pares proceso–delito, donde un proceso puede repetirse.",
        "Por eso las tres fuentes se comparan, pero nunca se suman: sumarlas contaría varias veces el mismo hecho.",
      ],
      enfatizar: [
        "Sumar las tres fuentes contaría varias veces el mismo hecho: se comparan en la escala común, mes por Bogotá, pero no se suman.",
        "Ninguna combinación de fuentes permite construir una serie diaria por localidad.",
      ],
      transicion: "Con esa restricción, la pregunta del proyecto queda así.",
      preguntas: [
        {
          pregunta: "¿Por qué no cruzar la Línea 123 con la Policía para tener localidad?",
          respuesta: "Porque miden cosas distintas y con resoluciones distintas: llamadas mensuales por localidad frente a víctimas diarias de toda la ciudad. Asignar localidades a las víctimas con la Línea 123 sería inventar un dato que la Policía no publica.",
        },
        {
          pregunta: "¿Cómo se cumple el mínimo de 500.000 registros?",
          respuesta: "Con el registro de la Policía, que tiene 741.986 filas de hurto a personas en Bogotá para 2020–2025, en una sola unidad de observación: una víctima por fila (decisión D-01). Fiscalía también lo supera, pero es complementaria y no cuenta víctimas.",
        },
      ],
    },
  },
  {
    id: "problema",
    seccion: "Planteamiento",
    titulo: "Pregunta de investigación",
    expone: "Juan Diego",
    Contenido: Problema,
    notas: {
      guion: [
        "Nuestra pregunta principal tiene dos partes: identificar los patrones temporales del hurto y pronosticar el número diario de víctimas registradas con menos error que una línea base ingenua.",
        "La pregunta complementaria es sobre las fuentes: qué diferencias de cobertura y de registro impiden compararlas directamente.",
        { accion: "Señalar los tres recuadros de la derecha." },
        "Tres precisiones. Pronosticamos cuántas víctimas registrará la Policía mañana en toda la ciudad, con lo que se sabe hoy. No pronosticamos el hurto ocurrido: el que no se denuncia no está en la serie. Y un modelo solo aporta si se equivoca menos que repetir el mismo día de la semana anterior.",
      ],
      enfatizar: [
        "Un pronóstico de un día, de toda la ciudad, con la información disponible al cerrar el día anterior.",
        "La línea base no se elige a conveniencia: es el mejor de cuatro comparadores triviales.",
      ],
      transicion: "¿Por qué vale la pena responder esto, y hasta dónde llega?",
      preguntas: [
        {
          pregunta: "¿Por qué un horizonte de un solo día?",
          respuesta: "Es el único horizonte en el que todas las predictoras están disponibles sin suponer nada sobre los retrasos de publicación (decisión D-04). Horizontes de 7 o 14 días quedan como trabajo futuro.",
        },
      ],
    },
  },
  {
    id: "justificacion",
    seccion: "Justificación",
    titulo: "Justificación y alcance",
    expone: "Juan Diego",
    Contenido: Justificacion,
    notas: {
      guion: [
        "La justificación tiene tres frentes: social, tecnológico y académico. Pero lo más importante de esta diapositiva es el alcance.",
        { accion: "Señalar el recuadro rojo, «Fuera del alcance»." },
        "Medimos cuánto se puede anticipar un conteo agregado de toda la ciudad. No anticipamos delitos individuales, no pronosticamos por localidad, porque la Policía no publica la localidad, y no recomendamos dónde patrullar.",
        "Un buen resultado estadístico no es evidencia causal ni justifica decisiones sobre comunidades concretas.",
      ],
      enfatizar: ["Las importancias de los modelos describen de qué información depende el pronóstico, no qué causa el hurto."],
      transicion: "Con ese alcance planteamos cinco objetivos específicos.",
    },
  },
  {
    id: "objetivos",
    seccion: "Objetivos",
    titulo: "Objetivos",
    expone: "Juan Diego",
    Contenido: Objetivos,
    notas: {
      guion: [
        "El objetivo general es analizar el hurto con varias fuentes y evaluar modelos que pronostiquen el número diario de víctimas.",
        "Los cinco objetivos específicos van de los datos al modelo: auditar las fuentes, construir la serie, comparar las fuentes, implementar los modelos y evaluarlos contra la línea base.",
        "Los cinco están cumplidos, y a la derecha está la evidencia de cada uno. Hay dos matices que decimos de entrada: la serie se cortó en octubre de 2025 y la evaluación no incluye intervalos de predicción.",
      ],
      enfatizar: ["Cada cifra de esta presentación sale de un archivo de outputs/ producido por un script."],
      transicion: "Empiezo por el primero: la auditoría de los datos.",
      preguntas: [
        {
          pregunta: "¿Por qué no hay intervalos de predicción?",
          respuesta: "Porque los residuos de SARIMA y ETS conservan autocorrelación (Ljung-Box rechaza a 7, 14 y 28 rezagos). Un intervalo que suponga errores independientes sería demasiado estrecho. Proponemos remuestreo por bloques o predicción conforme como trabajo futuro.",
        },
      ],
    },
  },
];

// Las cifras de la portada vienen de la serie; esta comprobación evita un desfase silencioso.
if (serie.dias !== 2131) console.warn("La serie no tiene los 2.131 días del informe:", serie.dias);
