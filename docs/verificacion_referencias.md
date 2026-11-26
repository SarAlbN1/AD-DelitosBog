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
| `hyndman2006` | Hyndman y Koehler (2006), *Another look at measures of forecast accuracy*, *International Journal of Forecasting, 22*(4), 679–688 | Crossref (DOI `10.1016/j.ijforecast.2006.03.001`) y preprint de los autores (`robjhyndman.com/papers/mase.pdf`) | Sí | Ver [referencias de la metodología](#referencias-de-la-metodología-38) | ✅ Citada en la sección 7 |
| `hyndman2021` | Hyndman y Athanasopoulos (2021), *Forecasting: Principles and practice* (3.ª ed.), OTexts | Open Library (ISBN 9780987507136, OTexts, 2021) y la edición en línea `otexts.com/fpp3`, secciones 5.8 y 5.10 | Sí. La edición en línea se actualiza; se cita la 3.ª edición | Ver [referencias de la metodología](#referencias-de-la-metodología-38) | ✅ Citada en la sección 7 |

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

## Referencias de las limitaciones (#48)

Consulta del **2026-11-24**. Cada una respalda lo siguiente, y nada más.

| Clave | Referencia | Cómo se verificó | Qué respalda en la sección 11 | Estado |
|---|---|---|---|---|
| `ensign2018` | Ensign, Friedler, Neville, Scheidegger y Venkatasubramanian (2018), *Runaway feedback loops in predictive policing*, *Proceedings of the 1st Conference on Fairness, Accountability and Transparency*, PMLR 81, 160–171 | Página de PMLR (`proceedings.mlr.press/v81/ensign18a.html`: autores, conferencia, páginas 160–171, 2018) y resumen en arXiv (`1706.09847`) | Según el resumen: un sistema que asigna la policía por zonas y se actualiza con los incidentes que esa policía **descubre** puede enviarla repetidamente a los mismos barrios con independencia de la tasa real; los incidentes **reportados** por residentes atenúan el efecto pero no lo eliminan | ✅ |
| `riascos2023` | Ya verificada arriba (Crossref) | Resumen en Crossref | Modelo de eventos espacio-temporales con subregistro; estima con datos de Bogotá las tasas «verdaderas» de delito y de subregistro. **No** se citan cifras del artículo | ✅ |

**Descartada: Lum e Isaac (2016)**, *To predict and serve?*, *Significance, 13*(5), 14–19 (DOI `10.1111/j.1740-9713.2016.00960.x`, verificado en Crossref). El texto completo es de pago y solo se pudo leer el resumen, que no menciona los bucles de retroalimentación. No se cita para no atribuirle lo que no se comprobó.

## Referencias de las secciones 9 y 10 (#46, #47)

Consulta del **2026-11-26**. Cada una respalda lo siguiente, y nada más. Los metadatos de Crossref (autores, año, revista, volumen, número y páginas) coinciden con la entrada de `Informe/referencias.tex`.

| Clave | Referencia | Cómo se verificó | Qué respalda | Estado |
|---|---|---|---|---|
| `breiman2001` | Breiman (2001), *Random forests*, *Machine Learning, 45*(1), 5–32 | Crossref (DOI `10.1023/A:1010933404324`) | Sección 10: medir la importancia de una variable como el aumento del error al permutar sus valores | ✅ |
| `diebold1995` | Diebold y Mariano (1995), *Comparing predictive accuracy*, *Journal of Business & Economic Statistics, 13*(3), 253–263 | Crossref (DOI `10.1080/07350015.1995.10524599`) | Sección 9: la prueba de igualdad de exactitud predictiva entre dos pronósticos | ✅ |
| `harvey1997` | Harvey, Leybourne y Newbold (1997), *Testing the equality of prediction mean squared errors*, *International Journal of Forecasting, 13*(2), 281–291 | Crossref (DOI `10.1016/S0169-2070(96)00719-4`) | Sección 9: la corrección para muestras pequeñas de la prueba anterior | ✅ |
| `newey1987` | Newey y West (1987), *A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix*, *Econometrica, 55*(3), 703–708 | Crossref (DOI `10.2307/1913610`) | Sección 9: la varianza robusta a la autocorrelación con 7 rezagos | ✅ con una salvedad: Crossref solo registra la primera página (703). La última (708) no se pudo confirmar en esta pasada |

## Pendientes
- [x] Confirmar el número de la nota de política de Riascos et al. (34 o 38) en el listado de notas de política de la Escuela de Gobierno Alberto Lleras Camargo.
- [ ] Martínez Chitiva (2025): leer el PDF para extraer las fuentes de datos y los modelos comparados, que la matriz del #25 necesita.
- [x] Las referencias de los datasets (Línea 123, Policía y Fiscalía) llevan «(s. f.)». En APA 7 deben incluir la fecha de consulta; esto se aborda en el #26. Resuelto: las tres llevan año (2026) y «Recuperado el 11 de noviembre de 2026».

## Verificación final (#53)

### Pasada preliminar: 2026-11-25

Sobre `main` (`9acfece`, secciones 2–7 y apéndices) más la referencia que añade el #113 (`ensign2018`, sección 11). Las secciones 1 y 8 a 11 aún no están en el informe. Cuando se integren, se repite la comprobación solo para sus citas y referencias nuevas.

**Citas y referencias.** Se extrajeron todas las claves de `\citet` y `\citep` de `Informe/informe.tex` y `Informe/secciones/*.tex`, y se compararon con los `\bibitem` de `Informe/referencias.tex`.

- `main`: 14 claves citadas y 14 entradas. No hay citas sin entrada ni entradas sin cita.
- Con el #113: 15 y 15 (`ensign2018` se cita en la sección 11 y tiene entrada).

**Enlaces.** Se consultó cada `\url` de `referencias.tex` siguiendo redirecciones.

| Clave | Enlace | Resultado |
|---|---|---|
| `campo2017` | `hdl.handle.net/1992/50785` | Resuelve. El repositorio Uniandes responde a clientes automáticos con una página de verificación. El registro ya se había verificado por su API (#24) |
| `fonseca2019` | `hdl.handle.net/10654/31958` | Resuelve al registro de UMNG. **Cambiado:** antes enlazaba al archivo (`…/bitstreams/…/content`). El handle es persistente y se obtuvo de la API DSpace del repositorio (`dc.identifier.uri`; título y fecha 2019-06-11 coinciden) |
| `garzon2025` | `hdl.handle.net/11371/8075` | Resuelve al registro de Los Libertadores. **Cambiado:** antes enlazaba a una descarga (`…/bitstreams/…/download`), que ya redirigía a otra ruta. El handle se obtuvo igual que el anterior (título y fecha 2025-06 coinciden) |
| `martinez2025` | `ridum.umanizales.edu.co/handle/20.500.12746/7648` | Resuelve. Igual que Uniandes, muestra una página de verificación a clientes automáticos |
| `riascos2020` | `gobierno.uniandes.edu.co/…/NP-38.pdf` | Resuelve (PDF) |
| `hyndman2021` | `otexts.com/fpp3/` | Resuelve |
| `ensign2018` | `proceedings.mlr.press/v81/ensign18a.html` | Resuelve |
| `fiscalia` | `datos.gov.co/d/dbdv-iihs` | Resuelve a la ficha «Procesos Fiscalía V3» |
| `policia` | `policia.gov.co/estadistica-delictiva` | Resuelve |
| `linea123` | `datosabiertos.bogota.gov.co/dataset/incidentes` | Resuelve |
| `sdp2025` | `datosabiertos.bogota.gov.co/dataset/proyecciones-y-retroproyecciones-de-poblacion-2005-2035` | Resuelve |

`provost2013` es un libro impreso y no lleva enlace.

**DOI.** Los tres resuelven a la página de su editorial. Sus metadatos en Crossref coinciden con la entrada: autores, año, revista o actas, volumen, número y páginas.

| Clave | DOI | Crossref |
|---|---|---|
| `hyndman2006` | `10.1016/j.ijforecast.2006.03.001` | Hyndman y Koehler, 2006, *International Journal of Forecasting* 22(4), 679–688 |
| `urcuqui2020` | `10.1109/BESC51023.2020.9348315` | Cinco autores, 2020, BESC 2020, pp. 1–6 |
| `riascos2023` | `10.1371/journal.pone.0287776` | Cinco autores, 2023, *PLOS ONE* 18(7), e0287776 |

### Pasada de DOI y enlaces: 2026-11-26

Sobre `main` (`628b99d`, secciones 1 a 7 y 9 a 11, y apéndices). La sección 8 aún no existe.

**Citas y referencias.** 19 entradas y 19 claves citadas: no hay citas sin entrada ni entradas sin cita.

**DOI.** Los siete DOI de `referencias.tex` se consultaron en Crossref y coinciden con la entrada: `breiman2001`, `diebold1995`, `harvey1997`, `hyndman2006`, `newey1987`, `riascos2023` y `urcuqui2020` (las cuatro primeras, nuevas, en la sección anterior). Newey y West: ver la salvedad sobre la última página.

**Ensign et al. (2018).** La ficha de PMLR (`proceedings.mlr.press/v81/ensign18a.html`) da el título *Runaway Feedback Loops in Predictive Policing*, los cinco autores de la entrada, la fecha 2018, las páginas 160–171 y la *Conference on Fairness, Accountability and Transparency*. Coincide.

**Enlaces.** Se siguieron las redirecciones de cada `\url`.

| Resultado | Claves |
|---|---|
| Resuelven (200 o 202) | `breiman2001`, `ensign2018`, `fiscalia`, `fonseca2019`, `garzon2025`, `harvey1997`, `hyndman2021`, `hyndman2006`, `newey1987`, `policia`, `riascos2020`, `riascos2023`, `sdp2025`, `linea123`, `urcuqui2020` |
| **403 por protección contra clientes automáticos** | `campo2017` y `martinez2025` (página de verificación de los repositorios) y `diebold1995` (T&F). El DOI de `diebold1995` sí se verificó en Crossref |

**Identificadores persistentes.** El sistema de handles resuelve `1992/50785`, `10654/31958` y `11371/8075` a la página de su repositorio. **`20.500.12746/7648`, el de Martínez Chitiva (2025), no está registrado en el sistema global de handles** (código de respuesta 2). La entrada cita directamente la dirección del repositorio de la Universidad de Manizales, que sí responde, pero detrás de una página de verificación. Hay que abrirla a mano en un navegador para confirmar que el registro existe; su metadato se verificó por API en el #24.

**Queda para la pasada final.** Esta pasada no reemplaza a la del cierre:

- [x] Repetir la comparación de citas y referencias con las secciones 1, 9, 10 y 11 (2026-11-26: 19 y 19). Queda repetirla cuando entre la sección 8.
- [x] Verificar las referencias nuevas de las secciones 9 y 10 (Breiman, Diebold y Mariano, Harvey et al. y Newey y West). Queda lo que traiga la sección 8, si trae alguna.
- [ ] Abrir a mano en un navegador la dirección de Martínez Chitiva (2025) y la última página de Newey y West (708), que esta pasada no pudo confirmar.
- [ ] Compilar el PDF y confirmar que no hay citas indefinidas (`Citation … undefined`) en el registro de LaTeX. En esta pasada no se compiló.
