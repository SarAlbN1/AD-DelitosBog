/**
 * Exporta la presentación a PDF: una diapositiva por página, 1920 × 1080 px (16:9), sin controles ni notas.
 *
 * 1. Sirve la compilación de `dist/` con `vite preview`.
 * 2. Abre `?modo=impresion` en Chromium (Playwright) y espera a que fuentes, imágenes y gráficas estén listas.
 * 3. Comprueba que ninguna diapositiva desborde su lienzo y que haya una sección por diapositiva.
 * 4. Imprime a `entregables/Presentacion_Proyecto.pdf` y verifica el número de páginas.
 *
 * Uso: `npm run export:pdf` (compila antes).
 */
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PUERTO = 4173;
const URL_BASE = `http://localhost:${PUERTO}/`;
const SALIDA = resolve(RAIZ, "entregables", "Presentacion_Proyecto.pdf");

async function esperarServidor(url: string, intentos = 60): Promise<void> {
  for (let i = 0; i < intentos; i++) {
    try {
      const r = await fetch(url);
      if (r.ok) return;
    } catch {
      /* todavía arrancando */
    }
    await new Promise((ok) => setTimeout(ok, 250));
  }
  throw new Error(`El servidor no respondió en ${url}`);
}

function servir(): ChildProcess {
  if (!existsSync(resolve(RAIZ, "dist", "index.html"))) {
    throw new Error("No existe dist/. Ejecute `npm run build` o use `npm run export:pdf`.");
  }
  const vite = resolve(RAIZ, "node_modules", "vite", "bin", "vite.js");
  return spawn(process.execPath, [vite, "preview", "--port", String(PUERTO), "--strictPort"], {
    cwd: RAIZ,
    stdio: "ignore",
  });
}

/** Cuenta las páginas de un PDF por sus objetos /Type /Page (suficiente para un PDF de Chromium). */
function contarPaginas(ruta: string): number {
  const texto = readFileSync(ruta).toString("latin1");
  return (texto.match(/\/Type\s*\/Page(?!s)/g) ?? []).length;
}

async function main(): Promise<void> {
  const servidor = servir();
  try {
    await esperarServidor(URL_BASE);
    const navegador = await chromium.launch();
    const pagina = await navegador.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
    const errores: string[] = [];
    pagina.on("pageerror", (e) => errores.push(e.message));
    pagina.on("console", (m) => m.type() === "error" && errores.push(m.text()));

    await pagina.goto(`${URL_BASE}?modo=impresion`, { waitUntil: "networkidle" });
    await pagina.waitForFunction(() => window.__PRESENTACION_LISTA__ === true, undefined, { timeout: 60_000 });
    await pagina.emulateMedia({ media: "print" });

    const revision = await pagina.evaluate(() => {
      const secciones = Array.from(document.querySelectorAll<HTMLElement>("section.pagina-impresa"));
      const desbordes: string[] = [];
      secciones.forEach((s, i) => {
        const caja = s.getBoundingClientRect();
        s.querySelectorAll<HTMLElement>("*").forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) return;
          // KaTeX dibuja llaves y raíces con SVG de 400em que su contenedor recorta: no es un desborde visible.
          if (el.closest(".katex")) return;
          if (r.right > caja.right + 1 || r.bottom > caja.bottom + 1 || r.left < caja.left - 1) {
            desbordes.push(`diapositiva ${i + 1}: <${el.tagName.toLowerCase()} class="${el.getAttribute("class") ?? ""}">`);
          }
        });
        // Contenido que el propio lienzo recorta.
        const lienzo = s.querySelector<HTMLElement>(".lienzo");
        if (lienzo && (lienzo.scrollHeight > lienzo.clientHeight + 1 || lienzo.scrollWidth > lienzo.clientWidth + 1)) {
          desbordes.push(`diapositiva ${i + 1}: el lienzo recorta contenido (${lienzo.scrollWidth}×${lienzo.scrollHeight})`);
        }
      });
      return { total: secciones.length, desbordes };
    });

    if (revision.desbordes.length > 0) {
      console.error("Elementos fuera del lienzo:\n" + revision.desbordes.slice(0, 40).join("\n"));
      throw new Error(`${revision.desbordes.length} elementos desbordan su diapositiva`);
    }
    if (errores.length > 0) throw new Error("Errores en la página:\n" + errores.join("\n"));

    mkdirSync(dirname(SALIDA), { recursive: true });
    await pagina.pdf({
      path: SALIDA,
      width: "1920px",
      height: "1080px",
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    });
    await navegador.close();

    const paginas = contarPaginas(SALIDA);
    if (paginas !== revision.total) {
      throw new Error(`El PDF tiene ${paginas} páginas y la presentación ${revision.total} diapositivas`);
    }
    const kb = Math.round(statSync(SALIDA).size / 1024);
    console.log(`PDF generado: ${SALIDA}\n${paginas} páginas de 1920 × 1080 px · ${kb} KB · sin desbordes`);
  } finally {
    servidor.kill();
  }
}

main().catch((e: unknown) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
