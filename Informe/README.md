# Informe — Analítica de Datos

**Proyecto:** Análisis multifuente y predicción del hurto a personas en Bogotá D. C. mediante técnicas de minería de datos y aprendizaje automático.

**Autores:** Juan Diego Rojas y Sara Albarracín. **Profesor:** Ferney Maldonado López.

## Primera entrega

Archivo: [primera_entrega.tex](primera_entrega.tex). Secciones 2 (Introducción), 3 (Trabajos relacionados) y 4 (Recolección y entendimiento de datos). Es autocontenido y puede compilarse en Overleaf con pdfLaTeX. La sección 1 y las secciones 5–11 corresponden a entregas posteriores.

## Fuentes acordadas

1. [Línea 123 — incidentes tramitados](https://datosabiertos.bogota.gov.co/dataset/incidentes).
2. [Policía Nacional — hurto a personas, archivos anuales](https://www.policia.gov.co/delitos-de-impacto/hurto-personas).
3. [Fiscalía — Procesos Fiscalía V3](https://www.datos.gov.co/d/dbdv-iihs).

## Evidencia pendiente para el requisito de al menos 500.000 registros

No sumar filas de datasets institucionales distintos para alcanzar el mínimo. Para cada fuente registrar en un archivo de auditoría:

- URL exacta, nombre del archivo, fecha de descarga, tamaño y SHA-256.
- Filas del archivo completo, filas de Bogotá (código DANE 11001), filas 2018–2025 y filas de categorías pertinentes a hurto.
- Número de registros únicos de acuerdo con la unidad de observación, valores nulos, duplicados, y criterio de filtrado de delitos.
- En Línea 123 diferenciar **número de filas** de suma de **CANT_INCIDENTES**. En Fiscalía distinguir fila, proceso anonimizado y tipo de delito. En Policía verificar si cada fila corresponde a un registro, un hecho o un conteo agregado.
- Dejar el conjunto que cumple el umbral de manera independiente claramente identificado; si la fuente supera 500.000 filas solo incluyendo categorías ajenas al hurto, consultar al profesor si ese universo es válido.

Los volúmenes preliminares compartidos por el equipo (Línea 123: 763.074 filas de todos los incidentes para 2018–2025; 25.144 filas con categorías que contienen «hurto»; Policía 2025: 123.364 filas Bogotá) **no se presentan como cifras finales auditadas**.

## Coordinación

Sara: cuando tengas listo el trabajo de segunda entrega en local, publícalo en una rama propia o avisa antes de integrarlo a `main`; comparte los CSV/diccionarios filtrados y el resumen de conteos verificables para actualizar la sección 4.

Juan Diego: actualizar `Informe/primera_entrega.tex` con las cifras definitivas, metodología de extracción y cualquier ajuste de objetivos que surja de la auditoría, preservando el trabajo de la segunda entrega.
