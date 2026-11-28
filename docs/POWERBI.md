# Tablero de Power BI: modelo de datos y montaje (#106)

Las hojas las genera `python scripts/exportar_powerbi.py` desde las salidas versionadas. Quedan en
`outputs/powerbi/`: un CSV por tabla.

## 0. El tablero ya montado: `powerbi/Tablero-DelitosBOG.pbip`

El tablero está versionado como **proyecto de Power BI** (`.pbip`), no como `.pbix` binario. Todo es
texto y se revisa en Git:

| Carpeta | Qué contiene | Cómo se produce |
|---|---|---|
| `powerbi/Tablero-DelitosBOG.SemanticModel/` | El modelo en TMDL: 20 tablas (`fact_modelos` lee la hoja del exportador, y `fact_predicciones` lee `outputs/modelado`), 11 relaciones y las medidas DAX | Se edita en Power BI Desktop y se guarda |
| `powerbi/Tablero-DelitosBOG.Report/` | Las cuatro páginas (Panorama, ¿Cuándo?, ¿Dónde? con el mapa de calor, Pronóstico), cada una con un hallazgo calculado por medida | `python scripts/generar_reporte_powerbi.py` |
| `outputs/powerbi/geo_localidades.csv`, `localidades_bogota.topojson` | Centroides y polígonos de las localidades para el mapa | `python scripts/geo_localidades_powerbi.py` (necesita `data/raw/localidades.geojson`, ver `data/README.md`) |

**Flujo de datos.** `data/raw` → scripts del proyecto → `outputs/powerbi/*.csv` (versionados en
`main`) → Power Query lee esos CSV de la **copia local del repositorio** con la función `LeerHoja` →
modelo → páginas. No hay orígenes web, así que Power BI no pide niveles de privacidad.

**Para abrirlo en otra máquina** (un `.pbip` abre el modelo sin datos: pulse **Actualizar**):

1. Clonar el repositorio y quedarse en `main` (o hacer `git pull`).
2. Abrir `powerbi/Tablero-DelitosBOG.pbip` con Power BI Desktop.
3. **Transformar datos → Editar parámetros → `RutaRepo`**: poner la ruta local del repositorio (el valor
   por defecto es `C:\ruta\al\AD-DelitosBog`, que no existe) y **Actualizar**.

El mapa usa el visual **Azure Maps** con capa de calor ponderada por la tasa. Si la organización lo
desactiva, la tabla de la misma página muestra la misma lectura (tasa coloreada de amarillo a rojo).

**Diseño.** Cada página tiene su propio color de acento (Panorama ámbar, ¿Cuándo? violeta, ¿Dónde?
coral, Pronóstico cian), su propia composición y ningún tipo de gráfico se repite entre páginas:
Panorama usa área y columnas; ¿Cuándo?, la matriz de calor y el anillo; ¿Dónde?, el mapa, el mapa de
árbol del volumen y la tabla con los dos puestos; Pronóstico, líneas y barras. Las familias de modelos
tienen un color fijo. Los títulos largos pasan a una segunda línea y los hallazgos tienen alto para la
frase entera.

**Textos fijos en el script.** El subtítulo y el título de la serie de la página Pronóstico nombran el
modelo («gradiente por histogramas») y la ventana («184 días») a mano, porque un título de visual no
lee medidas. Las dos cifras salen de `outputs/modelado/ajuste/` (#45) y del protocolo de evaluación
(`config/modelado.json`). Si cambian, hay que cambiar esos textos en `scripts/generar_reporte_powerbi.py`.

**Lo que no se versiona:** `powerbi/**/.pbi/localSettings.json` y `cache.abf` (en `powerbi/.gitignore`).

## 1. Cargar

El tablero `.pbip` ya carga las hojas (sección 0). Para montar un informe nuevo desde cero, en Power BI
Desktop **Obtener datos → Carpeta** sobre `outputs/powerbi/` evita cargar los CSV uno a
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
| `fact_modelos` | hecho | modelo × origen | 22 (4 comparadores y 18 modelos) |
| `fact_modelos_pliegue` | hecho | modelo × origen × pliegue | 132 |
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

-- Modelos (página 6). fact_modelos trae comparadores y modelos juntos, con `familia` y `origen`.
-- Los modelos del informe son los de origen "#45" y variante "completo". Sin ellos, estas medidas
-- dan vacío en lugar de un número falso.
Mejor modelo MAE =
MINX ( FILTER ( ALL ( fact_modelos ),
        fact_modelos[origen] IN { "#45", "#144" } && fact_modelos[variante] = "completo" ),
    fact_modelos[MAE] )

Mejora sobre la barra =
IF ( ISBLANK ( [Mejor modelo MAE] ), BLANK (), [Barra MAE] - [Mejor modelo MAE] )

Modelos que superan la barra =
COUNTROWS ( FILTER ( ALL ( fact_modelos ), fact_modelos[supera_barra] ) )
```

`fact_modelos` y `fact_modelos_pliegue` no se relacionan con ninguna otra tabla: su grano es el
modelo. Se cargan siempre con el mismo esquema, también cuando solo hay comparadores. La columna
`variante` distingue las pruebas de sensibilidad a 2020 (`sin_2020` en los árboles y en la regresión,
`desde_2021` en los modelos de series): **no son modelos distintos**, y una barra que las trate como tales exagera la
oferta de modelos. Filtrar por `variante = "completo"` en la vista principal.

La columna `origen` dice qué issue produjo cada fila: `#42` (comparadores), `#43` y `#44` (primera
versión de los modelos, con configuración fija), `#45` (hiperparámetros elegidos en los pliegues) y
`#144` (la regresión lineal, cuya regularización ya se elige en los pliegues dentro de su script).
**Un mismo modelo aparece una vez por origen**, así que sumar o promediar sin filtrar lo duplica. La
vista del informe es `origen` en `#42`, `#45` y `#144`: son las cifras de la sección 9.

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

**6. Modelado.** `fact_modelos` con el MAE y el MASE de cada modelo, ordenado por MAE y con la
barra marcada (`es_barra`). Tarjetas con `Barra MAE`, `Mejor modelo MAE` y `Mejora sobre la barra`.
`fact_modelos_pliegue` por pliegue: el orden entre comparadores no es estable (el ingenuo gana 4 de
6 aunque el estacional gane en la ventana final), y la lectura por pliegue dice si la mejora de un
modelo se sostiene. Vista principal con `variante = "completo"` y `origen` en `#42`, `#45` y `#144`; las
otras, en una página aparte de sensibilidad a 2020. **Las cifras del gradiente por histogramas no se
reproducen exactas entre plataformas** (ver `docs/MODELADO.md`): el tablero muestra las de la imagen
Docker de referencia (#128), y debe decirlo en una nota. **Entre los cuatro mejores modelos no hay
diferencias significativas, y la regresión lineal, la más débil, tampoco se distingue de ellos con
solidez** (sección 9: frente al gradiente, p = 0,023 con HLN y 0,073 con Newey-West): el
tablero no debe presentar un ganador. La regresión es la más débil de las cinco familias, y es la
transparente: sus coeficientes están en `outputs/modelado/regresion/coeficientes.csv`.

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
- ~~La página de modelado con resultados de modelos~~: la página Pronóstico lee las hojas que genera
  `scripts/exportar_powerbi.py` (`fact_modelos`, con la barra calculada, la familia, la variante y el
  origen) y, para la serie diaria, las predicciones de `outputs/modelado/ajuste` (#45) y de
  `outputs/modelado/regresion` (#144).
- ~~Los resultados ajustados de #45 y la regresión lineal de #144~~: ya están. La página Pronóstico
  muestra las cifras de la sección 9 del informe (origen `#45` y `#144`).
- **Sumapaz en la tasa.** La medida `Tasa 123 por 100k` divide por las personas-año de 2020–2025.
  Sumapaz no tiene llamadas en 2020 y da 179,3; `dim_localidad.tasa_100k_periodo` da 213,3 porque
  omite ese año del denominador. Las otras 19 localidades coinciden. Falta decidir cuál definición
  es la correcta (#22).
