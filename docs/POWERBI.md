# Tablero de Power BI: modelo de datos y montaje (#106)

Las hojas las genera `python scripts/exportar_powerbi.py` desde las salidas versionadas. Quedan en
`outputs/powerbi/`: un CSV por tabla y un `tablero_powerbi.xlsx` con una hoja por tabla.

## 0. El tablero ya montado: `powerbi/Tablero-DelitosBOG.pbip`

El tablero está versionado como **proyecto de Power BI** (`.pbip`), no como `.pbix` binario. Todo es
texto y se revisa en Git:

| Carpeta | Qué contiene | Cómo se produce |
|---|---|---|
| `powerbi/Tablero-DelitosBOG.SemanticModel/` | El modelo en TMDL: 18 tablas, 11 relaciones y las medidas DAX | Se edita en Power BI Desktop y se guarda |
| `powerbi/Tablero-DelitosBOG.Report/` | Las cuatro páginas (Panorama, Territorio, Fuentes y calidad, Modelado) | `python scripts/generar_reporte_powerbi.py` |
| `outputs/powerbi/geo_localidades.csv`, `localidades_bogota.topojson` | Centroides y polígonos de las localidades para el mapa | `python scripts/geo_localidades_powerbi.py` (necesita `data/raw/localidades.geojson`, ver `data/README.md`) |

**Flujo de datos.** `data/raw` → scripts del proyecto → `outputs/powerbi/*.csv` (versionados en
`main`) → Power Query lee esos CSV de la **copia local del repositorio** con la función `LeerHoja` →
modelo → páginas. No hay orígenes web, así que Power BI no pide niveles de privacidad.

**Para abrirlo en otra máquina:**

1. Clonar el repositorio y quedarse en `main` (o hacer `git pull`).
2. Abrir `powerbi/Tablero-DelitosBOG.pbip` con Power BI Desktop.
3. Si la carpeta del repositorio no es `C:\Users\saraa\Proy\AD-DelitosBog`: **Transformar datos →
   Editar parámetros → `RutaRepo`** con la ruta propia, y **Actualizar**.

El mapa usa el visual **Azure Maps** con capa de calor ponderada por la tasa. Si la organización lo
desactiva, la matriz de calor de la misma página muestra la misma lectura.

**Lo que no se versiona:** `powerbi/**/.pbi/localSettings.json` y `cache.abf` (en `powerbi/.gitignore`).

## 1. Cargar

En Power BI Desktop: **Obtener datos → Excel** y elegir `outputs/powerbi/tablero_powerbi.xlsx`,
que trae las 13 hojas. Marcar todas.

Si se prefieren los CSV, **Obtener datos → Carpeta** sobre `outputs/powerbi/` evita cargarlos uno a
uno.

## 2. El modelo, en estrella

| Tabla | Tipo | Grano | Filas |
|---|---|---|---:|
| `fact_serie_diaria` | hecho | un día | 2.131 |
| `fact_linea123_localidad` | hecho | año × mes × localidad | 1.846 |
| `fact_linea123_upz` | hecho | año × UPZ | 940 |
| `fact_fuentes_mensual` | hecho | mes × fuente | 360 |
| `fact_comparadores` | hecho | comparador | 4 |
| `fact_validacion_rodante` | hecho | pliegue | 6 |
| `dim_calendario` | dimensión | un día | 2.131 |
| `dim_localidad` | dimensión | localidad × año | 120 |
| `dim_fuente` | dimensión | fuente | 4 |
| `qa_embudo`, `qa_nulos`, `qa_atipicos`, `qa_reglas` | control | — | 9 / 39 / 10 / 8 |

### Relaciones

| De | A | Cardinalidad | Nota |
|---|---|---|---|
| `fact_serie_diaria[fecha]` | `dim_calendario[fecha]` | muchos a uno | Marcar `dim_calendario` como **tabla de fechas** |
| `fact_linea123_localidad[localidad]` | `dim_localidad[localidad]` | muchos a uno | Ver el aviso de la clave, abajo |
| `fact_linea123_upz[localidad]` | `dim_localidad[localidad]` | muchos a uno | |
| `fact_fuentes_mensual[fuente]` | `dim_fuente[fuente]` | muchos a uno | |

**El aviso de la clave.** `dim_localidad` tiene una fila por localidad **y año**, así que
`localidad` no es única en esa tabla. Hay dos salidas:

- la recomendada, crear en Power Query una columna `clave_anio = clave & "-" & anio` en las dos
  tablas y relacionar por ella, que es lo correcto si se quiere filtrar por año;
- o, si el tablero solo muestra el periodo completo, cargar `dim_localidad` filtrada a un solo año y
  relacionar por `clave`.

La columna `clave` existe precisamente para cruzar: la SDP escribe «La Candelaria» y Línea 123
«CANDELARIA». Ese desajuste ya dejó una localidad sin tasa una vez (#98), así que **no se cruza por
`localidad`**.

## 3. Medidas en DAX

```dax
-- La variable objetivo
Víctimas = SUM ( fact_serie_diaria[victimas] )

Media diaria = AVERAGE ( fact_serie_diaria[victimas] )

-- Comparar años con el último truncado: SIEMPRE media diaria, nunca el total
Media diaria del año = CALCULATE ( [Media diaria], ALLEXCEPT ( dim_calendario, dim_calendario[anio] ) )

Días con datos = DISTINCTCOUNT ( fact_serie_diaria[fecha] )

Año completo =
VAR d = [Días con datos]
RETURN IF ( d >= 365, "sí", "no (" & d & " días)" )

-- Línea 123: SUMA de incidentes, nunca conteo de filas
Incidentes 123 = SUM ( fact_linea123_localidad[incidentes] )

-- Tasa por habitante. El denominador son personas-año, no habitantes de un año
Tasa por 100k =
VAR inc = [Incidentes 123]
VAR personas = SUM ( dim_localidad[habitantes] )
RETURN DIVIDE ( inc * 100000, personas )

-- Efecto del festivo, controlando el día de la semana (si no, se mezcla con el lunes)
Media lunes festivo =
CALCULATE ( [Media diaria],
    dim_calendario[dia_semana_numero] = 0, dim_calendario[festivo] = 1 )

Media lunes laborable =
CALCULATE ( [Media diaria],
    dim_calendario[dia_semana_numero] = 0, dim_calendario[festivo] = 0 )

Efecto festivo % =
DIVIDE ( [Media lunes festivo] - [Media lunes laborable], [Media lunes laborable] )

-- La barra a batir: el mejor comparador, no uno fijado de antemano
Barra MAE = MINX ( ALL ( fact_comparadores ), fact_comparadores[MAE] )

Mejor comparador =
VAR m = [Barra MAE]
RETURN CALCULATE ( SELECTEDVALUE ( fact_comparadores[comparador] ),
    FILTER ( ALL ( fact_comparadores ), fact_comparadores[MAE] = m ) )
```

**Una medida que no debe existir**, y conviene decirlo explícitamente porque es fácil de escribir:

```dax
-- PROHIBIDA: las fuentes no se suman entre sí
Total todas las fuentes = SUM ( fact_fuentes_mensual[valor] )   -- ✗
```

`fact_fuentes_mensual` va en **formato largo** por eso. En formato ancho, sumar las tres columnas es
un clic; en largo hay que agrupar por fuente y el error salta a la vista.

## 4. Las ocho reglas que el tablero no puede romper

Están además en la hoja `qa_reglas`, para que viajen dentro del archivo:

| Regla | Por qué |
|---|---|
| El mapa y las comparaciones entre localidades usan **tasa**, no conteo | Por conteo Kennedy es 1.ª y por tasa **13.ª**. Un mapa de conteos colorea de rojo lo que solo es población |
| Línea 123 se agrega **sumando** incidentes | Sus filas son grupos: contarlas pondera igual un grupo de 1 y uno de 500 |
| Las fuentes **no se suman** entre sí | Miden cosas distintas |
| «SIN LOCALIZACION» no es una localidad | Fuera del mapa, reportada aparte: 5.683 incidentes, 0,69 % |
| 2020 va **marcado** como año atípico | Media diaria 227,1 frente a 434,9 en 2023 |
| El total de 2025 **no** se compara con años completos | La serie acaba el 2025-10-31; se comparan medias diarias |
| Noviembre y diciembre de 2025 están **fuera** | El registro cae a la mitad y Línea 123 no (#86) |
| Ninguna página presenta un **ranking de peligrosidad** | Ni por conteo ni por tasa: la tasa no capta la población flotante |

Las columnas `es_rural_sumapaz` y `poblacion_flotante_alta` de `dim_localidad` están para poder
marcar visualmente los casos que no se deben leer como el resto.

## 5. Guion de las páginas

**1. Resumen.** Serie diaria (línea, eje de `dim_calendario`). Tarjetas con víctimas totales, media
diaria y días. Tabla por año con **media diaria y total lado a lado**, más la columna «Año
completo», para que el 2025 truncado se vea como tal. Tabla de `dim_fuente` con `filas_auditadas` (Policía: 2020–2025, 741.986), `victimas_en_la_serie`
(730.870, hasta 2025-10-31) y si sostiene el mínimo. Son dos cifras distintas: no se muestran bajo el
mismo rótulo.

**2. Patrones temporales.** Barras por `dia_semana` (viernes 403,1 · domingo 245,0). Línea por
`nombre_mes`. Tarjeta con `Efecto festivo %` (−37,8 %) y el aviso de que compara lunes con lunes.
Puntos de `qa_atipicos` marcados sobre la serie.

**3. Territorio.** Mapa coroplético **por tasa**. Al lado, dos barras: conteo y tasa, con el puesto
en cada una, para que el salto de Kennedy del 1.º al 13.º se vea. Tabla de UPZ con el aviso de que
las diez primeras son solo el 22,3 %.

**4. Fuentes.** `fact_fuentes_mensual` normalizado por fuente (líneas). Matriz de correlación, con
la columna sin 2020 al lado: ahí se ve que Línea 123 cae de 0,601 a 0,284 y las dos de registro se
mantienen. Embudo de `qa_embudo`.

**5. Calidad.** `qa_nulos` por fuente y columna. Una tarjeta destacada con los **713.344 duplicados
exactos de 741.986** y el texto de por qué **no** se eliminan. `qa_reglas` como tabla.

**6. Modelado.** `fact_comparadores` con las cuatro métricas. Tarjeta con `Barra MAE` y `Mejor
comparador`. `fact_validacion_rodante` por pliegue, que muestra que el orden entre comparadores no
es estable: el ingenuo gana 4 de 6 aunque el estacional gane en la ventana final.

## 6. Comprobación

`scripts/exportar_powerbi.py` no copia cifras: las lee. Aun así conviene verificar que el tablero y
el informe cuentan lo mismo. Comprobado al generar:

| Cifra | Informe | Hojas |
|---|---|---|
| Días de la serie | 2.131 | 2.131 |
| Víctimas | 730.870 | 730.870 |
| Predictoras | 21 | 21 |
| Kennedy: puesto por conteo / por tasa | 1 / 13 | 1 / 13 |
| La Candelaria por tasa | 4 | 4 |
| Localidades × años | 20 × 6 | 120 filas |
| Barra: MAE / MASE | 49,04 / 0,922 | 49,04 / 0,922 |
| Meses no comparables | 2025-11, 2025-12 | los dos, marcados |

## 7. Lo que falta

- ~~El `.pbix`~~: resuelto con el proyecto `powerbi/Tablero-DelitosBOG.pbip` (sección 0).
- ~~La capa de localidades para el mapa~~: `scripts/geo_localidades_powerbi.py`.
- **La página de modelado con resultados de modelos**, no solo comparadores. Llega con #43 y #44.
- **Sumapaz en la tasa.** La medida `Tasa 123 por 100k` divide por las personas-año de 2020–2025.
  Sumapaz no tiene llamadas en 2020 y da 179,3; `dim_localidad.tasa_100k_periodo` da 213,3 porque
  omite ese año del denominador. Las otras 19 localidades coinciden. Falta decidir cuál definición
  es la correcta (#22).
