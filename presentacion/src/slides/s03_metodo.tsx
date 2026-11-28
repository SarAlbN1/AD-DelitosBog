import { DiagramaFuga } from "../components/diagramas/Fuga";
import { DiagramaPliegues } from "../components/diagramas/Pliegues";
import { Formula } from "../components/Formula";
import { Fuente, Panel, Rotulo } from "../components/piezas";
import { Revelar } from "../components/Revelar";
import { COLOR } from "../data/colores";
import { modelos } from "../data/datos";
import { num } from "../data/formato";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

const GRUPOS: [string, string, string][] = [
  ["Rezago de 1 día", "y(t−1)", "el nivel reciente"],
  ["Rezagos semanales", "y(t−7), y(t−14), y(t−28)", "el mismo día de semanas anteriores"],
  ["Medias y desviaciones previas", "7 y 28 días, y su tendencia", "5 variables"],
  ["Día de la semana", "y fin de semana", "2 variables"],
  ["Festivos", "festivo, víspera, día después, puente", "4 variables"],
  ["Calendario lento", "año, mes, día del mes, semana, quincena", "5 variables"],
  ["Indicador de 2020", "año atípico", "1 variable"],
];

function Fundamentos() {
  return (
    <Marco
      seccion="Fundamentos"
      titulo="Pronóstico de un paso: predecir mañana con lo que se sabe hoy"
      mensaje="Todas las predictoras están disponibles al cerrar el día t−1. Las de calendario se conocen con años de antelación; las demás solo usan el pasado."
    >
      <div className="grid grid-cols-[1fr_760px] gap-14">
        <div>
          <Revelar>
            <Panel tono="azul" className="px-6 py-6 text-[25px]">
              <Formula bloque tex={String.raw`\hat{y}_{t} \;=\; f\big(\,\underbrace{y_{t-1},\,y_{t-7},\,y_{t-14},\,y_{t-28},\,\bar{y}_{t-7:t-1},\dots}_{\text{historia}}\;,\;\underbrace{\text{día}_t,\ \text{festivo}_t,\ \text{mes}_t,\dots}_{\text{calendario}}\,\big)`} />
            </Panel>
          </Revelar>
          <Revelar paso={1}>
            <Rotulo className="mt-8">Las 21 predictoras, en siete grupos</Rotulo>
            <table className="mt-2 w-full text-[20px]">
              <tbody>
                {GRUPOS.map(([g, v, d]) => (
                  <tr key={g} className="border-b border-linea">
                    <td className="py-[8px] pr-4 font-semibold">{g}</td>
                    <td className="py-[8px] pr-4 font-mono text-[17px] text-azul">{v}</td>
                    <td className="py-[8px] text-gris">{d}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Revelar>
        </div>
        <Revelar paso={2}>
          <DiagramaFuga />
          <Panel className="mt-6 p-6">
            <Rotulo>Prueba automática contra la fuga</Rotulo>
            <p className="mt-2 text-[20px] leading-snug">
              Para cada día <i>t</i> se altera la serie desde <i>t</i> en adelante y se exige que la predicción de{" "}
              <i>t</i> no cambie. Los cinco modelos la pasan.
            </p>
          </Panel>
        </Revelar>
      </div>
    </Marco>
  );
}

function Validacion() {
  return (
    <Marco
      seccion="Metodología"
      titulo="Seis pliegues de origen rodante para elegir; 184 días intactos para evaluar"
      mensaje="Los hiperparámetros se eligen con el menor MAE en las 540 fechas de validación. La evaluación final no interviene en ninguna decisión."
    >
      <Revelar>
        <DiagramaPliegues />
      </Revelar>
      <div className="absolute right-0 bottom-0">
        <Fuente>outputs/baselines/validacion_rodante.csv · config/modelado.json</Fuente>
      </div>
    </Marco>
  );
}

function Metricas() {
  const comparadores = modelos.tabla.filter((m) => m.familia === "comparador");
  return (
    <Marco
      seccion="Metodología"
      titulo="Métricas en víctimas por día y una barra que no se elige a conveniencia"
      mensaje="La barra es el mejor de cuatro comparadores triviales en el mismo conjunto de evaluación (D-04). Un modelo que no baje de ella no aporta nada."
    >
      <div className="grid grid-cols-[1fr_820px] gap-14">
        <div className="space-y-5">
          {[
            ["MAE · métrica principal", String.raw`\mathrm{MAE}=\frac{1}{n}\sum_{i=1}^{n}\lvert y_i-\hat y_i\rvert`, "Se lee en víctimas al día."],
            ["RMSE · secundaria", String.raw`\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}`, "Penaliza más los errores grandes de los picos."],
            ["MASE · sin unidades", String.raw`\mathrm{MASE}=\frac{\mathrm{MAE}}{\frac{1}{T-7}\sum_{t=8}^{T}\lvert y_t-y_{t-7}\rvert}`, "Menor que 1: mejor que el ingenuo estacional en el entrenamiento (denominador 53,20)."],
          ].map(([t, f, d], i) => (
            <Revelar key={t} paso={i}>
              <div className="grid grid-cols-[250px_1fr] items-center gap-6 border-b border-linea pb-4">
                <div>
                  <div className="text-[20px] font-semibold">{t}</div>
                  <div className="mt-1 text-[17px] leading-snug text-gris">{d}</div>
                </div>
                <div className="text-[27px]">
                  <Formula bloque tex={f} />
                </div>
              </div>
            </Revelar>
          ))}
          <Revelar paso={3}>
            <p className="text-[18px] leading-snug text-gris">
              El MAPE se reporta, pero no decide: es asimétrico y castiga más la sobreestimación.
            </p>
          </Revelar>
        </div>
        <Revelar paso={2}>
          <Rotulo>Comparadores triviales en la evaluación final (184 días)</Rotulo>
          <table className="mt-3 w-full text-[21px] tabular">
            <thead>
              <tr className="border-b-2 border-tinta text-left text-[15px] uppercase tracking-[0.08em] text-gris">
                <th className="py-2 font-semibold">Comparador</th>
                <th className="py-2 text-right font-semibold">Fórmula</th>
                <th className="py-2 text-right font-semibold">MAE</th>
                <th className="py-2 text-right font-semibold">MASE</th>
              </tr>
            </thead>
            <tbody>
              {comparadores.map((c) => {
                const barra = c.id === "ingenuo_estacional";
                const formula: Record<string, string> = {
                  ingenuo: String.raw`y_{t-1}`,
                  ingenuo_estacional: String.raw`y_{t-7}`,
                  media_movil_7: String.raw`\bar y_{t-7:t-1}`,
                  media_movil_28: String.raw`\bar y_{t-28:t-1}`,
                };
                return (
                  <tr key={c.id} className={`border-b border-linea ${barra ? "bg-oxido-claro font-semibold" : ""}`}>
                    <td className="py-[10px] pl-2">{c.nombre}</td>
                    <td className="py-[10px] text-right text-[19px]">
                      <Formula tex={formula[c.id]} />
                    </td>
                    <td className="py-[10px] text-right">{num(c.MAE, 2)}</td>
                    <td className="py-[10px] pr-2 text-right">{num(c.MASE, 3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="mt-5 text-[19px] leading-snug text-gris">
            El orden de los comparadores cambia según la ventana: el ingenuo gana cuatro de los seis pliegues, pero en
            la evaluación final gana el ingenuo estacional. Por eso la barra no se fija de antemano.
          </p>
          <div className="mt-3">
            <Fuente>outputs/baselines/comparadores.csv</Fuente>
          </div>
        </Revelar>
      </div>
    </Marco>
  );
}

function Modelos() {
  const filas: { id: keyof typeof COLOR; nombre: string; familia: string; que: string; ve: string; eleccion: string }[] = [
    { id: "sarima", nombre: "SARIMA", familia: "Series de tiempo", que: "Autorregresión y media móvil con términos estacionales de periodo 7", ve: "Solo la serie", eleccion: "Órdenes por AIC en cada tramo; regla «desempate»: ante ΔAIC < 2, la más simple" },
    { id: "ets", nombre: "ETS", familia: "Series de tiempo", que: "Suavizado exponencial de nivel, tendencia y estacionalidad", ve: "Solo la serie", eleccion: "Cuatro configuraciones; regla «MAE interno» en los últimos 90 días del tramo" },
    { id: "regresion_lineal", nombre: "Regresión lineal", familia: "Regresión", que: "Combinación lineal de las predictoras, con penalización ridge", ve: "21 predictoras", eleccion: "α = 0,1 entre seis valores; a igualdad, la más regularizada" },
    { id: "bosque_aleatorio", nombre: "Bosque aleatorio", familia: "Árboles", que: "Promedio de 300 árboles entrenados con remuestreo", ve: "21 predictoras", eleccion: "7 candidatas; gana la configuración base (hoja mínima 3)" },
    { id: "gradiente_histogramas", nombre: "Gradiente por histogramas", familia: "Árboles", que: "Árboles en secuencia: cada uno corrige el error de los anteriores", ve: "21 predictoras", eleccion: "7 candidatas; profundidad 8, hoja mínima 7, 300 iteraciones" },
  ];
  return (
    <Marco
      seccion="Modelos"
      titulo="Cinco modelos, de menor a mayor capacidad, con el mismo protocolo"
      mensaje="No se busca el mejor modelo posible, sino medir cuánto mejora el pronóstico al añadir calendario y rezagos frente a los comparadores triviales."
    >
      <div className="rounded-[14px] border border-linea bg-white px-8 py-2">
      <table className="w-full text-[20px]">
        <thead>
          <tr className="border-b-2 border-tinta text-left text-[15px] uppercase tracking-[0.08em] text-gris">
            <th className="py-2 font-semibold">Modelo</th>
            <th className="py-2 font-semibold">Qué hace</th>
            <th className="py-2 font-semibold">Qué ve</th>
            <th className="py-2 font-semibold">Cómo se eligió (en los pliegues)</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((f, i) => (
            <tr key={f.id} className="border-b border-linea align-top">
              <td className="py-[12px] pr-6">
                <Revelar paso={i} desde="izquierda">
                  <div className="flex items-start gap-3">
                    <span className="mt-[7px] h-4 w-4 shrink-0 rounded-sm" style={{ background: COLOR[f.id] }} />
                    <div>
                      <div className="text-[23px] font-semibold">{f.nombre}</div>
                      <div className="text-[16px] uppercase tracking-[0.08em] text-gris">{f.familia}</div>
                    </div>
                  </div>
                </Revelar>
              </td>
              <td className="w-[520px] py-[14px] pr-6 leading-snug">{f.que}</td>
              <td className="w-[200px] py-[14px] pr-6">
                <span className={`rounded-full px-3 py-1 text-[17px] font-semibold ${f.ve === "Solo la serie" ? "bg-verde-claro text-verde" : "bg-azul-claro text-azul"}`}>
                  {f.ve}
                </span>
              </td>
              <td className="w-[560px] py-[14px] leading-snug text-gris">{f.eleccion}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      <div className="mt-5 grid grid-cols-3 gap-8 text-[19px] leading-snug">
        <p><b className="text-verde">SARIMA y ETS</b> representan el ciclo semanal de forma explícita, pero no ven el calendario.</p>
        <p><b className="text-azul">Los árboles</b> captan interacciones no lineales entre calendario y rezagos sin especificarlas.</p>
        <p><b style={{ color: COLOR.regresion_lineal }}>La regresión</b> es el modelo transparente: sus coeficientes se leen directamente.</p>
      </div>
    </Marco>
  );
}

export const METODO: Diapositiva[] = [
  {
    id: "fundamentos",
    seccion: "Fundamentos",
    titulo: "Pronóstico de un paso y fuga",
    expone: "Sara",
    Contenido: Fundamentos,
    notas: {
      guion: [
        "Formalmente es un pronóstico de un paso: el valor de hoy se predice con la historia hasta ayer y con el calendario de hoy.",
        { accion: "Señalar la fórmula y luego la tabla de predictoras." },
        "Usamos 21 predictoras en siete grupos: rezagos, medias recientes, día de la semana, festivos y calendario. El calendario se conoce de antemano; lo demás es pasado.",
        { accion: "Señalar el diagrama de la derecha." },
        "Aquí no sirve barajar los datos: cada día de prueba quedaría rodeado de días de entrenamiento y, con rezagos, el modelo vería la respuesta. Por eso usamos origen rodante: se entrena con el pasado y se predice lo que sigue. Una prueba automática altera el futuro y exige que el pronóstico no cambie.",
      ],
      enfatizar: ["La fuga de información es el error más común en series de tiempo; aquí está bloqueada por diseño y por prueba."],
      transicion: "Así se organiza esa validación en el tiempo.",
      preguntas: [
        {
          pregunta: "Si el modelo ve la serie completa, ¿cómo saben que no hace trampa?",
          respuesta: "Con la prueba sin_fuga: para cada día t se altera la serie desde t en adelante y se reconstruyen las predictoras. Si la predicción de t cambia, la prueba falla. Detecta incluso un modelo que mire el valor del mismo día que predice.",
        },
      ],
    },
  },
  {
    id: "validacion",
    seccion: "Metodología",
    titulo: "Origen rodante y evaluación final",
    expone: "Sara",
    Contenido: Validacion,
    notas: {
      guion: [
        "Los datos hasta el 30 de abril de 2025 son el entrenamiento. Los 184 días siguientes, de mayo a octubre, son la evaluación final: la barra roja.",
        { accion: "Recorrer los pliegues de arriba abajo." },
        "Dentro del entrenamiento hay seis pliegues de 90 días. Cada uno entrena con todo lo anterior y evalúa los 90 días siguientes, y el entrenamiento crece de pliegue en pliegue.",
        "Todos los hiperparámetros se eligen con el error en esas 540 fechas. La evaluación final se calcula una sola vez, al final, y no interviene en ninguna decisión. Así evitamos ajustar los modelos a la ventana con la que los juzgamos.",
      ],
      enfatizar: [
        "Separar elección y evaluación evita sobreajustar a la ventana de evaluación.",
        "Los pliegues además muestran la variabilidad: un buen resultado en una sola ventana no basta.",
      ],
      transicion: "¿Con qué medimos el error, y contra qué?",
      preguntas: [
        {
          pregunta: "¿Por qué 90 días por pliegue y seis pliegues?",
          respuesta: "El protocolo está fijado en D-04. Los seis pliegues cubren 540 días, de noviembre de 2023 a abril de 2025: todas las épocas del año, y dos veces la temporada de fin de año (pliegues 1 y 5). Cada pliegue tiene suficientes días para que su MAE sea estable. Es la evaluación con origen rodante de Hyndman y Athanasopoulos (2021).",
        },
      ],
    },
  },
  {
    id: "metricas",
    seccion: "Metodología",
    titulo: "Métricas y barra",
    expone: "Sara",
    Contenido: Metricas,
    notas: {
      guion: [
        "La métrica principal es el MAE: cuántas víctimas por día se equivoca el modelo. El RMSE castiga más los errores grandes, y un MASE menor que 1 significa que el modelo mejora al ingenuo estacional.",
        { accion: "Señalar la tabla de comparadores y su fila resaltada." },
        "La barra no la elegimos a conveniencia: es el mejor de cuatro comparadores triviales en la misma evaluación. Ganó el ingenuo estacional, que repite el valor de hace una semana, con un MAE de 49,04 víctimas por día. Esa es la cifra que hay que batir.",
      ],
      enfatizar: [
        "La barra es el mejor comparador en el mismo conjunto de evaluación, no uno elegido de antemano.",
        "El MAPE no decide: no está acotado por arriba y castiga más la sobreestimación.",
      ],
      transicion: "Y estos son los cinco modelos que compiten contra ella.",
      preguntas: [
        {
          pregunta: "¿No es injusto elegir la barra mirando la evaluación?",
          respuesta: "Es lo contrario: elegir el mejor comparador en la propia evaluación hace la barra más exigente. Es la regla D-04. Si se hubiera fijado de antemano, en la mayoría de pliegues habría quedado en el lugar equivocado.",
        },
      ],
    },
  },
  {
    id: "modelos",
    seccion: "Modelos",
    titulo: "Cinco familias de modelos",
    expone: "Sara",
    Contenido: Modelos,
    notas: {
      guion: [
        "Los ordenamos de menor a mayor capacidad, para ver qué aporta cada salto.",
        "SARIMA y ETS modelan la propia serie: representan el ciclo semanal, pero no ven el calendario, así que para ellos un festivo es un día normal.",
        "La regresión lineal usa las 21 predictoras con una penalización ridge. Es el modelo transparente: cada coeficiente se lee en víctimas.",
        "El bosque aleatorio promedia 300 árboles, y el gradiente por histogramas encadena árboles que corrigen el error de los anteriores. Los dos captan interacciones sin que tengamos que escribirlas.",
        { accion: "Señalar la última columna." },
        "Todos se eligieron en los pliegues y se evalúan con la misma función: mismos días, mismas métricas y misma barra.",
      ],
      enfatizar: ["Todos pasan por la misma función de evaluación: mismos días, mismas métricas, misma barra."],
      transicion: "Juan Diego nos muestra ahora cómo está construido todo esto.",
      preguntas: [
        {
          pregunta: "¿Por qué no usaron redes neuronales o Prophet?",
          respuesta: "No se evaluaron. La pregunta del proyecto era cuánto aportan calendario y rezagos frente a una regla ingenua, y los cuatro primeros modelos ya quedan estadísticamente empatados. Con unos 1.900 días de entrenamiento, un modelo con más capacidad tendría más riesgo de sobreajustar; sería una extensión posible, con el mismo protocolo.",
        },
        {
          pregunta: "¿Qué es la regla de «desempate» de SARIMA?",
          respuesta: "Entre las candidatas a menos de 2 puntos de AIC de la mejor, se elige la de menos parámetros. Así la selección no depende de diferencias mínimas entre plataformas. Se eligió por MAE en los pliegues frente a otras dos reglas.",
        },
      ],
    },
  },
];
