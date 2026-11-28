# Presentación de la sustentación final

Presentación de la tercera entrega (#56), hecha en React. Tiene 27 diapositivas de 1920 × 1080 (16:9), notas del expositor y exportación a PDF. Vive en su propia carpeta y no cambia nada del proyecto: solo **lee** `outputs/` y una figura del informe.

- **PDF para el profesor:** [`entregables/Presentacion_Proyecto.pdf`](entregables/Presentacion_Proyecto.pdf)
- **Guía de sustentación**, con guion, tiempos, conceptos y preguntas difíciles: [`GUIA_SUSTENTACION.md`](GUIA_SUSTENTACION.md)

## Comandos

Requiere Node 20 o posterior. El paso de datos usa Python con pandas, el mismo entorno del proyecto.

```bash
cd presentacion
npm install            # dependencias
npm run dev            # presentación en http://localhost:5173
npm run build          # comprueba tipos y compila a dist/
npm run export:pdf     # compila y genera entregables/Presentacion_Proyecto.pdf
npm run verificar      # prueba navegación, notas, índice y vista de impresión (tras build)
npm run datos          # vuelve a extraer las cifras de outputs/ (solo si cambian)
npm run guia           # regenera el guion y los tiempos de GUIA_SUSTENTACION.md
```

La exportación usa Playwright 1.48.2, fijado a esa versión, con su Chromium. Si falta el navegador, se instala con `npx playwright install chromium`.

## Uso durante la exposición

| Tecla | Acción |
|---|---|
| → · ↓ · Espacio · AvPág | Siguiente |
| ← · ↑ · RePág | Anterior |
| Inicio · Fin | Primera · última |
| F | Pantalla completa |
| N | Mostrar u ocultar las notas del expositor |
| O | Índice de diapositivas (Esc lo cierra) |

La barra inferior repite estas acciones y tiene el botón **PDF**, que abre la vista de impresión y el diálogo de impresión del navegador. Un clic sobre la diapositiva avanza. La URL guarda la diapositiva actual (`#/17`), así que al recargar no se pierde la posición.

Las notas solo existen en pantalla: no aparecen en la diapositiva, en la vista de impresión ni en el PDF.

## De dónde salen las cifras

Ninguna cifra de las gráficas se escribe a mano.

1. `scripts/preparar_datos.py` lee archivos versionados de `outputs/` (serie, auditoría, EDA, comparación, predicciones e interpretación) y escribe `src/data/generado/*.json`.
2. `src/data/datos.ts` los tipa. Las diapositivas los importan.
3. Cada gráfica indica al pie el archivo de origen.

Como comprobación, el MAE recalculado desde las predicciones de los 184 días coincide con la tabla del informe: 32,72; 32,94; 33,57; 34,22; 36,31; y 49,04 para la barra. El 32,94 es el 32,95 del informe, redondeado desde predicciones con un decimal.

El texto de las diapositivas resume el informe, sección por sección. El mapa de la diapositiva 10 es la figura `Informe/figuras/eda_mapa_tasa.pdf`, convertida a PNG.

## Estructura

```text
presentacion/
├── src/
│   ├── slides/         Diapositivas por bloque (s01_apertura … s06_cierre), cada una con sus notas
│   ├── components/     Presentador, vista de impresión, índice, panel de notas, piezas, fórmula (KaTeX)
│   │   └── diagramas/  Diagramas en SVG: fuentes, pliegues, fuga de información, flujo del proyecto
│   ├── layouts/        Marco común: sección, título, mensaje y pie numerado
│   ├── hooks/          Escala del lienzo, teclado, modo impresión, posición
│   ├── data/           datos.ts, colores fijos por modelo, formato es-CO y generado/*.json
│   └── styles/         Tailwind, fuentes locales y reglas de impresión
├── public/assets/      Mapa de tasas por localidad
├── scripts/            preparar_datos.py, export-pdf.ts, verificar-navegacion.ts, generar-guia.ts
├── entregables/        PDF y capturas de la verificación
├── GUIA_SUSTENTACION.md
└── README.md
```

## Decisiones técnicas

- **React + TypeScript + Vite + Tailwind.** Cada diapositiva es un componente con sus notas tipadas (`src/slides/tipos.ts`).
- **Lienzo fijo de 1920 × 1080 escalado.** Se diseña a una sola resolución y se escala con `transform`. En cualquier ventana la diapositiva se ve igual, sin recortes, y es idéntica a la página del PDF.
- **Recharts** para las gráficas de datos. Los **diagramas** (pliegues, fuga, flujo) son SVG propios en vez de Mermaid, para controlar la disposición y la tipografía y que el PDF sea idéntico a la pantalla.
- **KaTeX** renderiza las fórmulas en el propio HTML.
- **Fuentes locales** (`@fontsource`: Source Serif 4, Inter, JetBrains Mono), para que el PDF no dependa de la red.
- **Framer Motion** solo para entradas discretas. En la vista de impresión todo se dibuja en su estado final, sin animaciones.
- **Exportación con Playwright.** `scripts/export-pdf.ts`:
  - espera a que fuentes, imágenes y gráficas estén listas;
  - comprueba que ningún elemento se salga de su diapositiva;
  - imprime una diapositiva por página;
  - verifica que el PDF tenga tantas páginas como diapositivas.

## Validaciones realizadas

Todas en Windows 11, con Node 24 y Chromium 130 (Playwright 1.48.2):

- `npm run build`: sin errores de TypeScript. Vite avisa del tamaño del paquete (1,1 MB, 340 kB comprimido); no afecta a una presentación local.
- `npm run export:pdf`: 27 páginas de 1920 × 1080 px y ningún elemento fuera de su diapositiva. Revisé visualmente cada página del PDF.
- `npm run verificar`: 23 comprobaciones, entre ellas:
  - teclas y botones de navegación;
  - límites en la primera y la última diapositiva;
  - posición guardada en la URL;
  - notas e índice;
  - vista de impresión sin controles ni notas;
  - escalado en 1024 × 640 con proporción 16:9;
  - ninguna página con errores de JavaScript.
- Las cifras de las gráficas se cotejaron con las tablas del informe.

## Pendiente

- Confirmar con el profesor la duración y si la presentación se exige. #56 depende de esa confirmación.
- La duración sugerida es de unos 36 minutos y no está ensayada. La guía propone una versión de unos 20. El criterio de cierre de #56 es un ensayo con los tiempos medidos.
- El reparto entre Juan Diego y Sara es una propuesta por áreas de responsabilidad; está en el campo `expone` de cada diapositiva.
