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
- **Uso**: `objetivo`, `predictora`, `filtro`, `trazabilidad` o `no se usa`, según el papel previsto
  en el proyecto.

> Estado: **primera versión, pendiente de completar.** Las entradas marcadas «(por confirmar)» y la
> columna «Uso» de la segunda y tercera entrega necesitan una segunda pasada. Ver la sección 6.

---

## 1. Policía Nacional — registro (`policia_registro`)

Fuente principal propuesta. Seis archivos anuales, 2020–2025. **Una fila = una víctima**, con
`CANTIDAD` siempre igual a 1. Cubre todos los delitos del país; el proyecto se queda con
`CODIGO DANE` = 11001 y `DELITOS` = `(05022) Hurto a personas`.

| Variable | Nombre original | Tipo | Distintos | Descripción | Uso |
|---|---|---|---:|---|---|
| `fecha_hecho` | `FECHA HECHO` | fecha | 2.192 | Fecha en que ocurrió el hecho, formato `AAAA/MM/DD`. Son 2.192 días distintos, que es exactamente el número de días de 2020–2025. No hay huecos de días completos | objetivo |
| `cantidad` | `CANTIDAD` | entero | **1** | Siempre vale 1. Confirma que la fila es un registro individual y no un conteo. Contar filas y sumar esta columna dan el mismo número | trazabilidad |
| `delitos` | `DELITOS` | texto | 18 | Delito con su código ICCS en el texto, p. ej. `(05022) Hurto a personas`. La etiqueta es idéntica en los seis años | filtro |
| `codigo_dane` | `CODIGO DANE` | entero | 1.117 | Código DANE del municipio del hecho. Bogotá es 11001. Conserva el cero inicial en los municipios de departamentos con código bajo (`05001`) | filtro |
| `municipio` | `MUNICIPIO` | texto | 1.021 | Municipio del hecho. **No hay localidad ni barrio**: en Bogotá todas las filas caen en un único municipio, así que esta fuente no permite análisis territorial interno | no se usa |
| `departamento` | `DEPARTAMENTO` | texto | 33 | Departamento del hecho | no se usa |
| `mes` | `MES` | entero | 12 | Mes del hecho, redundante con `fecha_hecho` | no se usa |
| `armas_medios` | `ARMAS MEDIOS`, y `ARMA MEDIO` en 2021 | texto | 54 | Arma o medio empleado. En el hurto a personas de Bogotá en 2024 se reparte entre sin empleo de armas, arma blanca, arma de fuego, contundentes, no reportado y escopolamina. **El nombre de la columna cambia en 2021** y se unifica con `renombrar` en el manifiesto | predictora |
| `genero` | `GENERO` | texto | 2 | Género de la víctima. **5,28 % de nulos.** El propio archivo advierte que esta variable no tiene calidad validada en completitud | predictora, con reservas |
| `agrupa_edad_persona` | `*AGRUPA EDAD PERSONA*` | texto | 3 | Grupo de edad de la víctima, p. ej. «DE 18 AÑOS Y MÁS». **0,36 % de nulos** y la misma advertencia de calidad. Solo tres categorías, así que aporta poca resolución | predictora, con reservas |
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
| `localidad` | `LOCALIDAD` | texto | 22 | Localidad de Bogotá. **Única fuente con desglose territorial interno.** Incluye la categoría «SIN LOCALIZACION», que no es una localidad y hay que tratar aparte | predictora |
| `cod_localidad` | `COD_LOCALIDAD` | entero | 22 | Código de la localidad | trazabilidad |
| `upz` / `cod_upz` | `UPZ`, `COD_UPZ` | texto | 125 | Unidad de planeamiento zonal. También trae «SIN LOCALIZACION» | predictora |
| `id` | `ID` | texto | >200.000 | **No es único.** 2.633 identificadores se repiten en el archivo completo y 166 en las filas de hurto del periodo, con un máximo de 2 repeticiones. No sirve como clave primaria | no se usa |

## 4. Fiscalía — Procesos V3 (`fiscalia`)

**Una fila = un par proceso–delito** (noticia criminal). Un proceso puede ocupar varias filas.
2.002.177 filas, 1.300.703 dentro de 2018–2025, con 1.297.042 procesos distintos.

| Variable | Nombre original | Tipo | Distintos | Descripción | Uso |
|---|---|---|---:|---|---|
| `proceso_anonimizado` | ídem | texto | >200.000 | Identificador anonimizado del proceso. Es la clave para contar procesos únicos frente a filas | trazabilidad |
| `a_o_hecho` / `mes_hecho` | ídem | entero | 24 / 13 | Año y mes del hecho. **`mes_hecho` tiene 13 valores distintos**, uno más que los meses: incluye una categoría de «Sin Información» que hay que tratar antes de construir series | filtro |
| `a_o_creacion_proceso` / `mes_creacion_proceso` | ídem | entero | 17 / 12 | Año y mes en que se creó el proceso. **No es la fecha del hecho.** Usarla como tal introduciría fuga de información, porque un proceso puede abrirse meses después | no se usa |
| `delito` | `delito` | texto | 118 | Delito concreto, p. ej. «Hurto Calificado Art. 240 C.P. Agravado». 118 variantes | filtro |
| `capitulo_delito` | ídem | texto | 1 | «Del Hurto» tras el filtro. **Incluye todas las modalidades**: personas, automotores, residencias. No equivale al hurto a personas de Policía | filtro |
| `titulo_delito` | ídem | texto | 1 | «Delitos Contra El Patrimonio Economico». Constante tras el filtro | no se usa |
| `grado_delito` | ídem | texto | 5 | Grado del delito, p. ej. «Ninguno» (por confirmar: si distingue tentativa de consumado, es relevante) | por confirmar |
| `estado` | ídem | texto | 2 | Estado del proceso: activo o inactivo | predictora, con reservas |
| `etapa` | ídem | texto | 4 | Etapa procesal, p. ej. «Ejecución De Penas». **Depende del tiempo transcurrido desde el hecho**, así que es un candidato claro a fuga de información | no se usa |
| `tipo_noticia` | ídem | texto | 8 | Cómo entró la noticia criminal, p. ej. «De Oficio (Informes)». Distingue denuncia de actuación de oficio | predictora |
| `dir_hecho_rural_urbana` | ídem | texto | 3 | Zona del hecho. Incluye «Sin Información» | predictora |
| `seccional` | ídem | texto | 53 | Dirección seccional que tramita. 53 valores aunque el hecho sea siempre en Bogotá (por confirmar: probablemente refleja traslados entre seccionales) | por confirmar |
| `cod_dane_hecho` | ídem | entero | 1 | 11001 tras el filtro | filtro |
| `delito_querellable`, `proceso_conexado`, `proceso_con_conexidad`, `es_ruptura`, `procedimiento_abreviado`, `tipo_delito`, `ley` | ídem | texto | 2–3 | Atributos procesales binarios o casi binarios (por confirmar su definición exacta) | por confirmar |
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
4. **Hay tres candidatos claros a fuga de información** que no deben entrar como predictores:
   `a_o_creacion_proceso` / `mes_creacion_proceso`, `etapa` y, con cuidado, `estado`.
5. **Dos fuentes no tienen clave primaria utilizable**: el `ID` de Línea 123 se repite y Policía no
   publica identificador.

## 6. Lo que falta por completar

Esta es la primera versión. Queda pendiente:

- Confirmar con la ficha metodológica de la Fiscalía las entradas marcadas **(por confirmar)**:
  `grado_delito`, `seccional` y el bloque de atributos procesales binarios.
- Confirmar con la ficha metodológica de la Policía que la fila representa una **víctima** y no un
  hecho. Todo apunta a víctima, porque la fila trae género y edad de una persona, pero conviene
  tenerlo por escrito antes de afirmarlo en el informe.
- Revisar la columna **Uso**: refleja el papel previsto hoy y puede cambiar con la decisión de
  población (#18) y con la definición de la variable objetivo (#37).
- Añadir, cuando se decidan, las variables derivadas de la segunda entrega (#33).
