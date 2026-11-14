# Cobertura, distribuciones y figuras del informe (#21)

Documenta la cobertura temporal y territorial de las cuatro fuentes y selecciona las figuras que
entran en el informe de la primera entrega, cada una con su párrafo de interpretación.

Las figuras ya están generadas por `scripts/auditoria_datasets.py` en `outputs/auditoria/figuras/` y
`outputs/auditoria_policia/figuras/`, en PNG y PDF. No hay que dibujarlas a mano: se regeneran
corriendo la auditoría.

## 1. Cobertura temporal

| Fuente | Meses con datos | Periodo | Resolución máxima |
|---|---:|---|---|
| Línea 123 | 96 | 2018–2025 completo | Mes |
| Fiscalía | 96 | 2018–2025 completo | Mes |
| Policía, agregado | 96 | 2018–2025 completo | **Día** |
| Policía, registro | **72** | **2020–2025** | **Día** |

Ninguna fuente tiene meses vacíos dentro de su propio periodo. La única discontinuidad es que el
registro de Policía no publica 2018 ni 2019.

Fuera del periodo del proyecto, Línea 123 cubre además 2015–2017 y parte de 2026 (354.320 filas) y
Fiscalía arranca en 2010 (700.707 filas). Son datos válidos que el filtro excluye, no errores.

## 2. Cobertura territorial

| Fuente | Nivel más fino | Categorías |
|---|---|---|
| Línea 123 | **UPZ** | 20 localidades y 116 UPZ, más valores sin ubicación («SIN LOCALIZACION», «SIN UPZ …», «-») |
| Policía, registro | Municipio | Bogotá es un único valor: sin desglose interno |
| Policía, agregado | Municipio | Ídem |
| Fiscalía | Municipio | Ídem, más zona urbana/rural y 53 seccionales |

**Solo Línea 123 permite análisis por localidad.** Es una restricción fuerte: la fuente que sostiene
el volumen (Policía) no tiene territorio interno, y la que tiene territorio interno no sostiene el
volumen.

## 3. Distribuciones iniciales

### Evolución anual del hurto a personas en Bogotá (registro de Policía)

| Año | Víctimas registradas |
|---|---:|
| 2020 | 83.136 |
| 2021 | 109.428 |
| 2022 | 137.157 |
| 2023 | **158.745** |
| 2024 | 130.503 |
| 2025 | 123.017 |
| **Total** | **741.986** |

La serie sube desde el mínimo de 2020 hasta el máximo de 2023 y baja en 2024 y 2025. El valor bajo
de 2020 coincide con el año de las restricciones de movilidad por la pandemia, lo que conviene
tener presente: el primer año de la serie no es un año típico y puede afectar al entrenamiento de
los modelos de la tercera entrega.

### Distribución territorial (Línea 123, incidentes de hurto 2018–2025)

Se mide con la **suma de `CANT_INCIDENTES`**, no con el número de filas. Las filas de esta fuente
son grupos agregados, así que contarlas pondera igual a un grupo de 1 incidente y a uno de 500.

| Localidad | Incidentes | % | (Filas) | (% filas) |
|---|---:|---:|---:|---:|
| Kennedy | 133.250 | 12,2 % | 2.466 | 9,8 % |
| Suba | 125.987 | 11,5 % | 2.470 | 9,8 % |
| Engativá | 121.838 | 11,1 % | 1.872 | 7,4 % |
| Usaquén | 71.743 | 6,6 % | 1.995 | 7,9 % |
| Bosa | 69.953 | 6,4 % | 1.118 | 4,4 % |
| Ciudad Bolívar | 64.714 | 5,9 % | 1.711 | 6,8 % |
| Puente Aranda | 55.731 | 5,1 % | 1.111 | 4,4 % |
| Fontibón | 52.337 | 4,8 % | 1.668 | 6,6 % |
| Rafael Uribe Uribe | 49.729 | 4,5 % | 1.172 | 4,7 % |
| San Cristóbal | 48.298 | 4,4 % | 1.275 | 5,1 % |

Total: 1.094.313 incidentes en 25.144 filas.

**Las dos columnas dan rankings distintos, y por eso importa cuál se usa.** Por filas, Suba y
Kennedy empatan y Engativá aparece cuarta con el 7,4 %. Por incidentes, Kennedy es la primera y
Engativá sube a la tercera posición con el 11,1 %, mientras que Bosa y Puente Aranda entran en las
primeras posiciones y Usme y Teusaquillo salen. La medida correcta es la suma de incidentes: contar
filas mide cuántos grupos distintos se reportaron, no cuántos incidentes hubo.

La concentración en Kennedy, Suba y Engativá es coherente con que son las localidades más pobladas,
lo que refuerza la necesidad de **tasas por población** y no solo conteos absolutos, para no
producir una lectura estigmatizante.

## 4. Figuras seleccionadas para el informe

Hay 12 figuras disponibles. Se proponen **cuatro**, cada una porque sostiene una afirmación concreta
del informe y no porque quede bien.

### Figura 1 — `policia_registro_serie_mensual`

`outputs/auditoria_policia/figuras/policia_registro_serie_mensual.pdf`

> Serie mensual de víctimas de hurto a personas en Bogotá entre 2020 y 2025, construida sobre las
> 741.986 filas del registro de la Policía Nacional. Es la variable que el proyecto busca predecir,
> y la figura muestra tres cosas que condicionan el modelado. Primero, el nivel deprimido de 2020,
> año de las restricciones de movilidad, que hace que el inicio de la serie no sea representativo.
> Segundo, el crecimiento sostenido hasta 2023, que marca el máximo del periodo con 158.745
> víctimas. Tercero, el descenso de 2024 y 2025. Una serie con cambio de nivel y de tendencia
> justifica la validación temporal del protocolo de evaluación, en lugar de una partición aleatoria
> que mezclaría periodos con comportamientos distintos.

### Figura 2 — `policia_registro_embudo`

`outputs/auditoria_policia/figuras/policia_registro_embudo.pdf`

> Embudo de filtros del registro de la Policía: de 4.829.870 filas nacionales con todos los delitos
> se pasa a 1.406.157 al quedarse con Bogotá, y a 741.986 al quedarse con hurto a personas. Esta
> figura documenta cómo se construye la población del estudio y sostiene la verificación del
> requisito de 500.000 registros. Importa que las tres cifras se lean como filas y no como la suma
> de ninguna columna: en esta fuente cada fila es una víctima con `CANTIDAD` igual a 1, de modo que
> contar filas y sumar esa columna dan el mismo resultado, lo que no ocurre en las demás fuentes.

### Figura 3 — `linea123_localidad`

`outputs/auditoria/figuras/linea123_localidad.pdf`

> Distribución por localidad de los incidentes de hurto de Línea 123 entre 2018 y 2025, medida con la suma de `CANT_INCIDENTES`. Es la única
> figura territorial posible del proyecto: ni el registro de la Policía ni Fiscalía publican nada
> por debajo del municipio, así que todo el análisis por localidad depende de esta fuente. Kennedy,
> Suba y Engativá concentran entre el 11 % y el 12 % de los incidentes cada una, lo que es coherente
> con que sean de las localidades más pobladas de la ciudad. La figura se construye sumando
> `CANT_INCIDENTES` y no contando filas, porque las filas de esta fuente son grupos agregados y
> contarlas pondera igual a un grupo de un incidente y a uno de quinientos: con filas, Engativá
> aparecería cuarta con el 7,4 % en lugar de tercera con el 11,1 %. Por eso la lectura correcta
> exige además tasas por población y no conteos
> absolutos: un conteo alto en una localidad grande no indica mayor riesgo individual, y
> presentarlo así produciría una interpretación estigmatizante. La figura incluye además la
> categoría «SIN LOCALIZACION», que no es una localidad sino la ausencia de ubicación asignada al
> tramitar la llamada, y que se separa antes de cualquier mapa.

### Figura 4 — `policia_registro_nulos`

`outputs/auditoria_policia/figuras/policia_registro_nulos.pdf`

> Porcentaje de valores nulos por variable en el registro de la Policía. Sostiene la sección de
> limitaciones del informe. Las variables de fecha, delito, código DANE y cantidad no tienen un solo
> nulo, lo que da confianza sobre la población y la serie temporal. En cambio el género presenta un
> 5,28 % de ausencias y el grupo de edad un 0,36 %, exactamente las dos variables sobre las que el
> propio archivo advierte en su pie que no tienen calidad validada en completitud. La consecuencia
> metodológica es que esas dos variables no se imputan: si se usan, el valor ausente se trata como
> una categoría explícita y la limitación se declara.

### Figuras descartadas y por qué

| Figura | Motivo |
|---|---|
| `policia_agregado_serie_mensual` | Redundante con la figura 1, sobre la misma población pero agregada |
| `policia_agregado_localidad`, `policia_registro_localidad` | Una sola barra: en estas fuentes Bogotá es un único municipio |
| `policia_agregado_embudo` | El embudo no excluye nada: las 2.922 filas pasan los cuatro filtros |
| `linea123_serie_mensual`, `fiscalia_serie_mensual` | Útiles para comparar fuentes, pero la variable objetivo es la de Policía. Candidatas para la segunda entrega |
| `linea123_embudo`, `fiscalia_embudo` | El embudo relevante para el requisito es el de la fuente principal |

## 5. Pendiente

La elección de figuras supone que la población principal es el registro de Policía. Si la decisión
de #18 cambia a Fiscalía, las figuras 1, 2 y 4 se sustituyen por sus equivalentes de esa fuente, que
ya están generadas salvo la de nulos, que no aplica porque Fiscalía no tiene ninguno.
