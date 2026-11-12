# Calidad de los datos (#20)

Una tabla por fuente con los nulos, los duplicados y las anomalías detectadas, su causa probable y
el tratamiento que se propone. Todas las cifras salen de `outputs/auditoria/` y
`outputs/auditoria_policia/`, producidas por `scripts/auditoria_datasets.py`.

Un criterio que se aplica en todo el documento: **lo que la auditoría marca como anomalía no es
necesariamente un error.** Varias de estas marcas son características de la fuente y lo que
procede es documentarlas, no corregirlas.

## Resumen

| Fuente | Filas analizadas | Nulos | Duplicados exactos | Anomalías | Gravedad |
|---|---:|---|---|---|---|
| Policía, registro | 4.829.870 | 2 variables afectadas (5,28 % y 0,36 %) | 713.344 de 741.986 tras el filtro | Ninguna | Media |
| Policía, agregado | 2.922 | Ninguno | Ninguno | Ninguna | Baja |
| Línea 123 | 1.117.394 | Ninguno | Ninguno; `ID` repetido | 354.320 fuera de periodo | Baja |
| Fiscalía | 2.002.177 | Ninguno | Ninguno; proceso repetido por diseño | 767 sin fecha, 700.707 fuera de periodo | Media |

---

## 1. Policía Nacional — registro

| Hallazgo | Magnitud | Causa probable | Tratamiento propuesto |
|---|---|---|---|
| Nulos en `GENERO` | 255.192 filas, **5,28 %** | El propio archivo advierte en su pie que género y edad **no tienen calidad validada en completitud**. No es un fallo de la descarga: es una limitación declarada por la entidad | **No imputar.** Tratar el nulo como una categoría explícita «no reportado» si la variable se usa, y declarar la limitación en el informe (#48). No usarla como predictora principal |
| Nulos en `*AGRUPA EDAD PERSONA*` | 17.470 filas, **0,36 %** | La misma advertencia | Igual que el anterior. Además solo tiene 3 categorías, así que aporta poca resolución |
| Nulos en `MUNICIPIO` | 26 filas, 0,0005 % | Volumen residual. No afecta a Bogotá, que se filtra por `CODIGO DANE` | Ninguno. Las filas se descartan en el filtro territorial |
| **713.344 filas duplicadas exactas** de 741.986 tras el filtro de Bogotá y hurto. Solo 28.642 distintas, hasta 302 repeticiones | **96 % de las filas** | **No es un defecto.** Una fila es arma, departamento, municipio, fecha, género, grupo de edad, DANE, delito, mes y `CANTIDAD` = 1. Dos víctimas con el mismo perfil el mismo día producen filas idénticas, y el archivo no publica identificador de víctima ni de hecho | **Prohibido deduplicar por fila exacta.** Un `drop_duplicates()` dejaría 28.642 filas y tumbaría el requisito de 500.000. El control de consistencia de esta fuente es el agregado diario, no la unicidad de filas |
| El esquema cambia entre los seis archivos: encabezado en la fila 12 o 13, `ARMAS MEDIOS` o `ARMA MEDIO`, y `ICCS` ausente en 2023 | 3 de 6 archivos afectados | Cambios de formato de publicación entre años | Ya resuelto: el conversor detecta la fila del encabezado, el manifiesto unifica el nombre con `renombrar` y el filtro de hurto usa `DELITOS`, presente en los seis años |
| 25.207 filas de pie de archivo | notas y filas en blanco | Las entidades firman el archivo al final con la fuente y la fecha de entrega | Ya resuelto: se descartan antes de auditar y se cuentan por archivo en `conversion.json`. Si se contaran, inflarían el total |

**Lo que está limpio:** `FECHA HECHO` sin nulos y con los 2.192 días del periodo presentes, sin
huecos de días completos. `CANTIDAD` con un único valor distinto, lo que confirma que la fila es un
registro individual.

## 2. Policía / MinDefensa — agregado diario

| Hallazgo | Magnitud | Causa probable | Tratamiento propuesto |
|---|---|---|---|
| Sin nulos, sin duplicados, sin anomalías | 2.922 filas | Es un recurso agregado y validado en el portal | Ninguno |
| Riesgo de interpretación: `cantidad` suma 975.793 con solo 2.922 filas | — | Confundir la suma de la columna con el número de registros sobreestima el dataset en dos órdenes de magnitud | Documentado en `data/README.md` y en el reporte de auditoría. **El mínimo se mide en filas**, nunca por la suma de una columna de conteo |

Es la fuente más limpia de las cuatro, pero la que menos aporta en volumen.

## 3. Línea 123

| Hallazgo | Magnitud | Causa probable | Tratamiento propuesto |
|---|---|---|---|
| **354.320 filas fuera de 2018–2025** | 32 % del archivo | **No es un error.** El recurso publica 2015–2026 y el proyecto analiza 2018–2025 | Se excluyen en el filtro de periodo, que queda documentado en `embudo_filtros.csv`. Debe decirse en el informe para que las 1.117.394 filas originales no se confundan con las 763.074 del periodo |
| **`ID` no es único:** 2.633 identificadores repetidos en el archivo completo y 166 en las filas de hurto del periodo, máximo 2 repeticiones | 0,24 % | Probablemente la clave se construye concatenando año, UPZ y un consecutivo, y colisiona en algunos casos (por confirmar) | **No usar `ID` como clave primaria** ni para deduplicar. Si hace falta una clave, construirla con año, mes, localidad, UPZ y tipo. Importa para #32 |
| Categoría «SIN LOCALIZACION» en `LOCALIDAD` y `UPZ` | Una de las 22 localidades y de las 125 UPZ | Incidentes sin ubicación asignada al tramitar la llamada | **No es una localidad.** Separarla antes de cualquier análisis territorial y reportar su peso, porque si se trata como una localidad más distorsiona los mapas (#35) |
| Cero nulos y cero filas duplicadas exactas | — | — | Ninguno |

**Advertencia de interpretación:** `TIPO_DETALLE` es la tipificación operativa de la llamada, no una
calificación jurídica. Las categorías con «HURTO» no equivalen al delito de las otras fuentes.

## 4. Fiscalía — Procesos V3

| Hallazgo | Magnitud | Causa probable | Tratamiento propuesto |
|---|---|---|---|
| **767 filas con «Sin Información» en `a_o_hecho` y `mes_hecho`** | 0,04 % | El proceso se registró sin fecha del hecho conocida | **Excluir del análisis temporal** y reportar el número. No imputar: inventar una fecha del hecho sesgaría las series. La auditoría ya las marca como `anio_invalido` y `mes_invalido` |
| **700.707 filas fuera de 2018–2025** | 35 % del archivo | **No es un error.** El recurso cubre desde 2010 | Se excluyen en el filtro de periodo |
| El mismo proceso aparece en varias filas: 1.300.703 filas frente a 1.297.042 procesos distintos; 3.661 repetidos, hasta 9 veces | 0,28 % | **Es el diseño de la fuente.** La unidad es el par proceso–delito: un proceso con varios delitos ocupa varias filas | **No deduplicar.** Reportar siempre las dos cifras, filas y procesos únicos, porque responden a preguntas distintas |
| Cero nulos y cero filas duplicadas exactas | — | — | Ninguno |
| `capitulo_delito` = «Del Hurto» incluye modalidades distintas del hurto a personas | — | El capítulo agrupa personas, automotores, residencias y otras | **Restringir a la modalidad comparable** si se quiere contrastar con Policía, usando `delito` (118 variantes). Es una de las preguntas abiertas de #18 |
| Variables que dependen del tiempo transcurrido: `a_o_creacion_proceso`, `mes_creacion_proceso`, `etapa` y `estado` | — | Un proceso puede abrirse meses después del hecho y su etapa avanza con el tiempo | **No usarlas como predictoras.** Son fuga de información. Importa para #33 |

---

## 5. Cobertura temporal verificada

| Fuente | Meses con datos en el periodo | Cobertura |
|---|---:|---|
| Línea 123 | 96 | 2018–2025 completo |
| Fiscalía | 96 | 2018–2025 completo |
| Policía, agregado | 96 | 2018–2025 completo |
| Policía, registro | **72** | **2020–2025.** No existen 2018 ni 2019 a nivel de registro |

Ninguna fuente tiene meses vacíos dentro de su propio periodo. La única discontinuidad real del
proyecto es que el registro de Policía empieza en 2020, y esa es la decisión de #18.

## 6. Conclusión

Ninguna de las cuatro fuentes tiene problemas de calidad que impidan usarla. Lo que hay son tres
riesgos de **interpretación**, y los tres se evitan documentando en lugar de corrigiendo:

1. Deduplicar Policía por fila exacta destruiría el 96 % de los datos.
2. Confundir la suma de una columna de conteo con el número de registros sobreestima el dataset.
3. Usar variables de Fiscalía que dependen del tiempo transcurrido introduciría fuga de información
   en el modelo de la tercera entrega.

Los dos tratamientos que sí modifican datos son: excluir las 767 filas sin fecha de Fiscalía del
análisis temporal, y separar «SIN LOCALIZACION» de las localidades de Línea 123. Todo lo demás se
documenta y se deja como está.
