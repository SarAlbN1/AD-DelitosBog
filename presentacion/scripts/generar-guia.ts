/**
 * Rellena en GUIA_SUSTENTACION.md el guion y los tiempos a partir de las notas de cada diapositiva
 * (src/slides/*.tsx), entre los marcadores <!-- guion:inicio --> y <!-- guion:fin -->.
 * Así el guion de la guía y el del panel de notas son el mismo texto.
 *
 * Uso: `npm run guia`
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { DIAPOSITIVAS } from "../src/slides";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const GUIA = resolve(RAIZ, "GUIA_SUSTENTACION.md");

const mmss = (min: number) => {
  const s = Math.round(min * 60);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

let acumulado = 0;
const filas = DIAPOSITIVAS.map((d, i) => {
  const inicio = acumulado;
  acumulado += d.minutos;
  return `| ${i + 1} | ${d.seccion} · ${d.titulo} | ${d.expone} | ${mmss(d.minutos)} | ${mmss(inicio)} |`;
});

const partes: string[] = [];
partes.push("### Tiempos por diapositiva\n");
partes.push(`Duración total sugerida: **${mmss(acumulado)} min**, sin contar las preguntas.\n`);
partes.push("| # | Diapositiva | Expone | Duración | Empieza en |\n|---|---|---|---|---|");
partes.push(filas.join("\n"));
partes.push("\n### Guion por diapositiva\n");
DIAPOSITIVAS.forEach((d, i) => {
  partes.push(`#### ${i + 1}. ${d.titulo} · ${d.expone} · ${mmss(d.minutos)}\n`);
  partes.push(d.notas.guion.map((p) => `${p}`).join("\n\n"));
  partes.push(`\n**Enfatizar:**\n\n${d.notas.enfatizar.map((e) => `- ${e}`).join("\n")}`);
  partes.push(`\n**Transición:** _${d.notas.transicion}_\n`);
});

const texto = readFileSync(GUIA, "utf-8");
const [antes, resto] = texto.split("<!-- guion:inicio -->");
const [, despues] = resto.split("<!-- guion:fin -->");
writeFileSync(GUIA, `${antes}<!-- guion:inicio -->\n\n${partes.join("\n")}\n<!-- guion:fin -->${despues}`, "utf-8");
console.log(`Guion de ${DIAPOSITIVAS.length} diapositivas escrito en ${GUIA} (${mmss(acumulado)} min).`);
