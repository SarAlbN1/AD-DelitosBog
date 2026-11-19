# Verificación de referencias (issue #24)

Fecha de consulta: **2026-11-11**. Cada referencia de `Informe/primera_entrega.tex` se comparó con su fuente primaria: un registro del repositorio institucional, el PDF del documento, Crossref (DOI) u Open Library (libros).

**Resultado:** las 8 referencias existen y son pertinentes; 7 de ellas son estudios académicos. Se corrigieron dos datos y queda una duda abierta.

| Clave | Referencia | Cómo se verificó | Título, autoría y año | ¿Coincide la descripción del informe? | Estado |
|---|---|---|---|---|---|
| `campo2017` | Campo Agredo (2017), trabajo de grado de pregrado, Universidad de los Andes | API DSpace del repositorio Uniandes (`dc.title`, `dc.contributor.author`, `dc.date.issued`, `dc.type`); handle `1992/50785` | Sí. El título oficial termina «…en **base** de datos» y no «…bases de datos» | Sí: el resumen trata la predicción del hurto a personas con algoritmos sobre bases de datos | ✅ Corregido (título y enlace persistente) |
| `fonseca2019` | Fonseca Vásquez (2019), Especialización en Geomática, UMNG | Portada del PDF (11 de junio de 2019) | Sí | Sí: análisis espacial en Los Mártires 2017–2018 para decisiones de los CAI | ✅ |
| `garzon2025` | Garzón Acosta (2025), Especialización en Estadística Aplicada, Fundación Universitaria Los Libertadores | PDF (artículo de 7 páginas, «Aceptado: mayo 08, 2025») | Sí | Sí: MCE frente a VECM, 2015–2024, ADF, causalidad de Granger, IPC, desempleo y capturas | ✅ |
| `martinez2025` | Martínez Chitiva (2025), Maestría en Tecnología de la Información Geográfica, Universidad de Manizales | Registro del repositorio RIDUM (handle `20.500.12746/7648`) | Sí. El tipo «tesis de maestría» se deduce de la colección; el registro no tiene un campo de tipo | Sí: modelo espacio-temporal; **Random Forest supera a la regresión de Poisson** (MAE 7,13 frente a 9,94; RMSE 16,62 frente a 21,10), con una partición 80/20 que no se describe como temporal; datos hasta 2020. No compara con otros métodos estadísticos, así que no se escribe «supera a los métodos estadísticos» | ✅ Precisado el 2026-11-16 (#38) |
| `riascos2020` | Riascos, Dulce, Moreno y Gómez (2020), *Prediciendo el crimen en Bogotá*, Nota de Política, Universidad de los Andes | PDF: autores, «Octubre 2020», ISSN 2027-7199 | Sí | Sí: despliegue policial, cámaras y ubicación de CAI; sesgo y subregistro | ✅ **Número 38 confirmado** en el [listado oficial](https://gobierno.uniandes.edu.co/es/publicaciones/notas-de-politica) («Nota de política No. 38»). El «34» de los metadatos del PDF es el título del archivo de Illustrator; la portada no imprime el número |
| `urcuqui2020` | Urcuqui, Moreno, Montenegro, Riascos y Dulce (2020), IEEE BESC 2020, pp. 1–6 | Crossref | Sí | Sí: GAN condicional, exactitud y equidad | ✅ Se añadió el DOI `10.1109/BESC51023.2020.9348315` (antes había una URL personal) |
| `riascos2023` | Riascos Villegas, Ñungo, Gómez Tobón, Dulce Rubio y Gómez (2023), *PLOS ONE, 18*(7), e0287776 | Crossref (DOI `10.1371/journal.pone.0287776`) | Sí | Sí: modelado espacio-temporal con subregistro | ✅ |
| `provost2013` | Provost y Fawcett (2013), *Data science for business*, O'Reilly Media | Open Library (ISBN 9781449361327) | Sí | Sí: referencia metodológica general | ✅ |
| `sdp2025` | Secretaría Distrital de Planeación (2025), *Proyecciones y retroproyecciones de población (2005–2035)*, Datos Abiertos Bogotá | API CKAN del portal (`package_show`, 2026-11-16): organización «Secretaría Distrital de Planeación - SDP», licencia CC BY 4.0, recurso por localidad `202503_…_2005_2035.ods` creado el 2025-05-14 | Sí. El año de la referencia es el de la versión publicada (2025) | Sí: población por localidad y año, usada como denominador de las tasas de la Línea 123 | ✅ |
| `hyndman2006` | Hyndman y Koehler (2006), *Another look at measures of forecast accuracy*, *International Journal of Forecasting, 22*(4), 679–688 | Crossref (DOI `10.1016/j.ijforecast.2006.03.001`) y preprint de los autores (`robjhyndman.com/papers/mase.pdf`) | Sí | Ver [referencias de la metodología](#referencias-de-la-metodología-38) | ✅ Pendiente de citar en la sección 7 (#39) |
| `hyndman2021` | Hyndman y Athanasopoulos (2021), *Forecasting: Principles and practice* (3.ª ed.), OTexts | Open Library (ISBN 9780987507136, OTexts, 2021) y la edición en línea `otexts.com/fpp3`, secciones 5.8 y 5.10 | Sí. La edición en línea se actualiza; se cita la 3.ª edición | Ver [referencias de la metodología](#referencias-de-la-metodología-38) | ✅ Pendiente de citar en la sección 7 (#39) |

## Referencias de la metodología (#38)

Consulta del **2026-11-16**. Respaldan las métricas y la validación de `docs/METODOLOGIA.md`. Entran en `Informe/referencias.tex` cuando la sección 7 se integre en LaTeX (#39), porque APA solo lista las obras citadas. Cada una respalda lo siguiente, y nada más.

**`hyndman2006`** (preprint de los autores, secciones 2.2, 3 y 5):
- Propone el MASE: el error se escala por el **MAE dentro de la muestra del pronóstico ingenuo de un paso** (`|Yᵢ − Yᵢ₋₁|`), no del ingenuo estacional.
- Ese escalado es independiente de la escala de los datos. Un MASE menor que 1 indica errores menores, en promedio, que los del ingenuo de un paso dentro de la muestra.
- Los errores porcentuales (MAPE) son infinitos o indefinidos si algún `Yₜ = 0`, tienen una distribución muy sesgada cuando `Yₜ` está cerca de cero y suponen un cero con significado.
- Concluye que el MASE es la mejor medida disponible cuando las series tienen escalas muy distintas o valores cercanos a cero o negativos.

**`hyndman2021`** (secciones 5.8 y 5.10 de la edición en línea):
- Da la **versión estacional** del MASE: el denominador es el error medio del ingenuo estacional sobre el entrenamiento, `(1/(T−m)) Σ |yₜ − yₜ₋ₘ|`. Es la que usa `scripts/baselines.py`, con `m = 7`. Hay que citar esta obra, y no solo `hyndman2006`, para esa variante.
- Asimetría del MAPE: dice que pone una penalización mayor en los errores negativos que en los positivos.
- Define la validación cruzada de series de tiempo como **evaluación con origen de pronóstico rodante**: cada conjunto de prueba se pronostica solo con observaciones anteriores, así que no se usan observaciones futuras.

**Cuidado con el signo de la asimetría.** El preprint de `hyndman2006` dice «heavier penalty on positive errors» y `hyndman2021` dice «heavier penalty on negative errors»: usan convenciones de signo distintas para el error. Para no depender de la convención, el informe lo dice en términos del pronóstico:
- si `ŷ < y`, el error porcentual no pasa del 100 %;
- si `ŷ > y`, no tiene cota.

Por tanto, el MAPE castiga más la sobreestimación. Es una propiedad de la fórmula y puede citarse a `hyndman2021`.

## Pendientes
- [x] Confirmar el número de la nota de política de Riascos et al. (34 o 38) en el listado de notas de política de la Escuela de Gobierno Alberto Lleras Camargo.
- [ ] Martínez Chitiva (2025): leer el PDF para extraer las fuentes de datos y los modelos comparados, que la matriz del #25 necesita.
- [ ] Las referencias de los datasets (Línea 123, Policía y Fiscalía) llevan «(s. f.)». En APA 7 deben incluir la fecha de consulta; esto se aborda en el #26.
