import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";
import { Cifra, Fuente, Leyenda, Panel, Rotulo } from "../components/piezas";
import { Revelar } from "../components/Revelar";
import { COLOR } from "../data/colores";
import { embudo, fuentes, serie, territorio } from "../data/datos";
import { num } from "../data/formato";
import { useAnimar } from "../hooks/modo";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

const EJE = { fontSize: 18, fill: "#5b6472" };

function Auditoria() {
  const max = embudo[0].filas;
  const etiquetas = [
    "Todos los delitos del país, archivos anuales 2020–2025",
    "Solo Bogotá (código DANE 11001)",
    "Solo hurto a personas (05022)",
    "Dentro del periodo de la serie",
  ];
  return (
    <Marco
      seccion="Datos · auditoría"
      titulo="De 4,8 millones de filas a la serie objetivo, con cada filtro documentado"
      mensaje="La auditoría registra, para cada fuente, el embudo de filtros, los nulos, los duplicados, la cobertura y la huella SHA-256 de cada archivo."
    >
      <div className="grid grid-cols-[1fr_520px] gap-14">
        <div className="space-y-6">
          {embudo.map((p, i) => (
            <Revelar key={p.paso} paso={i} desde="izquierda">
              <div className="grid grid-cols-[360px_1fr] items-center gap-6">
                <div className="text-[21px] leading-snug">{etiquetas[i]}</div>
                <div className="flex items-center gap-4">
                  <div
                    className="h-[58px] rounded-[6px]"
                    style={{
                      width: `${Math.max(4, (p.filas / max) * 100) * 5.4}px`,
                      background: i === embudo.length - 1 ? COLOR.azul : i === 2 ? "#3f6c9e" : "#c9d5e4",
                    }}
                  />
                  <span className="font-serif text-[34px] font-semibold tabular">{num(p.filas)}</span>
                </div>
              </div>
            </Revelar>
          ))}
          <div className="pt-4">
            <Fuente>outputs/powerbi/qa_embudo.csv · scripts/auditoria_datasets.py</Fuente>
          </div>
        </div>
        <div className="flex flex-col gap-6">
          <Revelar paso={4}>
            <Panel tono="azul" className="p-8">
              <Cifra valor="741.986" etiqueta="registros de hurto a personas en Bogotá, 2020–2025" detalle="Supera por sí solo el mínimo de 500.000 registros, en una sola unidad: una víctima por fila (D-01)." />
            </Panel>
          </Revelar>
          <Revelar paso={5}>
            <Panel className="p-7">
              <Rotulo>Tres advertencias de la auditoría</Rotulo>
              <ul className="mt-3 list-disc space-y-2 pl-6 text-[20px] leading-snug">
                <li>713.344 filas son duplicados exactos legítimos: dos víctimas del mismo perfil el mismo día. No se deduplica.</li>
                <li>La Policía solo publica a nivel de registro desde 2020.</li>
                <li>Noviembre y diciembre de 2025 caen a la mitad: se excluyen.</li>
              </ul>
            </Panel>
          </Revelar>
        </div>
      </div>
    </Marco>
  );
}

function SerieObjetivo() {
  const animar = useAnimar();
  const datos = serie.mensual;
  return (
    <Marco
      seccion="Datos · serie objetivo"
      titulo="La serie diaria cambia de nivel de un año a otro"
      mensaje={`${num(serie.dias)} días, del 2020-01-01 al 2025-10-31, con una media de ${num(serie.media, 1)} víctimas por día. 2020 entra marcado como atípico.`}
    >
      <div className="grid grid-cols-[1fr_430px] gap-12">
        <div>
          <Rotulo>Media diaria de víctimas, por mes</Rotulo>
          <LineChart width={1220} height={520} data={datos} margin={{ top: 22, right: 20, bottom: 8, left: 0 }}>
            <CartesianGrid stroke="#d9d1c1" vertical={false} />
            <ReferenceArea x1="2020-03" x2="2020-12" fill="#b4441a" fillOpacity={0.07} />
            <XAxis
              dataKey="mes"
              tick={EJE}
              tickFormatter={(m: string) => (m.endsWith("-01") ? m.slice(0, 4) : "")}
              interval={0}
              tickLine={false}
              axisLine={{ stroke: "#cfcac0" }}
            />
            <YAxis tick={EJE} domain={[0, 550]} ticks={[0, 100, 200, 300, 400, 500]} width={64} tickLine={false} axisLine={false} />
            <ReferenceLine y={serie.media} stroke="#8a919c" strokeDasharray="5 5" label={{ value: `media ${num(serie.media, 1)}`, position: "insideBottomRight", fontSize: 17, fill: "#5b6472" }} />
            <Line dataKey="media" stroke={COLOR.azul} strokeWidth={3.5} dot={false} isAnimationActive={animar} animationDuration={1200} />
          </LineChart>
          <div className="mt-1 flex items-center justify-between">
            <span className="text-[18px] text-oxido">Sombreado: marzo–diciembre de 2020, restricciones de movilidad</span>
            <Fuente>outputs/powerbi/fact_serie_diaria.csv</Fuente>
          </div>
        </div>
        <Revelar paso={1}>
          <Rotulo>Media diaria por año</Rotulo>
          <table className="mt-3 w-full text-[22px] tabular">
            <tbody>
              {serie.anual.map((a) => (
                <tr key={a.anio} className="border-b border-linea">
                  <td className="py-[11px] font-semibold">{a.anio}</td>
                  <td className="py-[11px] text-right font-serif text-[26px]">{num(a.media, 1)}</td>
                  <td className="py-[11px] pl-4 text-[17px] text-gris">
                    {a.anio === 2020 ? "atípico" : a.anio === 2023 ? "pico" : !a.completo ? `hasta oct. (${a.dias} d)` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-5 text-[19px] leading-snug text-gris">
            2025 está truncado: su total sugiere una caída, pero su media diaria supera la de 2024. Se comparan medias,
            no totales.
          </p>
        </Revelar>
      </div>
    </Marco>
  );
}

function Patrones() {
  const animar = useAnimar();
  const dias = serie.dia_semana.map((d) => ({ ...d, etiqueta: d.dia.slice(0, 3) }));
  const f = serie.festivos;
  const vie = serie.dia_semana.find((d) => d.dia === "viernes")!.media;
  const dom = serie.dia_semana.find((d) => d.dia === "domingo")!.media;
  const meses = serie.por_mes.map((m) => m.media);
  return (
    <Marco
      seccion="Análisis exploratorio"
      titulo="El día de la semana es la señal dominante, y el festivo se conoce de antemano"
      mensaje="Estas dos señales del análisis exploratorio son las que después se espera ver dentro de los modelos."
    >
      <div className="grid grid-cols-[1fr_600px] gap-14">
        <div>
          <Rotulo>Media de víctimas por día de la semana, 2020–2025</Rotulo>
          <BarChart width={1040} height={470} data={dias} margin={{ top: 40, right: 10, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="#d9d1c1" vertical={false} />
            <XAxis dataKey="etiqueta" tick={{ ...EJE, fontSize: 21 }} tickLine={false} axisLine={{ stroke: "#cfcac0" }} />
            <YAxis tick={EJE} domain={[0, 450]} ticks={[0, 100, 200, 300, 400]} width={56} tickLine={false} axisLine={false} />
            <Bar dataKey="media" radius={[6, 6, 0, 0]} isAnimationActive={animar}>
              {dias.map((d) => (
                <Cell key={d.dia} fill={d.dia === "viernes" ? COLOR.azul : d.dia === "domingo" ? COLOR.oxido : "#c3d0e0"} />
              ))}
              <LabelList dataKey="media" position="top" formatter={(v: unknown) => num(Number(v), 1)} style={{ fontSize: 20, fill: "#14213d" }} />
            </Bar>
          </BarChart>
          <Fuente>outputs/eda/resumen_eda.json · scripts/eda.py</Fuente>
        </div>
        <div className="flex flex-col gap-6">
          <Revelar paso={1}>
            <Panel tono="azul" className="p-7">
              <Cifra valor={`+${num((vie / dom - 1) * 100, 0)} %`} etiqueta="víctimas del viernes frente al domingo" />
            </Panel>
          </Revelar>
          <Revelar paso={2}>
            <Panel tono="oxido" className="p-7">
              <Cifra
                tono="oxido"
                valor={`${num(f.diferencia_lunes_pct, 1)} %`}
                etiqueta="en un lunes festivo frente a un lunes laborable"
                detalle={`${num(f.media_lunes_festivo, 1)} frente a ${num(f.media_lunes_laborable, 1)}. Se compara lunes con lunes porque la Ley 51 de 1983 traslada muchos festivos al lunes.`}
              />
            </Panel>
          </Revelar>
          <Revelar paso={3}>
            <p className="text-[20px] leading-snug text-gris">
              La estacionalidad mensual es débil: la media va de {num(Math.min(...meses), 1)} a {num(Math.max(...meses), 1)} según el mes.
            </p>
          </Revelar>
        </div>
      </div>
    </Marco>
  );
}

function FuentesNoSeSuman() {
  const animar = useAnimar();
  const c = fuentes.correlaciones;
  const claves = [
    { k: "Policía (registro)", color: COLOR.azul, nombre: "Policía · víctimas" },
    { k: "Fiscalía (Procesos V3)", color: COLOR.regresion_lineal, nombre: "Fiscalía · proceso–delito" },
    { k: "Línea 123", color: COLOR.ets, nombre: "Línea 123 · llamadas" },
  ];
  return (
    <Marco
      seccion="Análisis exploratorio · fuentes"
      titulo="Los dos registros institucionales se mueven juntos; la Línea 123, no"
      mensaje={`En la única escala común, mes × Bogotá (${fuentes.meses} meses), cada fuente se expresa como índice de su propia media. Ninguna se suma a otra.`}
    >
      <div className="grid grid-cols-[1fr_470px] gap-12">
        <div>
          <Rotulo>Índice mensual (100 = media de la fuente en el periodo común)</Rotulo>
          <div className="mt-3">
            <Leyenda items={claves.map((x) => ({ color: x.color, nombre: x.nombre }))} />
          </div>
          <LineChart width={1210} height={470} data={fuentes.serie} margin={{ top: 18, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="#d9d1c1" vertical={false} />
            <XAxis dataKey="mes" tick={EJE} tickFormatter={(m: string) => (m.endsWith("-01") ? m.slice(0, 4) : "")} interval={0} tickLine={false} axisLine={{ stroke: "#cfcac0" }} />
            <YAxis tick={EJE} domain={[0, 160]} ticks={[0, 40, 80, 120, 160]} width={56} tickLine={false} axisLine={false} />
            <ReferenceLine y={100} stroke="#8a919c" strokeDasharray="5 5" />
            {claves.map((x) => (
              <Line key={x.k} dataKey={x.k} stroke={x.color} strokeWidth={x.k.startsWith("Policía") ? 3.5 : 2.6} dot={false} isAnimationActive={animar} connectNulls={false} />
            ))}
          </LineChart>
          <Fuente>outputs/powerbi/fact_fuentes_mensual.csv · outputs/eda/fuentes_correlacion_*.csv</Fuente>
        </div>
        <div className="flex flex-col gap-7 pt-6">
          <Revelar paso={1}>
            <Cifra valor={num(c.policia_fiscalia, 3)} etiqueta="correlación Policía–Fiscalía" detalle="Pearson, mensual" />
          </Revelar>
          <Revelar paso={2}>
            <Cifra tono="verde" valor={num(c.policia_linea123, 3)} etiqueta="correlación Policía–Línea 123" />
          </Revelar>
          <Revelar paso={3}>
            <Cifra tono="oxido" valor={num(c.policia_linea123_sin2020, 3)} etiqueta="la misma, sin 2020" detalle="Gran parte de la coincidencia viene de la caída compartida de 2020." />
          </Revelar>
        </div>
      </div>
    </Marco>
  );
}

function Territorio() {
  const filas = territorio.filter((l) => l.puesto_tasa <= 6 || ["KENNEDY", "ENGATIVÁ", "SUBA", "BOSA"].includes(l.localidad));
  const nombre = (s: string) =>
    s.toLowerCase().replace(/(^|\s)\S/g, (c) => c.toUpperCase()).replace("Candelaria", "La Candelaria");
  return (
    <Marco
      seccion="Análisis exploratorio · territorio"
      titulo="El orden de las localidades depende del denominador"
      mensaje="Kennedy es la primera por número de llamadas y la 13.ª por tasa; Los Mártires, la 14.ª por número, es la primera por tasa. Ninguno de los dos órdenes mide peligrosidad."
    >
      <div className="grid grid-cols-[1fr_440px] gap-12">
        <div>
          <Rotulo>Llamadas de hurto a la Línea 123, 2020–2025</Rotulo>
          <table className="mt-3 w-full text-[21px] tabular">
            <thead>
              <tr className="border-b-2 border-tinta text-left text-[16px] uppercase tracking-[0.08em] text-gris">
                <th className="py-2 font-semibold">Localidad</th>
                <th className="py-2 text-right font-semibold">Llamadas</th>
                <th className="py-2 text-right font-semibold">Puesto por número</th>
                <th className="py-2 text-right font-semibold">Tasa por 100.000</th>
                <th className="py-2 text-right font-semibold">Puesto por tasa</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((l) => {
                const destacada = ["KENNEDY", "LOS MÁRTIRES", "CANDELARIA"].includes(l.localidad);
                return (
                  <tr key={l.localidad} className={`border-b border-linea ${destacada ? "bg-azul-claro/70" : ""}`}>
                    <td className="py-[9px] pl-2 font-semibold">{nombre(l.localidad)}</td>
                    <td className="py-[9px] text-right">{num(l.incidentes)}</td>
                    <td className="py-[9px] text-right">{l.puesto_conteo}.º</td>
                    <td className="py-[9px] text-right">{num(l.tasa, 1)}</td>
                    <td className="py-[9px] pr-2 text-right font-semibold text-azul">{l.puesto_tasa}.º</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="mt-4 text-[19px] leading-snug text-gris">
            La tasa usa población residente: en las localidades del centro, con mucha población flotante, la sobrestima.
            La Línea 123 mide llamadas tramitadas, no hechos.
          </p>
          <div className="mt-2">
            <Fuente>outputs/eda/territorial_tasas.csv · población: SDP 2025</Fuente>
          </div>
        </div>
        <Revelar paso={1} className="flex justify-center">
          <img src="./assets/eda_mapa_tasa.png" alt="Mapa de la tasa de llamadas de hurto por localidad" className="h-[620px] w-auto" />
        </Revelar>
      </div>
    </Marco>
  );
}

export const DATOS: Diapositiva[] = [
  {
    id: "auditoria",
    seccion: "Datos",
    titulo: "Auditoría y embudo",
    expone: "Juan Diego",
    Contenido: Auditoria,
    notas: {
      guion: [
        "Para la Policía, el embudo arranca con 4,8 millones de filas: todos los delitos del país en los archivos de 2020 a 2025.",
        { accion: "Señalar las barras de arriba abajo." },
        "Con solo Bogotá quedan 1,4 millones; con solo hurto a personas, 741.986; y en el periodo de la serie, 730.870 víctimas.",
        { accion: "Señalar el recuadro «Tres advertencias de la auditoría»." },
        "Lo más llamativo: 713.344 filas son duplicados exactos, y no es un error. El archivo no trae identificador, así que dos víctimas del mismo perfil el mismo día dan filas idénticas. Borrarlas dejaría 28.642 filas.",
        "Además, noviembre y diciembre de 2025 caen a la mitad sin que lo haga la Línea 123, y por eso se excluyen.",
      ],
      enfatizar: [
        "Contamos filas en una sola unidad de observación: una víctima por fila.",
        "Cada archivo tiene su huella SHA-256 en el apéndice, para que cualquiera compruebe que usa los mismos datos.",
      ],
      transicion: "Con esos registros construimos la serie diaria. Sara, ¿cómo se comporta?",
      preguntas: [
        {
          pregunta: "¿Cómo saben que los duplicados no son errores?",
          respuesta: "Cada fila trae CANTIDAD = 1 y la suma por día coincide con el agregado diario de MinDefensa: exacta en 2020, 2021, 2022, 2023 y 2025, y con una unidad de diferencia en 2024. Si fueran errores, el agregado no cuadraría.",
        },
        {
          pregunta: "¿Por qué excluir noviembre y diciembre de 2025?",
          respuesta: "El registro cae un 51,6 % y un 49,1 % frente a la media de los diez meses anteriores, mientras la Línea 123 apenas se mueve. La causa no está establecida (consolidación incompleta o cambio de registro), y con esos meses en la evaluación un modelo podría parecer que acierta una caída que no es del fenómeno.",
        },
      ],
    },
  },
  {
    id: "serie",
    seccion: "Datos",
    titulo: "Serie objetivo",
    expone: "Sara",
    Contenido: SerieObjetivo,
    notas: {
      guion: [
        "Gracias, Juan Diego. Esta es la serie que vamos a pronosticar, resumida como la media diaria de víctimas de cada mes. La línea punteada es la media de todo el periodo: 343 víctimas por día.",
        { accion: "Señalar el sombreado de 2020." },
        "En abril de 2020, con las restricciones de movilidad, la serie cae por debajo de la mitad; ese año tiene una media de 227 víctimas al día. Luego sube hasta el pico de 2023, con 435, baja en 2024 y se recupera en 2025.",
        "Los modelos tendrán que seguir ese cambio de nivel. A 2020 no lo eliminamos: entra marcado como atípico, y las conclusiones no dependen de él.",
      ],
      enfatizar: [
        "2020 no se elimina: entra con un indicador de año atípico y se prueba la sensibilidad sin él.",
        "Con un año truncado se comparan medias diarias, nunca totales.",
      ],
      transicion: "Dentro de cada semana aparece una regularidad mucho más fuerte.",
      preguntas: [
        {
          pregunta: "¿Por qué no quitar 2020?",
          respuesta: "Porque lo que se sabe es que su nivel coincide con las restricciones de movilidad, no cuánto de la caída es menos hechos y cuánto menos denuncias. Se conserva marcado y se comprobó que sin él el MAE final cambia entre −0,57 y +0,79: ninguna conclusión depende de cómo se trate.",
        },
      ],
    },
  },
  {
    id: "patrones",
    seccion: "Análisis exploratorio",
    titulo: "Ciclo semanal y festivos",
    expone: "Sara",
    Contenido: Patrones,
    notas: {
      guion: [
        "El hurto registrado sigue la actividad de la ciudad.",
        { accion: "Señalar la barra azul del viernes y la roja del domingo." },
        "El viernes es el día más alto, con 403 víctimas de media, y el domingo el más bajo, con 245: el viernes registra un 65 % más.",
        { accion: "Señalar el recuadro del festivo." },
        "Con los festivos hay una trampa. En Colombia muchos festivos se trasladan al lunes, que ya es un día bajo, así que comparar festivo contra no festivo mezclaría los dos efectos. Por eso comparamos lunes con lunes: un lunes festivo registra un 37,8 % menos que uno laborable.",
        "La estacionalidad por mes existe, pero es mucho más débil. Estas dos señales, el día de la semana y el festivo, son las que después esperamos encontrar dentro de los modelos.",
      ],
      enfatizar: [
        "El festivo es una variable que se conoce con años de antelación: no hay riesgo de fuga al usarla.",
        "Estas dos señales son la hipótesis que después contrastamos con lo que aprendieron los modelos.",
      ],
      transicion: "Ahora pongamos las tres fuentes una al lado de la otra.",
    },
  },
  {
    id: "fuentes",
    seccion: "Análisis exploratorio",
    titulo: "Las fuentes no se suman",
    expone: "Sara",
    Contenido: FuentesNoSeSuman,
    notas: {
      guion: [
        "Para comparar las fuentes sin sumarlas, expresamos cada una como un índice de su propia media, en los 70 meses que tienen en común.",
        { accion: "Señalar las líneas azul y ocre." },
        "La Policía y la Fiscalía casi se superponen: su correlación es de 0,962. Son dos registros institucionales del mismo proceso.",
        { accion: "Señalar la línea verde." },
        "La Línea 123 se separa. Su correlación con la Policía es de 0,601, y si quitamos 2020 baja a 0,284: buena parte de la coincidencia era la caída compartida de 2020.",
        "Esto responde la pregunta complementaria: las fuentes no son intercambiables, y cada una se usa en la resolución que publica.",
      ],
      enfatizar: ["Esto responde la pregunta complementaria: las fuentes no son intercambiables y cada una se usa en su resolución."],
      transicion: "Lo que sí permite la Línea 123 es mirar el territorio.",
    },
  },
  {
    id: "territorio",
    seccion: "Análisis exploratorio",
    titulo: "Territorio: número frente a tasa",
    expone: "Sara",
    Contenido: Territorio,
    notas: {
      guion: [
        "Si contamos llamadas, Kennedy, Engativá y Suba encabezan la lista, pero también son las localidades más pobladas.",
        { accion: "Señalar las filas resaltadas: Los Mártires, La Candelaria y Kennedy." },
        "Al dividir por población el orden cambia por completo. Los Mártires pasa del puesto 14 al primero, con 3,7 veces la tasa de Kennedy, y La Candelaria, penúltima por número, queda cuarta por tasa. En el mapa se ve que las tasas altas se concentran en el centro.",
        "Pero hay dos cuidados. La tasa usa la población residente, y el centro recibe mucha población flotante, así que ahí está sobrestimada. Y ninguno de los dos órdenes mide peligrosidad: describen dónde se pide atención.",
      ],
      enfatizar: [
        "La tasa usa población residente y el centro recibe mucha población flotante: la tasa allí está sobrestimada.",
        "Ninguno de los dos órdenes mide peligrosidad ni dice nada de quienes viven en cada localidad.",
      ],
      transicion: "Hasta aquí la descripción. Ahora, cómo planteamos el pronóstico.",
      preguntas: [
        {
          pregunta: "¿Por qué no modelaron por localidad?",
          respuesta: "Porque la variable objetivo es el registro de la Policía, que no identifica la localidad. Inferir conteos diarios por localidad desde la Línea 123 sería inventar datos. Si la Policía publicara la localidad, sería el siguiente paso, con las cautelas sobre bucles de retroalimentación.",
        },
      ],
    },
  },
];

