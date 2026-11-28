/**
 * Comprueba el modo presentación en Chromium: atajos de teclado, botones, notas, índice y que las notas
 * no aparezcan en la vista de impresión. Deja capturas en `entregables/capturas/`.
 *
 * Uso: `npm run verificar` (sirve `dist/`; compile antes con `npm run build`).
 */
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, type Page } from "playwright";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const URL_BASE = "http://localhost:4173/";
const CAPTURAS = resolve(RAIZ, "entregables", "capturas");

const contador = async (p: Page) => (await p.locator("nav span.tabular").innerText()).trim();

function comprobar(condicion: boolean, mensaje: string): void {
  if (!condicion) throw new Error(`FALLA: ${mensaje}`);
  console.log(`ok · ${mensaje}`);
}

async function main(): Promise<void> {
  const vite = resolve(RAIZ, "node_modules", "vite", "bin", "vite.js");
  const servidor = spawn(process.execPath, [vite, "preview", "--port", "4173", "--strictPort"], { cwd: RAIZ, stdio: "ignore" });
  try {
    for (let i = 0; i < 60; i++) {
      try {
        if ((await fetch(URL_BASE)).ok) break;
      } catch {
        await new Promise((ok) => setTimeout(ok, 250));
      }
    }
    mkdirSync(CAPTURAS, { recursive: true });
    const navegador = await chromium.launch();
    const p = await navegador.newPage({ viewport: { width: 1600, height: 900 } });
    const errores: string[] = [];
    p.on("pageerror", (e) => errores.push(e.message));
    await p.goto(URL_BASE, { waitUntil: "networkidle" });

    const total = Number((await contador(p)).split("/")[1]);
    comprobar((await contador(p)) === `1 / ${total}`, `arranca en la diapositiva 1 de ${total}`);

    await p.keyboard.press("ArrowRight");
    await p.keyboard.press("ArrowRight");
    comprobar((await contador(p)) === `3 / ${total}`, "→ avanza");
    await p.keyboard.press("ArrowLeft");
    comprobar((await contador(p)) === `2 / ${total}`, "← retrocede");
    await p.keyboard.press("End");
    comprobar((await contador(p)) === `${total} / ${total}`, "Fin va a la última");
    await p.keyboard.press("ArrowRight");
    comprobar((await contador(p)) === `${total} / ${total}`, "no pasa de la última");
    await p.keyboard.press("Home");
    comprobar((await contador(p)) === `1 / ${total}`, "Inicio va a la primera");
    await p.keyboard.press(" ");
    comprobar((await contador(p)) === `2 / ${total}`, "Espacio avanza");
    comprobar(p.url().endsWith("#/2"), "la URL guarda la diapositiva (#/2)");

    await p.getByRole("button", { name: "Siguiente (→)" }).click();
    comprobar((await contador(p)) === `3 / ${total}`, "botón Siguiente");
    await p.getByRole("button", { name: "Última diapositiva (Fin)" }).click();
    comprobar((await contador(p)) === `${total} / ${total}`, "botón Última");
    await p.getByRole("button", { name: "Primera diapositiva (Inicio)" }).click();
    comprobar((await contador(p)) === `1 / ${total}`, "botón Primera");

    await p.goto(`${URL_BASE}#/10`, { waitUntil: "networkidle" });
    await p.reload({ waitUntil: "networkidle" });
    comprobar((await contador(p)) === `10 / ${total}`, "al recargar con #/10 abre la diapositiva 10");
    await p.waitForTimeout(1200);
    await p.screenshot({ path: resolve(CAPTURAS, "modo-presentacion.png") });

    await p.keyboard.press("n");
    comprobar(await p.getByText("Preguntas probables").isVisible(), "N abre las notas del expositor");
    await p.waitForTimeout(500);
    await p.screenshot({ path: resolve(CAPTURAS, "notas-expositor.png") });
    await p.keyboard.press("n");
    comprobar(!(await p.getByText("Preguntas probables").isVisible()), "N cierra las notas");

    await p.keyboard.press("o");
    comprobar(await p.getByText("Índice de diapositivas").isVisible(), "O abre el índice");
    await p.waitForTimeout(400);
    await p.screenshot({ path: resolve(CAPTURAS, "indice.png") });
    await p.keyboard.press("ArrowRight");
    comprobar((await contador(p)) === `10 / ${total}`, "con el índice abierto, las flechas no navegan");
    await p.locator("button", { hasText: "Diebold-Mariano entre modelos" }).click();
    comprobar((await contador(p)) === `12 / ${total}`, "clic en una miniatura va a esa diapositiva y cierra el índice");

    // La vista de impresión no lleva controles ni notas.
    const imp = await navegador.newPage({ viewport: { width: 1920, height: 1080 } });
    await imp.goto(`${URL_BASE}?modo=impresion`, { waitUntil: "networkidle" });
    await imp.waitForFunction(() => window.__PRESENTACION_LISTA__ === true);
    comprobar((await imp.locator("section.pagina-impresa").count()) === total, `la vista de impresión tiene ${total} páginas`);
    comprobar((await imp.locator("nav").count()) === 0, "la vista de impresión no tiene controles");
    comprobar((await imp.getByText("Preguntas probables").count()) === 0, "la vista de impresión no tiene notas");

    // Ventana pequeña: el lienzo se escala sin recortes.
    await p.setViewportSize({ width: 1024, height: 640 });
    await p.waitForTimeout(400);
    const caja = await p.locator(".lienzo").first().boundingBox();
    comprobar(caja !== null && caja.width <= 1024 && caja.height <= 640 - 48, "en 1024 × 640 el lienzo cabe entero");
    comprobar(caja !== null && Math.abs(caja.width / caja.height - 16 / 9) < 0.01, "se conserva la proporción 16:9");

    comprobar(errores.length === 0, "sin errores de JavaScript");
    await navegador.close();
    console.log(`\nCapturas en ${CAPTURAS}`);
  } finally {
    servidor.kill();
  }
}

main().catch((e: unknown) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
