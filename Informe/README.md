# Informe — Analítica de Datos

**Proyecto:** Análisis multifuente y predicción del hurto a personas en Bogotá D. C., 2020–2025, mediante técnicas de minería de datos y aprendizaje automático.

**Autores:** Juan Diego Rojas y Sara Albarracín. **Profesor:** Ferney Maldonado López.

## Informe en curso (desde la segunda entrega)

El informe se compila desde [informe.tex](informe.tex), que incluye un archivo por sección (#39):

| Archivo | Contenido | Responsable |
|---|---|---|
| `preambulo.tex`, `portada.tex` | Paquetes, formato y portada. La entrega se cambia en `\entregaactual` y `\entregasubtitulo`, dentro de `informe.tex` | Ambos |
| `secciones/02_introduccion.tex` | Sección 2 | Juan Diego |
| `secciones/03_trabajos_relacionados.tex` | Sección 3 | Juan Diego |
| `secciones/04_datos.tex` | Sección 4 | Juan Diego |
| `secciones/05_preprocesamiento.tex`, `06_analisis_exploratorio.tex`, `07_metodologia.tex` | Secciones 5–7. Se activan quitando el `%` de su `\input` en `informe.tex` | Sara |
| `referencias.tex` | Referencias en APA 7 | Ambos |
| `secciones/apendices.tex` | Apéndices A–D: diccionario de datos, archivos y SHA-256, reproducibilidad y tablas complementarias (#51) | Juan Diego |

Se compila en Overleaf con pdfLaTeX. Hay que subir todos estos archivos con sus carpetas, incluida [`figuras/`](figuras/). Si falta una figura, el informe compila igual y muestra un recuadro «Figura pendiente».

## Primera entrega

Archivo: [primera_entrega.tex](primera_entrega.tex). Es la versión entregada, en la etiqueta `entrega-1`, y no se edita. Contiene las secciones 2 (Introducción), 3 (Trabajos relacionados) y 4 (Recolección y entendimiento de datos). Las secciones 2–4 de `informe.tex` parten de ella.

## Fuentes y función de cada una

Las decisiones están en [`docs/decisiones.md`](../docs/decisiones.md), D-01.

| Fuente | Función | Filas de hurto en Bogotá |
|---|---|---:|
| [Policía Nacional — delitos a nivel de registro](https://www.policia.gov.co/estadistica-delictiva) | Principal: requisito de 500.000 y variable objetivo | 741.986 (2020–2025) |
| [Fiscalía — Procesos Fiscalía V3](https://www.datos.gov.co/d/dbdv-iihs) | Complementaria; hurto en todas sus modalidades | 1.300.703 (2018–2025) |
| [Línea 123 — llamadas tramitadas](https://datosabiertos.bogota.gov.co/dataset/incidentes) | Complementaria; demanda ciudadana y localidad | 25.144 filas, 1.094.313 llamadas (2018–2025) |

Las filas de fuentes distintas no se suman.

## De dónde sale cada cifra y figura de la sección 4

| Salida | Script |
|---|---|
| `outputs/auditoria/`, `outputs/auditoria_policia/` | `scripts/auditoria_datasets.py` ([docs/AUDITORIA.md](../docs/AUDITORIA.md)) |
| `outputs/serie_objetivo/` y `figuras/serie_diaria_policia.pdf` | `scripts/serie_objetivo_policia.py` |
| `outputs/informe/fiscalia_*.csv` | `scripts/fiscalia_modalidades.py` |
| `outputs/informe/series_mensuales_fuentes.csv`, `linea123_localidad_2020_2025.csv` y sus figuras | `scripts/figuras_informe.py` |

Las figuras de `figuras/` son copias de las de `outputs/`. Si se regeneran, hay que volver a copiarlas.

```bash
python scripts/policia_registro_a_csv.py --entrada data/raw/policia_registro --salida data/raw/policia_registro/csv
python scripts/serie_objetivo_policia.py
python scripts/fiscalia_modalidades.py
python scripts/figuras_informe.py
cp outputs/serie_objetivo/figuras/serie_diaria_policia.pdf outputs/informe/figuras/series_mensuales_fuentes.pdf outputs/informe/figuras/linea123_localidad.pdf Informe/figuras/
```
