# Diccionario de datos (#19)

Describe las variables de las cuatro fuentes tal como vienen publicadas, antes de cualquier
transformación. Los nombres, tipos, número de valores distintos y ejemplos **no están escritos a
mano**: salen de `outputs/auditoria/diccionario_variables.csv` y
`outputs/auditoria_policia/diccionario_variables.csv`, que produce `scripts/auditoria_datasets.py`.

Columnas de cada tabla:

- **Variable**: el nombre normalizado que usa la auditoría (minúsculas, sin tildes, con `_`).
- **Nombre original**: como aparece en el archivo publicado.
- **Tipo**: inferido por la auditoría sobre los valores reales, no declarado por la fuente.
- **Distintos**: número de valores distintos observados.
- **Descripción**: qué representa. Donde dice **(por confirmar)**, es una interpretación razonable
  que todavía no está respaldada por la ficha metodológica de la entidad.
- **Uso**: `objetivo`, `predictora`, `filtro`, `trazabilidad`, `descriptiva` (se analiza pero no
  entra al modelo) o `no se usa`, según el papel previsto en el proyecto.

> Estado: **completo para la primera entrega.**
> - Las entradas de Fiscalía «(por confirmar)» se resolvieron con la ficha oficial del conjunto en datos.gov.co.
> - La columna «Uso» sigue la decisión D-01 ([decisiones.md](decisiones.md)).
> - Lo que sigue abierto está en la sección 6.

---

## 1. Policía Nacional — registro (`policia_registro`)

Fuente principal y de la variable objetivo (D-01). Seis archivos anuales, 2020–2025. **Una fila = una víctima**, con
`CANTIDAD` siempre igual a 1. Cubre todos los delitos del país; el proyecto se queda con
`CODIGO DANE` = 11001 y `DELITOS` = `(05022) Hurto a personas`.

| Variable | Nombre original | Tipo | Distintos | Descripción | Uso |
|---|---|---|---:|---|---|
| `fecha_hecho` | `FECHA HECHO` | fecha | 2.192 | Fecha en que ocurrió el hecho, formato `AAAA/MM/DD`. Son 2.192 días distintos, que es exactamente el número de días de 2020–2025. No hay huecos de días completos | objetivo |
| `cantidad` | `CANTIDAD` | entero | **1** | Siempre vale 1. Confirma que la fila es un registro individual y no un conteo. Contar filas y sumar esta columna dan el mismo número | trazabilidad |
| `delitos` | `DELITOS` | texto | 18 | Delito con su código ICCS en el texto, p. ej. `(05022) Hurto a personas`. La etiqueta es idéntica en los seis años | filtro |
| `codigo_dane` | `CODIGO DANE` | entero | 1.117 | Código DANE del municipio del hecho. Bogotá es 11001 | filtro |
| `municipio` | `MUNICIPIO` | texto | 1.021 | Municipio del hecho. **No hay localidad ni barrio**: en Bogotá todas las filas caen en un único municipio, así que esta fuente no permite análisis territorial interno | no se usa |
| `departamento` | `DEPARTAMENTO` | texto | 33 | Departamento del hecho | no se usa |
| `mes` | `MES` | entero | 12 | Mes del hecho, redundante con `fecha_hecho` | no se usa |
| `armas_medios` | `ARMAS MEDIOS`, y `ARMA MEDIO` en 2021 | texto | 54 | Arma o medio empleado. En el hurto a personas de Bogotá en 2024 se reparte entre sin empleo de armas, arma blanca, arma de fuego, contundentes, no reportado y escopolamina. **El nombre de la columna cambia en 2021** y se unifica con `renombrar` en el manifiesto | predictora |
| `genero` | `GENERO` | texto | 2 | Género de la víctima. **5,28 % de nulos en el archivo nacional, pero solo 0,08 % (622 filas) en el hurto a personas de Bogotá** (`outputs/serie_objetivo/resumen_serie.json`). El propio archivo advierte que esta variable no tiene calidad validada en completitud | descriptiva; no entra en la serie diaria |
| `agrupa_edad_persona` | `*AGRUPA EDAD PERSONA*` | texto | 3 | Grupo de edad de la víctima, p. ej. «DE 18 AÑOS Y MÁS». **0,36 % de nulos en el archivo nacional y 0,05 % (392) en la población**, con la misma advertencia de calidad. El 98,9 % es «DE 18 AÑOS Y MÁS», así que aporta poca resolución | descriptiva; no entra en la serie diaria |
| `iccs` | `ICCS` | entero | 18 | Código ICCS del delito, redundante con el prefijo de `DELITOS`. **Presente en 5 de los 6 archivos: falta en 2023.** Por eso el filtro de hurto usa `DELITOS` y no esta columna | no se usa |

**No hay identificador de víctima ni de hecho.** Esto tiene una consecuencia que condiciona todo el
preprocesamiento: 713.344 de las 741.986 filas de hurto en Bogotá son duplicados exactos, porque dos
víctimas del mismo perfil el mismo día producen filas idénticas. Un `drop_duplicates()` dejaría
28.642 filas y tumbaría el requisito de 500.000. Detalle en
[`cruce_policia_registro_agregado.md`](cruce_policia_registro_agregado.md).

## 2. MinDefensa `4rxi-8m8d` — agregado diario (`policia_agregado`)

Control de consistencia. **Una fila = un día y un municipio**, con el conteo de hurtos de ese día.
2.922 filas para 2018–2025.

| Variable | Nombre original | Tipo | Distintos | Descripción | Uso |
|---|---|---|---:|---|---|
| `fecha_hecho` | `fecha_hecho` | fecha | 2.922 | Fecha del hecho, en ISO con hora siempre a `00:00:00`. Un valor por día del periodo | trazabilidad |
| `cantidad` | `cantidad` | entero | 521 | **Número de hurtos registrados ese día**, no una fila por hecho. Suma 975.793 en 2018–2025. Confundirla con el número de filas sobreestima el dataset en dos órdenes de magnitud | trazabilidad |
| `cod_muni` | `cod_muni` | entero | 1 | Código DANE del municipio. Todo 11001 tras el filtro | filtro |
| `municipio`, `departamento`, `cod_depto` | ídem | texto/entero | 1 | Constantes tras el filtro de Bogotá | no se usa |

Esta fuente **no sirve para el mínimo de 500.000** (aporta 2.922 filas) pero sí para dos cosas:
verificar el registro año por año, y cubrir 2018–2019, que el registro no publica.

## 3. Línea 123 — incidentes tramitados (`linea123`)

**Una fila = un agregado** de llamadas por año, mes, localidad, UPZ y tipo de incidente. 1.117.394
filas, de las que 25.144 son de hurto dentro de 2018–2025.

| Variable | Nombre original | Tipo | Distintos | Descripción | Uso |
|---|---|---|---:|---|---|
| `cant_incidentes` | `CANT_INCIDENTES` | entero | 1.568 | **Número de llamadas tramitadas** del grupo, no de hechos. Las 25.144 filas de hurto suman 1.094.313 incidentes | trazabilidad |
| `anio` | `ANIO` | entero | 12 | Año del incidente. Hay 12 años: el archivo cubre 2015–2026, más allá del periodo del proyecto. 354.320 filas quedan fuera de 2018–2025 | filtro |
| `mes` | `MES` | entero | 12 | Mes del incidente. La resolución temporal máxima de esta fuente es el mes | predictora |
| `tipo_detalle` | `TIPO_DETALLE` | texto | 138 | Tipificación operativa del incidente. El filtro de hurto busca «HURTO» aquí. **Es la tipificación de la llamada, no una calificación jurídica**, así que no equivale al delito de las otras fuentes | filtro |
| `tipo_incidente` | `TIPO_INCIDENTE` | texto | 107 | Categoría superior del incidente | no se usa |
| `localidad` | `LOCALIDAD` | texto | 22 | Localidad de Bogotá. **Única fuente con desglose territorial interno.** Los 22 valores son las 20 localidades más «SIN LOCALIZACION» y «-» (13 filas), que no son localidades y hay que tratar aparte | predictora |
| `cod_localidad` | `COD_LOCALIDAD` | entero | 22 | Código de la localidad | trazabilidad |
| `upz` / `cod_upz` | `UPZ`, `COD_UPZ` | texto | 125 | Unidad de planeamiento zonal. 116 UPZ más 9 valores sin ubicación («SIN LOCALIZACION», siete «SIN UPZ <localidad>» y «-»), que suman 121.254 filas del archivo completo | predictora |
| `id` | `ID` | texto | >200.000 | **No es único.** 2.633 identificadores se repiten en el archivo completo y 166 en las filas de hurto del periodo, con un máximo de 2 repeticiones. No sirve como clave primaria | no se usa |

## 4. Fiscalía — Procesos V3 (`fiscalia`)

**Una fila = un par proceso–delito** (noticia criminal). Un proceso puede ocupar varias filas.
2.002.177 filas, 1.300.703 dentro de 2018–2025, con 1.297.042 procesos distintos.

| Variable | Nombre original | Tipo | Distintos | Descripción | Uso |
|---|---|---|---:|---|---|
| `proceso_anonimizado` | ídem | texto | >200.000 | Identificador anonimizado del proceso. Es la clave para contar procesos únicos frente a filas | trazabilidad |
| `a_o_hecho` / `mes_hecho` | ídem | entero | 24 / 13 | Año y mes del hecho. **`mes_hecho` tiene 13 valores distintos en el archivo completo**, uno más que los meses: incluye «Sin Información». Esas 767 filas tampoco traen año y quedan fuera del filtro 2018–2025, así que **dentro de la población todos los meses son válidos** | filtro |
| `a_o_creacion_proceso` / `mes_creacion_proceso` | ídem | entero | 17 / 12 | Año y mes en que se creó el proceso. **No es la fecha del hecho.** Usarla como tal introduciría fuga de información, porque un proceso puede abrirse meses después | no se usa |
| `delito` | `delito` | texto | 118 | Tipo penal: artículo del Código Penal, cuantía y, si la hay, circunstancia de agravación, p. ej. «Hurto Calificado Art. 240 C.P. Agravado». Son 118 variantes en el archivo y 114 en 2018–2025. **No codifica la víctima**, así que no permite aislar el hurto a personas; el 94,2 % de las filas no excluibles son tipos genéricos (`outputs/informe/fiscalia_modalidades_resumen.csv`, D-01) | descriptiva |
| `capitulo_delito` | ídem | texto | 1 | «Del Hurto» tras el filtro. **Incluye todas las modalidades**: personas, automotores, residencias. No equivale al hurto a personas de Policía | filtro |
| `titulo_delito` | ídem | texto | 1 | «Delitos Contra El Patrimonio Economico». Constante tras el filtro | no se usa |
| `grado_delito` | ídem | texto | 5 | Según la ficha oficial, informa si el delito es «Agravado, Ninguno, Sin información, Tentativa, Tentativa / Agravado». **Sí distingue la tentativa del delito consumado.** En 2018–2025 tiene 4 valores: Ninguno (1.209.762), Agravado (80.678), Tentativa (6.005) y Tentativa/Agravado (4.258) | descriptiva |
| `estado` | ídem | texto | 2 | Según la ficha, es la situación operativa de la investigación **«al momento de la consulta»**: Activo o Inactivo. Como se fija en la fecha de corte y no en la del hecho, es **fuga de información** si se usa para predecir | no se usa |
| `etapa` | ídem | texto | 4 | Macroetapa procesal según la ficha: Indagación, Investigación, Juicio y Ejecución de Penas. **Depende del tiempo transcurrido desde el hecho**, así que es fuga de información | no se usa |
| `tipo_noticia` | ídem | texto | 8 | Fuente por la que se inicia la investigación según la ficha: denuncia, petición especial, compulsa de copias, de oficio, actos urgentes, asistencia judicial o querella | descriptiva |
| `dir_hecho_rural_urbana` | ídem | texto | 3 | Zona del hecho. Incluye «Sin Información» | descriptiva |
| `seccional` | ídem | texto | 53 | Nombre oficial «DEPENDENCIA»: dependencia de la Fiscalía a la que está asignada la noticia criminal. **No es una ubicación del hecho.** En 2018–2025 tiene 32 valores, y el 99,89 % de las filas (1.299.264) corresponde a la Dirección Seccional de Bogotá. El resto son direcciones especializadas, «Por Asignar» y otras seccionales | no se usa |
| `cod_dane_hecho` | ídem | entero | 1 | 11001 tras el filtro | filtro |
| `delito_querellable` | ídem | texto | 2 | Si el delito es querellable según el Código de Procedimiento Penal. En 2018–2025, Sí en 114.259 filas | descriptiva |
| `proceso_conexado` | ídem | texto | 2 | Si el proceso **fue fusionado a otro** («caso hijo», art. 51 del CPP). Sí en 4.772 filas | trazabilidad |
| `proceso_con_conexidad` | ídem | texto | 2 | Si el proceso **recibe información de otros** («caso padre», art. 51 del CPP). Sí en 3.130 filas | trazabilidad |
| `es_ruptura` | ídem | texto | 2 | Si hubo ruptura de la unidad procesal (art. 53 del CPP), que **genera un nuevo proceso sobre los mismos hechos**. Sí en 4.432 filas. Junto con las dos anteriores, indica que un mismo hecho puede aparecer en más de un proceso | trazabilidad |
| `procedimiento_abreviado` | ídem | texto | 2 | Si se tramita por el procedimiento abreviado de la Ley 1826 de 2017. Sí en 1.238.967 filas | descriptiva |
| `tipo_delito` | ídem | texto | 2 | «Reparto» si es la conducta principal del caso y «Concurso» si es adicional en la misma investigación. Reparto en 1.289.368 filas y Concurso en 11.335 | descriptiva |
| `ley` | ídem | texto | 3 | Norma procesal: Ley 906 (1.293.313), Ley 1098 de infancia y adolescencia (7.364) y Jurisdicción Menores (26) | descriptiva |
| `deli_id` | ídem | entero | 119 | Código interno del delito, redundante con `delito` | no se usa |
| `trimestre_hecho`, `trimestre_creacion` | ídem | texto | 4–5 | Trimestre, redundante con el mes | no se usa |
| `pais_hecho`, `departamento_hecho`, `municipio_hecho` | ídem | texto | 1 | Constantes tras el filtro de Bogotá | no se usa |
| `fecha_corte_datos` | ídem | fecha | 1 | Fecha de corte de la extracción: `31/10/2026`. Sirve para fechar el dataset | trazabilidad |

**Ninguna variable territorial por debajo del municipio.** Fiscalía no permite análisis por
localidad.

---

## 5. Lo que este diccionario deja claro

1. **Las cuatro fuentes miden cosas distintas** y sus columnas de conteo no son comparables:
   `CANTIDAD` = 1 por víctima, `cantidad` = hurtos por día, `CANT_INCIDENTES` = llamadas, y en
   Fiscalía la unidad es el proceso.
2. **Solo Línea 123 tiene desglose territorial interno.** Policía y Fiscalía llegan al municipio.
   Cualquier análisis por localidad sale de Línea 123 o no sale.
3. **Solo Policía tiene fecha diaria.** Línea 123 y Fiscalía llegan al mes. La resolución común a
   las tres es mes × Bogotá.
4. **Hay tres variables con fuga de información** que no deben entrar como predictores:
   `a_o_creacion_proceso` / `mes_creacion_proceso`, `etapa` y `estado`. La ficha oficial confirma que `estado`
   describe el proceso al momento de la consulta.
5. **Dos fuentes no tienen clave primaria utilizable**: el `ID` de Línea 123 se repite y Policía no
   publica identificador.

## 6. Lo que falta por completar

Esta es la primera versión. Queda pendiente:

- **Hecho: definiciones de Fiscalía.** Se tomaron de la ficha oficial del conjunto (`https://www.datos.gov.co/api/views/dbdv-iihs.json`, campo `description` de cada columna, consultada el 2026-11-12). Las frecuencias salen de `scripts/fiscalia_atributos.py` (`outputs/informe/fiscalia_atributos.csv`).
- **Hecho: columna «Uso».** Se alineó con D-01:
  - la variable objetivo es la fecha del registro de Policía agregada por día;
  - Fiscalía es complementaria, así que sus variables son descriptivas;
  - «descriptiva» se añade a los valores de «Uso».
- **Sigue abierto: la unidad de Policía no está confirmada por escrito.** Ni el archivo ni la página de estadística delictiva dicen expresamente que la fila sea una víctima. Lo sostienen tres evidencias:
  - `CANTIDAD` vale 1 en todas las filas;
  - cada fila trae el género y la edad de una persona;
  - el pie del archivo habla de las variables de género y edad de las personas.

  El informe lo presenta como inferencia de esa evidencia.
- **Sigue abierto:** añadir las variables derivadas de la segunda entrega cuando se decidan (#33).
