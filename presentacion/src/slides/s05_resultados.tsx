import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Line,
  LineChart,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";
import { Cifra, Fuente, Leyenda, Panel, Rotulo } from "../components/piezas";
import { Revelar } from "../components/Revelar";
import { COLOR, MODELOS_FINALES, NOMBRE } from "../data/colores";
import { interpretacion, modelo, modelos, pronostico } from "../data/datos";
import { fechaCorta, num, valorP } from "../data/formato";
import { useAnimar, useModo } from "../hooks/modo";
import { Marco } from "../layouts/Marco";
import type { Diapositiva } from "./tipos";

const EJE = { fontSize: 18, fill: "#5b6472" };
const barra = modelo("ingenuo_estacional");

function Resultados() {
  const animar = useAnimar();
  const filas = [...MODELOS_FINALES.map((id) => modelo(id)), barra];
  const datos = filas.map((m) => ({ id: m.id, nombre: m.id === "ingenuo_estacional" ? "Ingenuo estacional" : m.nombre, MAE: m.MAE }));
  return (
    <Marco
      seccion="Resultados"
      titulo="Los cinco modelos bajan el error de la barra entre un 26 y un 33 %"
      mensaje={<>Evaluación final: 184 días, de mayo a octubre de 2025. La diferencia con la barra es significativa en los cinco (Diebold-Mariano, p entre 1·10<sup>−9</sup> y 7·10<sup>−6</sup>).</>}
    >
      <div className="grid grid-cols-[820px_1fr] gap-14">
        <div>
          <Rotulo>MAE en la evaluación final (víctimas por día)</Rotulo>
          <BarChart width={820} height={470} data={datos} layout="vertical" margin={{ top: 12, right: 90, bottom: 8, left: 10 }}>
            <CartesianGrid stroke="#ebe9e3" horizontal={false} />
            <XAxis type="number" domain={[0, 55]} ticks={[0, 10, 20, 30, 40, 50]} tick={EJE} tickLine={false} axisLine={{ stroke: "#cfcac0" }} />
            <YAxis type="category" dataKey="nombre" width={260} tick={{ fontSize: 20, fill: "#14213d" }} tickLine={false} axisLine={false} />
            <ReferenceLine x={barra.MAE} stroke={COLOR.oxido} strokeDasharray="6 4" strokeWidth={2} />
            <Bar dataKey="MAE" barSize={42} radius={[0, 6, 6, 0]} isAnimationActive={animar}>
              {datos.map((d) => (
                <Cell key={d.id} fill={d.id === "ingenuo_estacional" ? COLOR.barra : COLOR[d.id as keyof typeof COLOR]} />
              ))}
              <LabelList dataKey="MAE" position="right" formatter={(v: unknown) => num(Number(v), 2)} style={{ fontSize: 21, fill: "#14213d", fontWeight: 600 }} />
            </Bar>
          </BarChart>
          <Fuente>outputs/modelado/comparacion/tabla_comparativa.csv</Fuente>
        </div>
        <Revelar paso={1}>
          <table className="w-full text-[20.5px] tabular">
            <thead>
              <tr className="border-b-2 border-tinta text-right text-[15px] uppercase tracking-[0.08em] text-gris">
                <th className="py-2 text-left font-semibold">Modelo</th>
                <th className="py-2 font-semibold">RMSE</th>
                <th className="py-2 font-semibold">MASE</th>
                <th className="py-2 font-semibold">ΔMAE</th>
                <th className="py-2 font-semibold">p</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((m) => (
                <tr key={m.id} className={`border-b border-linea text-right ${m.id === "ingenuo_estacional" ? "font-semibold" : ""}`}>
                  <td className="py-[11px] text-left">
                    <span className="mr-3 inline-block h-3 w-3 rounded-sm" style={{ background: m.id === "ingenuo_estacional" ? COLOR.barra : COLOR[m.id as keyof typeof COLOR] }} />
                    {m.id === "ingenuo_estacional" ? "Barra" : m.nombre}
                  </td>
                  <td className="py-[11px]">{num(m.RMSE, 2)}</td>
                  <td className="py-[11px]">{num(m.MASE, 3)}</td>
                  <td className="py-[11px]">{m.delta_pct == null || m.id === "ingenuo_estacional" ? "—" : `${num(m.delta_pct, 1)} %`}</td>
                  <td className="py-[11px]">
                    {m.p == null ? "—" : (
                      <>
                        {valorP(m.p).texto}
                        {valorP(m.p).exponente && <sup>{valorP(m.p).exponente}</sup>}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-7 grid grid-cols-2 gap-8">
            <Cifra valor="10 %" etiqueta="error relativo al valor diario, aproximado" detalle="MAPE entre 9,50 y 10,47 %, frente a 14,39 % de la barra" />
            <Cifra tono="verde" valor="0,62–0,68" etiqueta="MASE de los cinco modelos" detalle="Menor que 1: mejor que repetir la semana anterior" />
          </div>
        </Revelar>
      </div>
    </Marco>
  );
}

const SELECCIONABLES = ["gradiente_histogramas", "ets", "regresion_lineal"] as const;

function Pronostico() {
  const animar = useAnimar();
  const { impresion } = useModo();
  const [sel, setSel] = useState<(typeof SELECCIONABLES)[number]>("gradiente_histogramas");
  const festivos = pronostico.filter((d) => d.festivo === 1).map((d) => d.fecha);
  return (
    <Marco
      seccion="Resultados"
      titulo="Los modelos siguen el ciclo semanal; la barra repite los días anómalos"
      mensaje="Víctimas diarias observadas y pronosticadas un día adelante en los 184 días de evaluación. La barra copia cada anomalía una semana tarde. Las líneas verticales marcan los 8 festivos."
    >
      <div className="flex items-center justify-between">
        <Leyenda
          items={[
            { color: COLOR.observado, nombre: "Observado", grosor: 2 },
            { color: COLOR[sel], nombre: NOMBRE[sel] },
            { color: COLOR.barra, nombre: "Ingenuo estacional (barra)", discontinua: true },
          ]}
        />
        {!impresion && (
          <div className="no-imprimir flex gap-2" onClick={(e) => e.stopPropagation()}>
            {SELECCIONABLES.map((m) => (
              <button
                key={m}
                onClick={() => setSel(m)}
                className={`rounded-full border px-4 py-1.5 text-[17px] ${sel === m ? "border-azul bg-azul text-white" : "border-linea bg-white text-tinta hover:border-azul"}`}
              >
                {NOMBRE[m]}
              </button>
            ))}
          </div>
        )}
      </div>
      <LineChart width={1760} height={530} data={pronostico} margin={{ top: 20, right: 16, bottom: 6, left: 0 }}>
        <CartesianGrid stroke="#ebe9e3" vertical={false} />
        <XAxis dataKey="fecha" tick={EJE} tickFormatter={(f: string) => (f.endsWith("-01") ? fechaCorta(f) : "")} interval={0} tickLine={false} axisLine={{ stroke: "#cfcac0" }} />
        <YAxis tick={EJE} domain={[100, 600]} ticks={[100, 200, 300, 400, 500, 600]} width={60} tickLine={false} axisLine={false} />
        {festivos.map((f) => (
          <ReferenceLine key={f} x={f} stroke={COLOR.oxido} strokeOpacity={0.35} strokeWidth={2} />
        ))}
        <Line dataKey="barra" stroke={COLOR.barra} strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={animar} />
        <Line dataKey="real" stroke={COLOR.observado} strokeWidth={1.8} dot={false} isAnimationActive={animar} />
        <Line key={sel} dataKey={sel} stroke={COLOR[sel]} strokeWidth={3} dot={false} isAnimationActive={animar} animationDuration={900} />
      </LineChart>
      <div className="mt-1 flex justify-between">
        <span className="text-[18px] text-gris">
          MAE en estos días: {NOMBRE[sel]} {num(modelo(sel).MAE, 2)} · barra {num(barra.MAE, 2)}
        </span>
        <Fuente>outputs/modelado/ajuste/ y regresion/predicciones_por_pliegue.csv</Fuente>
      </div>
    </Marco>
  );
}

function Pliegues() {
  const animar = useAnimar();
  const finales = MODELOS_FINALES.map((id) => modelo(id));
  return (
    <Marco
      seccion="Validación"
      titulo="La mejora no depende de una ventana: los cinco ganan en los seis pliegues"
      mensaje="Los modelos y la barra coinciden en qué ventanas son difíciles, pero en ellas la barra empeora mucho más."
    >
      <div className="grid grid-cols-[1fr_560px] gap-12">
        <div>
          <Rotulo>MAE por pliegue de validación</Rotulo>
          <div className="mt-3">
            <Leyenda items={[...MODELOS_FINALES.map((id) => ({ color: COLOR[id], nombre: NOMBRE[id] })), { color: COLOR.barra, nombre: "Barra", discontinua: true }]} />
          </div>
          <LineChart width={1150} height={480} data={modelos.pliegues} margin={{ top: 18, right: 20, bottom: 24, left: 0 }}>
            <CartesianGrid stroke="#ebe9e3" vertical={false} />
            <XAxis
              dataKey="pliegue"
              tick={EJE}
              tickFormatter={(p: number) => ["nov 23–feb 24", "feb–may 24", "may–ago 24", "ago–nov 24", "nov 24–ene 25", "ene–abr 25"][p - 1]}
              tickLine={false}
              axisLine={{ stroke: "#cfcac0" }}
              padding={{ left: 30, right: 30 }}
            />
            <YAxis tick={EJE} domain={[20, 80]} ticks={[20, 30, 40, 50, 60, 70, 80]} width={56} tickLine={false} axisLine={false} />
            <Line dataKey="barra" stroke={COLOR.barra} strokeWidth={3} strokeDasharray="7 5" dot={{ r: 5, fill: COLOR.barra }} isAnimationActive={animar} />
            {MODELOS_FINALES.map((id) => (
              <Line key={id} dataKey={id} stroke={COLOR[id]} strokeWidth={id === "gradiente_histogramas" ? 3.5 : 2.5} dot={{ r: 4, fill: COLOR[id] }} isAnimationActive={animar} />
            ))}
          </LineChart>
          <Fuente>outputs/modelado/comparacion/mae_por_pliegue.csv</Fuente>
        </div>
        <Revelar paso={1}>
          <table className="w-full text-[20px] tabular">
            <thead>
              <tr className="border-b-2 border-tinta text-right text-[14px] uppercase tracking-[0.08em] text-gris">
                <th className="py-2 text-left font-semibold">Modelo</th>
                <th className="py-2 font-semibold">Media</th>
                <th className="py-2 font-semibold">Desv.</th>
                <th className="py-2 font-semibold">Peor</th>
              </tr>
            </thead>
            <tbody>
              {[...finales].sort((a, b) => (a.mae_medio_pliegues ?? 0) - (b.mae_medio_pliegues ?? 0)).concat(barra).map((m) => (
                <tr key={m.id} className={`border-b border-linea text-right ${m.id === "ingenuo_estacional" ? "font-semibold" : ""}`}>
                  <td className="py-[10px] text-left">{m.id === "ingenuo_estacional" ? "Barra" : m.nombre}</td>
                  <td className="py-[10px]">{num(m.mae_medio_pliegues ?? 0, 2)}</td>
                  <td className="py-[10px]">{num(m.desv_pliegues ?? 0, 2)}</td>
                  <td className="py-[10px]">{num(m.peor_pliegue ?? 0, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Panel tono="panel" className="mt-6 p-6">
            <p className="text-[19px] leading-snug">
              El orden en los pliegues no anticipa el de la evaluación final: la regresión es segunda en los pliegues y
              última en la evaluación. Y la media del gradiente es su criterio de selección, así que no es independiente.
            </p>
          </Panel>
        </Revelar>
      </div>
    </Marco>
  );
}

const ORDEN = ["gradiente_histogramas", "ets", "sarima", "bosque_aleatorio", "regresion_lineal"];

function SinGanador() {
  const p = (a: string, b: string) => modelos.dm.find((d) => (d.a.startsWith(a) && d.b.startsWith(b)) || (d.a.startsWith(b) && d.b.startsWith(a)));
  const celda = 172;
  return (
    <Marco
      seccion="Validación · comparación entre modelos"
      titulo="Entre los cuatro mejores no hay un ganador"
      mensaje="Prueba de Diebold-Mariano por pares, con pérdida absoluta. Ningún par de los cuatro primeros se distingue; la regresión solo se separa del gradiente, y no de forma robusta."
    >
      <div className="grid grid-cols-[auto_1fr] gap-14">
        <Revelar>
          <div className="grid" style={{ gridTemplateColumns: `230px repeat(4, ${celda}px)` }}>
            <div />
            {ORDEN.slice(0, 4).map((c) => (
              <div key={c} className="px-2 pb-3 text-center text-[17px] font-semibold leading-tight" style={{ color: COLOR[c as keyof typeof COLOR] }}>
                {NOMBRE[c]}
              </div>
            ))}
            {ORDEN.slice(1).map((f, i) => (
              <div key={f} className="contents">
                <div className="flex items-center pr-4 text-right text-[19px] font-semibold leading-tight" style={{ color: COLOR[f as keyof typeof COLOR] }}>
                  <span className="ml-auto">{NOMBRE[f]}</span>
                </div>
                {ORDEN.slice(0, 4).map((c, j) => {
                  if (j > i) return <div key={c} />;
                  const r = p(f, c)!;
                  const sig = r.p_hln < 0.05;
                  return (
                    <div key={c} className={`m-[3px] flex flex-col items-center justify-center rounded-[10px] border ${sig ? "border-oxido bg-oxido-claro" : "border-linea bg-white"}`} style={{ height: 104 }}>
                      <span className={`font-serif text-[30px] font-semibold tabular ${sig ? "text-oxido" : "text-tinta"}`}>{num(r.p_hln, 3)}</span>
                      <span className="text-[15px] text-gris tabular">NW: {num(r.p_nw, 3)}</span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div className="mt-3">
            <Fuente>outputs/modelado/comparacion/diebold_mariano_entre_modelos.csv</Fuente>
          </div>
        </Revelar>
        <div className="flex flex-col gap-6">
          <Revelar paso={1}>
            <Panel className="p-7">
              <Rotulo>Cómo leer la tabla</Rotulo>
              <p className="mt-2 text-[20px] leading-snug">
                Número grande: valor <i>p</i> con la corrección de Harvey, Leybourne y Newbold. Debajo, con la varianza de
                Newey-West de 7 rezagos, que tiene en cuenta que los errores de días consecutivos están correlacionados.
              </p>
            </Panel>
          </Revelar>
          <Revelar paso={2}>
            <Panel tono="oxido" className="p-7">
              <p className="text-[20px] leading-snug">
                Gradiente frente a regresión: <b>p = 0,023</b>, pero <b>0,073</b> con Newey-West. Además son diez
                comparaciones sin corrección por multiplicidad. La regresión es la más débil sin que eso se pueda afirmar con
                solidez.
              </p>
            </Panel>
          </Revelar>
          <Revelar paso={3}>
            <p className="text-[21px] leading-snug">
              <b>Conclusión:</b> el orden de la tabla de resultados describe esta ventana, no una clasificación general. Lo
              que sí se sostiene es que los cinco superan la barra, y en todos los pliegues.
            </p>
          </Revelar>
        </div>
      </div>
    </Marco>
  );
}

function Festivos() {
  const animar = useAnimar();
  const datos = modelos.festivos.map((f) => ({ ...f, corto: f.nombre.replace(" (barra)", "").replace("Gradiente por histogramas", "Gradiente").replace("Ingenuo estacional", "Barra") }));
  return (
    <Marco
      seccion="Resultados · dónde se separan"
      titulo="Los festivos separan a los modelos con calendario de los demás"
      mensaje="En los 8 festivos de la evaluación, SARIMA y ETS sobrestiman en más de 55 víctimas: pronostican el festivo como un día normal de su día de la semana."
    >
      <div className="grid grid-cols-[1fr_520px] gap-12">
        <div>
          <div className="flex items-center justify-between">
            <Rotulo>MAE según el tipo de día (víctimas por día)</Rotulo>
            <div className="flex gap-6 text-[18px]">
              <span className="inline-flex items-center gap-2"><span className="h-4 w-4 rounded-sm bg-oxido" /> Festivos (8 días)</span>
              <span className="inline-flex items-center gap-2"><span className="h-4 w-4 rounded-sm bg-[#c3d0e0]" /> No festivos (176)</span>
            </div>
          </div>
          <BarChart width={1180} height={500} data={datos} margin={{ top: 36, right: 10, bottom: 4, left: 0 }} barGap={6}>
            <CartesianGrid stroke="#ebe9e3" vertical={false} />
            <XAxis dataKey="corto" tick={{ ...EJE, fontSize: 19, fill: "#14213d" }} tickLine={false} axisLine={{ stroke: "#cfcac0" }} interval={0} />
            <YAxis tick={EJE} domain={[0, 90]} ticks={[0, 20, 40, 60, 80]} width={50} tickLine={false} axisLine={false} />
            <Bar dataKey="mae_festivo" fill={COLOR.oxido} radius={[5, 5, 0, 0]} barSize={56} isAnimationActive={animar}>
              <LabelList dataKey="mae_festivo" position="top" formatter={(v: unknown) => num(Number(v), 1)} style={{ fontSize: 18, fill: "#b4441a", fontWeight: 600 }} />
            </Bar>
            <Bar dataKey="mae_no_festivo" fill="#c3d0e0" radius={[5, 5, 0, 0]} barSize={56} isAnimationActive={animar}>
              <LabelList dataKey="mae_no_festivo" position="top" formatter={(v: unknown) => num(Number(v), 1)} style={{ fontSize: 18, fill: "#5b6472" }} />
            </Bar>
          </BarChart>
          <Fuente>outputs/modelado/comparacion/errores_por_periodo.csv</Fuente>
        </div>
        <Revelar paso={1}>
          <Rotulo>Sesgo en festivos (pronóstico − observado)</Rotulo>
          <table className="mt-3 w-full text-[21px] tabular">
            <tbody>
              {modelos.festivos.map((f) => (
                <tr key={f.nombre} className="border-b border-linea">
                  <td className="py-[10px]">{f.nombre.replace(" (barra)", "")}</td>
                  <td className={`py-[10px] text-right font-semibold ${f.sesgo_festivo > 0 ? "text-oxido" : "text-azul"}`}>
                    {f.sesgo_festivo > 0 ? "+" : ""}
                    {num(f.sesgo_festivo, 1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-5 text-[19px] leading-snug text-gris">
            Los árboles, que tienen la variable de festivo, bajan ese error a 36,7 y 42,7, aunque tienden a subestimar.
            Con solo ocho festivos, la magnitud es imprecisa.
          </p>
        </Revelar>
      </div>
    </Marco>
  );
}

function Interpretacion() {
  const animar = useAnimar();
  const grupos = interpretacion.grupos.filter((g) => g.grupo !== "Indicador de 2020");
  return (
    <Marco
      seccion="Interpretación"
      titulo="Los modelos se apoyan en lo que anticipó el análisis exploratorio, y en el día anterior"
      mensaje="Importancia por permutación agrupada: cuánto sube el MAE de la evaluación al desordenar cada grupo de variables. Describe dependencia, no causa."
    >
      <div className="grid grid-cols-[1fr_700px] gap-12">
        <div>
          <div className="flex items-center justify-between">
            <Rotulo>Aumento del MAE al permutar el grupo (%)</Rotulo>
            <div className="flex gap-6 text-[18px]">
              <span className="inline-flex items-center gap-2"><span className="h-4 w-4 rounded-sm" style={{ background: COLOR.gradiente_histogramas }} /> Gradiente</span>
              <span className="inline-flex items-center gap-2"><span className="h-4 w-4 rounded-sm" style={{ background: COLOR.bosque_aleatorio }} /> Bosque aleatorio</span>
            </div>
          </div>
          <BarChart width={1000} height={520} data={grupos} layout="vertical" margin={{ top: 10, right: 70, bottom: 4, left: 10 }} barGap={4}>
            <CartesianGrid stroke="#ebe9e3" horizontal={false} />
            <XAxis type="number" domain={[0, 45]} ticks={[0, 10, 20, 30, 40]} tick={EJE} tickLine={false} axisLine={{ stroke: "#cfcac0" }} />
            <YAxis type="category" dataKey="grupo" width={330} tick={{ fontSize: 19, fill: "#14213d" }} tickLine={false} axisLine={false} />
            <Bar dataKey="gradiente" fill={COLOR.gradiente_histogramas} barSize={24} radius={[0, 4, 4, 0]} isAnimationActive={animar}>
              <LabelList dataKey="gradiente" position="right" formatter={(v: unknown) => num(Number(v), 1)} style={{ fontSize: 17, fill: "#14213d" }} />
            </Bar>
            <Bar dataKey="bosque" fill={COLOR.bosque_aleatorio} barSize={24} radius={[0, 4, 4, 0]} isAnimationActive={animar}>
              <LabelList dataKey="bosque" position="right" formatter={(v: unknown) => num(Number(v), 1)} style={{ fontSize: 17, fill: "#5b6472" }} />
            </Bar>
          </BarChart>
          <Fuente>outputs/modelado/interpretacion/importancia_grupos_evaluacion.csv (50 permutaciones)</Fuente>
        </div>
        <Revelar paso={1}>
          <Rotulo>¿Reproducen la magnitud del análisis exploratorio?</Rotulo>
          <table className="mt-3 w-full text-[20px] tabular">
            <thead>
              <tr className="border-b-2 border-tinta text-right text-[14px] uppercase tracking-[0.08em] text-gris">
                <th className="py-2 text-left font-semibold">Señal</th>
                <th className="w-[110px] py-2 font-semibold">Datos</th>
                <th className="w-[120px] py-2 font-semibold">Gradiente</th>
                <th className="w-[110px] py-2 font-semibold">Bosque</th>
              </tr>
            </thead>
            <tbody className="whitespace-nowrap">
              <tr className="border-b border-linea text-right">
                <td className="py-[12px] text-left whitespace-normal">Lunes festivo frente a laborable</td>
                <td className="py-[12px]">−37,8 %</td>
                <td className="py-[12px] font-semibold text-azul">−37,3 %</td>
                <td className="py-[12px]">−30,2 %</td>
              </tr>
              <tr className="border-b border-linea text-right">
                <td className="py-[12px] text-left whitespace-normal">Viernes frente a domingo, en la evaluación</td>
                <td className="py-[12px]">+42,5 %</td>
                <td className="py-[12px]">+47,3 %</td>
                <td className="py-[12px]">+39,7 %</td>
              </tr>
            </tbody>
          </table>
          <Panel tono="azul" className="mt-6 p-6">
            <p className="text-[19px] leading-snug">
              <b>Regresión lineal:</b> cada víctima del día anterior suma {num(interpretacion.coeficientes.find((c) => c.variable === "rezago_1")!.por_unidad, 2)} al
              pronóstico, y el festivo resta {num(-interpretacion.coeficientes.find((c) => c.variable === "festivo")!.por_unidad, 1)} víctimas,
              del orden de las 122 que separan un lunes laborable de uno festivo.
            </p>
          </Panel>
          <p className="mt-4 text-[18px] leading-snug text-gris">
            SARIMA y ETS no tienen variables que permutar: su estructura ya dice que solo usan la serie y el ciclo de 7 días.
          </p>
        </Revelar>
      </div>
    </Marco>
  );
}

export const RESULTADOS: Diapositiva[] = [
  {
    id: "resultados",
    seccion: "Resultados",
    titulo: "Comparación con la barra",
    minutos: 2,
    expone: "Juan Diego",
    Contenido: Resultados,
    notas: {
      guion: [
        "Este es el resultado principal. La línea discontinua roja es la barra: el ingenuo estacional, con 49,04 víctimas por día de error.",
        "Los cinco modelos quedan muy por debajo. SARIMA, ETS y los dos árboles entre 32,72 y 34,22: entre un 30 y un 33 % menos. La regresión lineal, 36,31: un 26 % menos.",
        "La columna p es la prueba de Diebold-Mariano contra la barra: compara día a día la pérdida de los dos pronósticos. En los cinco la diferencia es muy significativa, y se mantiene con pérdida cuadrática y con Newey-West.",
        "En términos prácticos, el error es de alrededor del 10 % del valor diario, frente al 14 % de la barra.",
      ],
      enfatizar: [
        "La evaluación final se calculó una sola vez, después de elegir todo con los pliegues.",
        "El MASE menor que 1 significa que el modelo se equivoca menos que repetir la semana anterior.",
      ],
      transicion: "Veamos qué significa eso día a día.",
      preguntas: [
        {
          pregunta: "¿Qué es exactamente la prueba de Diebold-Mariano?",
          respuesta: "Toma la diferencia diaria entre las pérdidas de dos pronósticos, aquí el error absoluto, y contrasta si su media es cero. Usamos la corrección de Harvey, Leybourne y Newbold para muestras pequeñas, y como robustez la varianza de Newey-West con 7 rezagos, porque los errores de días consecutivos están correlacionados.",
        },
        {
          pregunta: "¿Un error de 33 víctimas al día es bueno?",
          respuesta: "Es un 33 % menos que la mejor regla trivial y alrededor del 10 % del valor diario. Si alcanza para un uso concreto depende del uso; el proyecto no evalúa uso operativo, y para eso faltan intervalos de predicción y medir el retraso de publicación.",
        },
      ],
    },
  },
  {
    id: "pronostico",
    seccion: "Resultados",
    titulo: "Pronóstico frente a observado",
    minutos: 1.25,
    expone: "Juan Diego",
    Contenido: Pronostico,
    notas: {
      guion: [
        "Aquí están los 184 días. En negro lo observado, en azul el gradiente y en gris discontinuo la barra.",
        "El modelo sigue el ciclo semanal. La barra, en cambio, repite con una semana de retraso cualquier día anómalo: se ven picos y caídas aislados que aparecen siete días tarde.",
        "Las líneas verticales son los ocho festivos. Con los botones de arriba se puede cambiar a ETS o a la regresión.",
      ],
      enfatizar: ["Mostrar ETS en un festivo: el modelo no baja, porque no sabe que es festivo."],
      transicion: "¿Y si la ventana de evaluación hubiera sido otra?",
    },
  },
  {
    id: "pliegues",
    seccion: "Validación",
    titulo: "Estabilidad en los pliegues",
    minutos: 1.5,
    expone: "Juan Diego",
    Contenido: Pliegues,
    notas: {
      guion: [
        "Batir la barra en una sola ventana no basta. Aquí está el MAE en los seis pliegues.",
        "Los cinco modelos ganan a la barra en los seis. Su peor pliegue, entre 35,49 y 44,61, queda muy por debajo del peor de la barra, 75,57.",
        "También varían mucho menos: la desviación entre pliegues va de 4,34 a 7,46, frente a 14,11 de la barra.",
        "El pliegue 5, noviembre a enero, es difícil para todos: los festivos de fin de año rompen el ciclo semanal.",
      ],
      enfatizar: [
        "El orden de los modelos cambia entre pliegues y evaluación: otra razón para no hablar de un ganador.",
      ],
      transicion: "Precisamente: ¿hay un modelo ganador?",
    },
  },
  {
    id: "sin-ganador",
    seccion: "Validación",
    titulo: "Diebold-Mariano entre modelos",
    minutos: 1.5,
    expone: "Juan Diego",
    Contenido: SinGanador,
    notas: {
      guion: [
        "Esta matriz compara los modelos entre sí. Cada celda es el valor p de la prueba de Diebold-Mariano para ese par.",
        "Entre los cuatro primeros, los valores van de 0,17 a 0,91: ninguna diferencia es significativa.",
        "La única celda en rojo es el gradiente frente a la regresión: 0,023. Pero con Newey-West sube a 0,073, y son diez comparaciones sin corregir por multiplicidad.",
        "La conclusión honesta es que con estos 184 días no hay un ganador.",
      ],
      enfatizar: ["Lo robusto no es el orden entre modelos, sino que todos superan la barra."],
      transicion: "Pero hay un tipo de día en que los modelos sí se separan.",
      preguntas: [
        {
          pregunta: "Entonces, ¿qué modelo recomendarían?",
          respuesta: "Ninguno destaca con la evidencia disponible. Si hubiera que elegir, un modelo con calendario, como los árboles, por su comportamiento en festivos; o ETS, si se prefiere simplicidad y se corrigen los festivos aparte. El informe deja esa elección abierta.",
        },
      ],
    },
  },
  {
    id: "festivos",
    seccion: "Resultados",
    titulo: "Errores en festivos",
    minutos: 1.25,
    expone: "Juan Diego",
    Contenido: Festivos,
    notas: {
      guion: [
        "En los días no festivos, todos los modelos están entre 31 y 35 de MAE.",
        "En los ocho festivos se separan. SARIMA y ETS se equivocan en 72 y 69, casi tanto como la barra, y sobrestiman en 56 y 59: no ven el calendario.",
        "Los árboles bajan ese error a 37 y 43, aunque se pasan al otro lado y subestiman. La regresión queda en medio.",
      ],
      enfatizar: ["Con solo ocho festivos la magnitud es imprecisa, pero el signo es claro y coincide con la estructura de cada modelo."],
      transicion: "¿En qué se apoyan los modelos para pronosticar?",
    },
  },
  {
    id: "interpretacion",
    seccion: "Interpretación",
    titulo: "Importancia por permutación",
    minutos: 2,
    expone: "Juan Diego",
    Contenido: Interpretacion,
    notas: {
      guion: [
        "Para los árboles medimos la importancia por permutación: se desordena un grupo de variables entre los días y se mide cuánto sube el MAE. Si no sube, el modelo no dependía de ese grupo.",
        "Tres hallazgos. Primero, el ciclo semanal es la señal principal, y cada modelo la toma por un camino distinto: el gradiente del día de la semana, el bosque de los rezagos de 7, 14 y 28 días.",
        "Segundo, el día anterior pesa tanto como el ciclo semanal. El análisis exploratorio no lo destacó, pero sí lo anticipaba que el ingenuo de un día ganara cuatro pliegues: recoge el nivel reciente de la serie.",
        "Tercero, los festivos pesan aunque sean solo 8 de 184 días.",
        "A la derecha comprobamos el sentido: al marcar un lunes laborable como festivo, el gradiente baja su pronóstico un 37,3 %, casi exactamente el 37,8 % del análisis exploratorio.",
      ],
      enfatizar: [
        "Importancia no es causa: que el modelo use el día anterior no significa que un día con muchos hurtos provoque otro.",
        "El indicador de 2020 da cero por construcción: en la evaluación vale cero en todos los días.",
      ],
      transicion: "Todo esto tiene límites que hay que decir con claridad.",
      preguntas: [
        {
          pregunta: "¿Por qué agrupar las variables al permutar?",
          respuesta: "Porque hay sustitutas: el rezago de 7 y el de 14 llevan casi la misma información. Si se permuta solo uno, el modelo usa el otro y ambos parecen poco importantes. Al permutar el grupo, el modelo ya no tiene a qué recurrir.",
        },
        {
          pregunta: "¿Qué pasa con el día del mes?",
          respuesta: "En el gradiente, permutar solo el día del mes sube el MAE un 8,6 %, y el análisis exploratorio no lo estudió. Como varía mucho entre pliegues, puede ser un artefacto de fechas concretas del entrenamiento. No lo interpretamos sin un análisis específico; está en trabajo futuro.",
        },
      ],
    },
  },
];
