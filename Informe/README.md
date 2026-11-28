# Informe — Analítica de Datos

**Proyecto:** Análisis multifuente y predicción del hurto a personas en Bogotá D. C., 2020–2025, mediante técnicas de minería de datos y aprendizaje automático.

**Autores:** Juan Diego Rojas y Sara Albarracín. **Profesor:** Ferney Maldonado López.

## Cómo se compila

El informe se compila desde [informe.tex](informe.tex), que incluye un archivo por sección:

| Archivo | Contenido | Responsable |
|---|---|---|
| `preambulo.tex`, `portada.tex` | Paquetes, formato y portada. La entrega se cambia en `\entregaactual` y `\entregasubtitulo`, dentro de `informe.tex` | Ambos |
| `secciones/01_resumen.tex` | Sección 1, resumen ejecutivo | Juan Diego |
| `secciones/02_introduccion.tex`, `03_trabajos_relacionados.tex`, `04_datos.tex` | Secciones 2 a 4 | Juan Diego |
| `secciones/05_preprocesamiento.tex`, `06_analisis_exploratorio.tex`, `07_metodologia.tex` | Secciones 5 a 7. Parten de `scripts/preprocesamiento.py`, [`docs/EDA_HALLAZGOS.md`](../docs/EDA_HALLAZGOS.md) y [`docs/METODOLOGIA.md`](../docs/METODOLOGIA.md) | Sara (contenido) y Juan Diego (integración) |
| `secciones/08_implementacion.tex` | Sección 8, implementación del modelado. Parte de [`docs/MODELADO.md`](../docs/MODELADO.md) | Juan Diego |
| `secciones/09_resultados.tex`, `10_interpretacion.tex`, `11_conclusiones.tex` | Secciones 9 a 11: resultados, interpretación, y conclusiones con las limitaciones | Juan Diego |
| `referencias.tex` | Referencias en APA 7 | Ambos |
| `secciones/apendices.tex` | Apéndices A–D: diccionario de datos, archivos y SHA-256, reproducibilidad y tablas complementarias | Juan Diego |

Se compila con pdfLaTeX (`latexmk -pdf`), en Overleaf o en local. Hay que subir todos estos archivos con sus carpetas, incluida [`figuras/`](figuras/). Si falta una figura, el informe compila igual y muestra un recuadro «Figura pendiente».

La versión de la primera entrega está en la etiqueta `entrega-1` del repositorio y no se edita aquí.

## Fuentes y función de cada una

Las decisiones están en [`docs/decisiones.md`](../docs/decisiones.md), D-01.

| Fuente | Función | Filas de hurto en Bogotá |
|---|---|---:|
| [Policía Nacional — delitos a nivel de registro](https://www.policia.gov.co/estadistica-delictiva) | Principal: requisito de 500.000 y variable objetivo | 741.986 (2020–2025) |
| [Fiscalía — Procesos Fiscalía V3](https://www.datos.gov.co/d/dbdv-iihs) | Complementaria; hurto en todas sus modalidades | 1.300.703 (2018–2025) |
| [Línea 123 — llamadas tramitadas](https://datosabiertos.bogota.gov.co/dataset/incidentes) | Complementaria; demanda ciudadana y localidad | 25.144 filas, 1.094.313 llamadas (2018–2025) |

Las filas de fuentes distintas no se suman.

## De dónde sale cada cifra y figura de las secciones 4 a 11

| Salida | Script |
|---|---|
| `outputs/auditoria/`, `outputs/auditoria_policia/` | `scripts/auditoria_datasets.py` ([docs/AUDITORIA.md](../docs/AUDITORIA.md)) |
| `outputs/serie_objetivo/` y `figuras/serie_diaria_policia.pdf` | `scripts/serie_objetivo_policia.py` |
| `outputs/informe/fiscalia_*.csv` | `scripts/fiscalia_modalidades.py` |
| `outputs/informe/series_mensuales_fuentes.csv`, `linea123_localidad_2020_2025.csv` y sus figuras | `scripts/figuras_informe.py` |
| `outputs/poblacion/` (población por localidad y año, denominador de las tasas) | `scripts/poblacion_localidad.py` |
| `outputs/preprocesamiento/` (tablas de pasos y de validación de la sección 5) | `scripts/preprocesamiento.py` |
| `outputs/features/diccionario_features.json` (variables derivadas y apéndice A) | `scripts/features.py` |
| `outputs/eda/` y las figuras `eda_*.pdf` (sección 6) | `scripts/eda.py` |
| `outputs/baselines/` (comparadores y pliegues de la sección 7) | `scripts/baselines.py` |
| `outputs/modelado/` (métricas, predicciones y coeficientes de cada modelo) | `scripts/modelado/` (`estadisticos.py`, `arboles.py`, `ajuste.py`, `regresion.py`) |
| `outputs/modelado/comparacion/` y las figuras `modelos_*.pdf` (sección 9) | `scripts/modelado/comparacion.py` |
| `outputs/modelado/interpretacion/` y `importancia_permutacion_grupos.pdf` (sección 10) | `scripts/modelado/interpretacion.py` |

Las figuras de `figuras/` son copias de las de `outputs/`. Si se regeneran, hay que volver a copiarlas. Los scripts de la sección 9 y 10 las copian solos. Las cifras de modelado se generan en la imagen de Docker de referencia ([`docs/REPRODUCIBILIDAD.md`](../docs/REPRODUCIBILIDAD.md), sección 6).

```bash
python scripts/policia_registro_a_csv.py --entrada data/raw/policia_registro --salida data/raw/policia_registro/csv
python scripts/serie_objetivo_policia.py
python scripts/fiscalia_modalidades.py
python scripts/figuras_informe.py
python scripts/preprocesamiento.py
python scripts/features.py
python scripts/eda.py
python scripts/baselines.py
cp outputs/serie_objetivo/figuras/serie_diaria_policia.pdf outputs/informe/figuras/series_mensuales_fuentes.pdf outputs/informe/figuras/linea123_localidad.pdf Informe/figuras/
cp outputs/eda/figuras/eda_dia_semana.pdf outputs/eda/figuras/eda_estacionalidad_mensual.pdf outputs/eda/figuras/eda_localidad_tasa.pdf outputs/eda/figuras/eda_mapa_tasa.pdf outputs/eda/figuras/eda_fuentes_normalizadas.pdf Informe/figuras/
```
