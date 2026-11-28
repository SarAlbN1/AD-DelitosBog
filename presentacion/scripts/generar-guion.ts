/**
 * Genera el guion de la exposición a partir de las notas de cada diapositiva (src/slides/*.tsx):
 *
 * - `GUION.md`, para leerlo en GitHub o en el editor;
 * - `entregables/Guion_presentacion.pdf`, para imprimirlo o tenerlo en otro dispositivo.
 *
 * El texto hablado y las acotaciones son los mismos del panel de notas (tecla N). Los tiempos se
 * calculan por palabras (src/slides/duracion.ts), así que cambian solos si cambia el guion.
 *
 * Uso: `npm run guion`
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { DIAPOSITIVAS } from "../src/slides";
import { BLOQUES, type Bloque } from "../src/slides/bloques";
import { esAccion, minutos, PALABRAS_POR_MINUTO } from "../src/slides/duracion";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MD = resolve(RAIZ, "GUION.md");
const PDF = resolve(RAIZ, "entregables", "Guion_presentacion.pdf");

const fmt = (m: number) => `${m.toLocaleString("es-CO", { maximumFractionDigits: 2 })} min`;
const diapos = (b: Bloque) => DIAPOSITIVAS.slice(b.desde - 1, b.hasta);
const duracionBloque = (b: Bloque) => diapos(b).reduce((s, d) => s + minutos(d), 0);
/** Quién habla en un bloque, en orden de aparición: «Juan Diego → Sara → Ambos». */
const quienes = (b: Bloque) => [...new Set(diapos(b).map((d) => d.expone))].join(" → ");
const total = BLOQUES.reduce((s, b) => s + duracionBloque(b), 0);

const REGLAS = [
  "**Se pronostica el registro de la Policía, no el hurto ocurrido.** Decirlo siempre así: el hurto que no se denuncia no está en la serie.",
  "**Solo cifras del informe.** Leer las de la diapositiva, no las de memoria. Si preguntan algo que no se midió, se dice que no se midió.",
  "**Nunca decir que un modelo «gana».** Los cuatro mejores no se distinguen entre sí; lo sólido es que los cinco superan la barra.",
  "**Importancia no es causa.** Decir «el modelo depende de», nunca «causa» o «provoca».",
  "**Las fuentes se comparan, no se suman.** Policía, Línea 123 y Fiscalía cuentan cosas distintas.",
];

const INSTALACION = [
  "cd presentacion",
  "npm install",
  "npm run build",
  "npm run preview      # abre la presentación en http://localhost:4173",
];

const ANTES = [
  "**Juan Diego:** abrir la presentación con `npm run preview` en Chrome o Edge, ir a http://localhost:4173 y pulsar **F** para pantalla completa.",
  "Tener abierto como respaldo el PDF `entregables/Presentacion_Proyecto.pdf`.",
  "**Si el proyector duplica la pantalla, no abrir las notas (N):** se verían proyectadas. Usar este guion impreso o en otro dispositivo.",
  "Probar en el equipo de la sala que → y el clic avanzan, y que los botones de la diapositiva 18 cambian el modelo.",
  "Zoom del navegador al 100 % (Ctrl + 0): la presentación se escala sola a la pantalla.",
  "Cada uno pasa sus propias diapositivas (→ o clic). Al cambiar de bloque se entrega el control con la frase de relevo.",
];

const CUIDADOS = [
  "**Mientras se señala algo, se sigue hablando.** Las acotaciones van entre corchetes y no se leen en voz alta.",
  "**Si falla el navegador:** abrir el PDF a pantalla completa y seguir con el mismo texto. En la diapositiva 18 el PDF muestra solo el gradiente: se salta el clic y se dice «en ETS, en cambio, el pronóstico no baja en los festivos».",
  "**Si se acaba el tiempo:** las diapositivas 15 y 16 (arquitectura y decisiones) se reducen a una frase cada una. No se recortan las de resultados (17 a 22) ni la de limitaciones (23).",
  "**Durante las preguntas:** tecla **O** para abrir el índice y saltar a la diapositiva que corresponda. Las respuestas preparadas están en `GUIA_SUSTENTACION.md`.",
];

/** Acotaciones de todas las diapositivas, para la tabla «Qué se hace en pantalla». */
/** Agrupa las líneas habladas seguidas en un solo bloque; las acotaciones quedan sueltas. */
function tramos(d: (typeof DIAPOSITIVAS)[number]): ({ accion: string } | { texto: string[] })[] {
  const salida: ({ accion: string } | { texto: string[] })[] = [];
  for (const l of [...d.notas.guion, d.notas.transicion]) {
    if (esAccion(l)) salida.push(l);
    else {
      const ultimo = salida[salida.length - 1];
      if (ultimo && "texto" in ultimo) ultimo.texto.push(l);
      else salida.push({ texto: [l] });
    }
  }
  return salida;
}

const acciones = DIAPOSITIVAS.flatMap((d, i) =>
  d.notas.guion.filter(esAccion).map((a) => ({ n: i + 1, d, accion: a.accion })),
);

function markdown(): string {
  const l: string[] = [];
  l.push("# Guion de la presentación · Hurto a personas en Bogotá, 2020–2025\n");
  l.push("- **Integrantes:** Juan Diego Rojas · Sara Albarracín");
  l.push(`- **Duración planeada:** ${fmt(total)}, sin las preguntas. El límite lo fija el profesor (por confirmar).`);
  l.push("- **Fuentes:** `Informe/informe.tex` (main), la presentación de `presentacion/` (#162) y `GUIA_SUSTENTACION.md`");
  l.push(`- **Cómo se calcula el tiempo:** ${PALABRAS_POR_MINUTO} palabras por minuto, más 5 s por diapositiva y 3 s por acotación. Se regenera con \`npm run guion\`.\n`);
  l.push("## Resumen de quién habla\n");
  l.push("| Bloque | Tema | Diapositivas | Quién | Tiempo |\n|---|---|---|---|---|");
  for (const b of BLOQUES) l.push(`| ${b.numero} | ${b.tema} | ${b.desde}–${b.hasta} | ${quienes(b)} | ${fmt(duracionBloque(b))} |`);
  l.push(`|  | **Total** |  |  | **${fmt(total)}** |\n`);
  l.push("## Reglas para todos\n");
  REGLAS.forEach((r) => l.push(`- ${r}`));
  l.push("\n---\n");
  l.push("## Parte 1 · Preparación (antes de exponer)\n");
  l.push("### 1.1 Instalación (una sola vez)\n");
  l.push("```bash\n" + INSTALACION.join("\n") + "\n```\n");
  l.push("### 1.2 Antes de empezar\n");
  ANTES.forEach((a, i) => l.push(`${i + 1}. ${a}`));
  l.push("\n### 1.3 Qué se hace en pantalla\n");
  l.push("| Diapositiva | Acción | Quién |\n|---|---|---|");
  acciones.forEach((a) => l.push(`| ${a.n} · ${a.d.titulo} | ${a.accion} | ${a.d.expone} |`));
  l.push("\n### 1.4 Cuidados durante la exposición\n");
  CUIDADOS.forEach((c) => l.push(`- ${c}`));
  l.push("\n---\n");
  l.push("## Parte 2 · Guion\n");
  for (const b of BLOQUES) {
    l.push(`### BLOQUE ${b.numero} · ${b.tema} · 🎤 ${quienes(b).toUpperCase()} · ${fmt(duracionBloque(b))}\n`);
    diapos(b).forEach((d, k) => {
      const n = b.desde + k;
      l.push(`#### ▶ Diapositiva ${n} · _${d.titulo}_ · ${fmt(minutos(d))}\n`);
      if (d.expone !== diapos(b)[k - 1]?.expone && quienes(b).includes("→")) l.push(`**🎤 ${d.expone.toUpperCase()}**\n`);
      for (const t of tramos(d)) {
        l.push("texto" in t ? t.texto.map((p) => `> ${p}`).join("\n>\n") + "\n" : `**[${t.accion}]**\n`);
      }
    });
    l.push("---\n");
  }
  l.push("## Parte 3 · Registro del ensayo\n");
  l.push("Lo llena quien no está hablando, con cronómetro. Criterio: el límite que fije el profesor.\n");
  l.push(`| Ensayo | ${BLOQUES.map((b) => `Bloque ${b.numero}`).join(" | ")} | Total |`);
  l.push(`|---|${BLOQUES.map(() => "---").join("|")}|---|`);
  l.push(`| Planeado | ${BLOQUES.map((b) => fmt(duracionBloque(b))).join(" | ")} | ${fmt(total)} |`);
  for (const e of [1, 2]) l.push(`| ${e} | ${BLOQUES.map(() => " ").join(" | ")} |   |`);
  l.push("\nNotas (qué se recortó y por qué):\n");
  return l.join("\n");
}

// ---------- HTML para el PDF ----------

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
/** Negritas y código del Markdown de las reglas y los cuidados. */
const inline = (s: string) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`(.+?)`/g, "<code>$1</code>");

function html(): string {
  const filasBloques = BLOQUES.map(
    (b) => `<tr><td>${b.numero}</td><td>${b.tema}</td><td>${b.desde}–${b.hasta}</td><td>${quienes(b)}</td><td>${fmt(duracionBloque(b))}</td></tr>`,
  ).join("");
  const guion = BLOQUES.map((b) => {
    const cuerpo = diapos(b)
      .map((d, k) => {
        const n = b.desde + k;
        const cambio = d.expone !== diapos(b)[k - 1]?.expone && quienes(b).includes("→");
        const lineas = tramos(d)
          .map((t) =>
            "texto" in t
              ? `<blockquote>${t.texto.map((p) => `<p>${esc(p)}</p>`).join("")}</blockquote>`
              : `<p class="accion">[${inline(t.accion)}]</p>`,
          )
          .join("");
        return `${cambio ? `<p class="turno">🎤 ${d.expone.toUpperCase()}</p>` : ""}<div class="diapo"><span>▶ Diapositiva ${n} · <i>${esc(d.titulo)}</i></span><span class="t">${fmt(minutos(d))}</span></div>${lineas}`;
      })
      .join("");
    return `<h3>BLOQUE ${b.numero} · ${b.tema} · 🎤 ${quienes(b).toUpperCase()} · ${fmt(duracionBloque(b))}</h3>${cuerpo}<hr/>`;
  }).join("");
  const acc = acciones.map((a) => `<tr><td>${a.n} · ${esc(a.d.titulo)}</td><td>${inline(a.accion)}</td><td>${a.d.expone}</td></tr>`).join("");
  return `<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
  @page { size: A4; margin: 18mm 17mm; }
  body { font-family: "Segoe UI", "Noto Sans", Arial, sans-serif; color: #1f2937; font-size: 10.5pt; line-height: 1.5; }
  h1 { color: #14325c; font-size: 20pt; line-height: 1.25; border-bottom: 3px solid #14325c; padding-bottom: 8px; margin: 0 0 12px; }
  h2 { color: #14325c; font-size: 15pt; border-bottom: 1.5px solid #c7d2e0; padding-bottom: 4px; margin-top: 22px; }
  h2.parte { border-bottom: 3px solid #14325c; break-before: page; font-size: 17pt; }
  h3 { color: #1d4f88; font-size: 12.5pt; border-bottom: 1px solid #c7d2e0; padding-bottom: 3px; margin-top: 20px; break-after: avoid; }
  h4 { color: #14325c; font-size: 11.5pt; margin: 14px 0 6px; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9.5pt; }
  th, td { border: 1px solid #c7d2e0; padding: 5px 7px; text-align: left; vertical-align: top; }
  th { background: #e8eef6; color: #14325c; }
  tr.total td { font-weight: 700; }
  code { background: #eef1f5; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
  pre { background: #eef1f5; padding: 10px 12px; border-radius: 4px; font-size: 9pt; }
  .diapo { background: #2a5c8f; color: #fff; font-weight: 700; padding: 6px 12px; border-radius: 4px; margin: 14px 0 8px; display: flex; justify-content: space-between; break-after: avoid; }
  .diapo .t { font-weight: 400; opacity: .85; }
  blockquote { margin: 0 0 6px; padding: 8px 12px; background: #f2f5f9; border-left: 4px solid #2a5c8f; }
  blockquote p { margin: 0 0 7px; break-inside: avoid; } blockquote p:last-child { margin-bottom: 0; }
  .accion { color: #8a4b08; font-weight: 700; margin: 6px 0; break-after: avoid; }
  .turno { color: #1d4f88; font-weight: 700; margin: 12px 0 0; }
  hr { border: none; border-top: 1px dashed #c7d2e0; margin: 18px 0; }
  ul, ol { padding-left: 20px; } li { margin: 3px 0; }
  .meta li { margin: 2px 0; }
  </style></head><body>
  <h1>Guion de la presentación · Hurto a personas en Bogotá, 2020–2025</h1>
  <ul class="meta">
    <li><b>Integrantes:</b> Juan Diego Rojas · Sara Albarracín</li>
    <li><b>Duración planeada:</b> ${fmt(total)}, sin las preguntas. El límite lo fija el profesor (por confirmar).</li>
    <li><b>Fuentes:</b> <code>Informe/informe.tex</code> (main), la presentación de <code>presentacion/</code> (#162) y <code>GUIA_SUSTENTACION.md</code></li>
    <li><b>Cómo se calcula el tiempo:</b> ${PALABRAS_POR_MINUTO} palabras por minuto, más 5 s por diapositiva y 3 s por acotación.</li>
  </ul>
  <h2>Resumen de quién habla</h2>
  <table><tr><th>Bloque</th><th>Tema</th><th>Diapositivas</th><th>Quién</th><th>Tiempo</th></tr>${filasBloques}
  <tr class="total"><td></td><td>Total</td><td></td><td></td><td>${fmt(total)}</td></tr></table>
  <h2>Reglas para todos</h2><ul>${REGLAS.map((r) => `<li>${inline(r)}</li>`).join("")}</ul>
  <h2 class="parte">Parte 1 · Preparación (antes de exponer)</h2>
  <h3>1.1 Instalación (una sola vez)</h3><pre>${INSTALACION.map(esc).join("\n")}</pre>
  <h3>1.2 Antes de empezar</h3><ol>${ANTES.map((a) => `<li>${inline(a)}</li>`).join("")}</ol>
  <h3>1.3 Qué se hace en pantalla</h3>
  <table><tr><th>Diapositiva</th><th>Acción</th><th>Quién</th></tr>${acc}</table>
  <h3>1.4 Cuidados durante la exposición</h3><ul>${CUIDADOS.map((c) => `<li>${inline(c)}</li>`).join("")}</ul>
  <h2 class="parte">Parte 2 · Guion</h2>${guion}
  <h2 class="parte">Parte 3 · Registro del ensayo</h2>
  <p>Lo llena quien no está hablando, con cronómetro. Criterio: el límite que fije el profesor.</p>
  <table><tr><th>Ensayo</th>${BLOQUES.map((b) => `<th>Bloque ${b.numero}</th>`).join("")}<th>Total</th></tr>
  <tr><td>Planeado</td>${BLOQUES.map((b) => `<td>${fmt(duracionBloque(b))}</td>`).join("")}<td>${fmt(total)}</td></tr>
  ${[1, 2].map((e) => `<tr><td>${e}</td>${BLOQUES.map(() => "<td>&nbsp;</td>").join("")}<td></td></tr>`).join("")}</table>
  <p>Notas (qué se recortó y por qué):</p>
  </body></html>`;
}

async function main(): Promise<void> {
  writeFileSync(MD, markdown(), "utf-8");
  mkdirSync(dirname(PDF), { recursive: true });
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  await pagina.setContent(html(), { waitUntil: "load" });
  await pagina.pdf({ path: PDF, format: "A4", printBackground: true, displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: '<div style="font-size:8pt;color:#6b7280;width:100%;text-align:center;font-family:Segoe UI,sans-serif"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    margin: { top: "16mm", bottom: "18mm", left: "17mm", right: "17mm" } });
  await navegador.close();
  const sinBloque = DIAPOSITIVAS.length - BLOQUES.reduce((s, b) => s + (b.hasta - b.desde + 1), 0);
  if (sinBloque !== 0) throw new Error(`Los bloques no cubren las ${DIAPOSITIVAS.length} diapositivas`);
  console.log(`Guion: ${DIAPOSITIVAS.length} diapositivas en ${BLOQUES.length} bloques, ${fmt(total)}.\n${MD}\n${PDF}`);
}

main().catch((e: unknown) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
