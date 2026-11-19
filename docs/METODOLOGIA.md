# Metodología (sección 7) · #38

Base de la sección 7 del informe. Las cifras salen de `scripts/baselines.py` y están en
`outputs/baselines/`.

## 1. El problema

**Tarea.** Pronóstico de un paso: predecir el número de víctimas de hurto a personas registradas en
Bogotá el día `t`, usando solo información disponible al cerrar `t-1`.

**Variable objetivo.** Víctimas diarias registradas por la Policía Nacional (D-01). Serie de 2.131
días, del 2020-01-01 al 2025-10-31, media 343,0.

**Horizonte.** Un día, `t+1` (D-04). Es el único horizonte en el que todas las predictoras están
disponibles sin supuestos adicionales sobre retrasos de publicación.

**Qué se predice y qué no.** La serie cuenta hurtos **registrados**, no hurtos ocurridos. El
subregistro es conocido y documentado en la literatura sobre criminalidad en Bogotá
\[riascos2023\], así que el modelo pronostica el conteo oficial y no la victimización real. Esta
distinción se mantiene en todo el informe.

## 2. Validación

**Partición fija, sin barajar.** Entrenamiento del 2020-01-01 al 2025-04-30 (1.947 días);
evaluación del 2025-05-01 al 2025-10-31 (184 días, media 366,8).

Una validación cruzada aleatoria sería **inválida** aquí: barajar los días pondría futuro en el
conjunto de entrenamiento, y con rezagos y medias móviles el modelo acabaría prediciendo un día
cuyos vecinos ya ha visto. El error resultante sería optimista y no mediría nada útil.

**Validación de origen rodante dentro del entrenamiento.** Seis pliegues de 90 días. Cada pliegue
entrena con todo lo anterior a su origen y evalúa el tramo siguiente, así que el conjunto de
entrenamiento crece y nunca contiene días posteriores a los que evalúa. Equivale a
`TimeSeriesSplit` sin barajado.

Es el esquema que Hyndman y Athanasopoulos llaman **evaluación con origen de pronóstico rodante**:
cada conjunto de prueba se pronostica solo con observaciones anteriores, de modo que no se usan
observaciones futuras \[hyndman2021\].

El conjunto de evaluación **no se toca** durante la selección de hiperparámetros. Se usa una sola
vez, al final.

| Pliegue | Entrena hasta | Evalúa hasta | Días de entrenamiento |
|---|---|---|---:|
| 1 | 2023-11-07 | 2024-02-05 | 1.407 |
| 2 | 2024-02-05 | 2024-05-05 | 1.497 |
| 3 | 2024-05-05 | 2024-08-03 | 1.587 |
| 4 | 2024-08-03 | 2024-11-01 | 1.677 |
| 5 | 2024-11-01 | 2025-01-30 | 1.767 |
| 6 | 2025-01-30 | 2025-04-30 | 1.857 |

## 3. Métricas

Con `y` el valor observado, `ŷ` la predicción y `n` los días evaluados:

| Métrica | Definición | Papel |
|---|---|---|
| **MAE** | `(1/n) Σ |yᵢ − ŷᵢ|` | **Principal.** Se lee en víctimas al día |
| **RMSE** | `√[(1/n) Σ (yᵢ − ŷᵢ)²]` | Secundaria. Penaliza más los errores grandes, que importan en los picos |
| **MAPE** | `(100/n) Σ |yᵢ − ŷᵢ| / yᵢ` | Informativa. **Asimétrica**: si `ŷ < y` el error porcentual no pasa del 100 %, y si `ŷ > y` no tiene cota, así que castiga más la sobreestimación. No se usa para decidir |
| **MASE** | `MAE / MAE_ingenuo_estacional(entrenamiento)` | Adimensional. Menor que 1 mejora al ingenuo estacional; mayor que 1 lo empeora |

**Por qué MASE y no solo MAE.** MAE depende de la escala y de la ventana: un MAE de 49 no dice si es
bueno sin saber contra qué. MASE es un cociente, así que es comparable entre ventanas y entre
series, y su umbral es interpretable: **1 es el ingenuo estacional**.

**Dos referencias, y no son intercambiables.** Hyndman y Koehler (2006) proponen el MASE y escalan
el error por el MAE del **ingenuo de un paso** dentro de la muestra, `|Yᵢ − Yᵢ₋₁|`
\[hyndman2006\]. Lo que este proyecto usa es la **versión estacional**, con denominador
`(1/(T−m)) Σ |yₜ − yₜ₋ₘ|` y `m = 7`, que es la que da Hyndman y Athanasopoulos (2021)
\[hyndman2021\]. Atribuir la variante estacional al artículo de 2006 sería inexacto.

De `hyndman2006` se toma además el motivo para no decidir con MAPE: los errores porcentuales son
infinitos o indefinidos si algún valor es cero, y su distribución se sesga mucho cuando los valores
se acercan a cero.

**El denominador del MASE se calcula sobre el entrenamiento**, no sobre la evaluación. Si se
calculara sobre la evaluación, la métrica dependería del tramo que se quiere medir y dejaría de ser
comparable entre modelos evaluados en ventanas distintas. En esta serie el denominador es **53,20**.

Las dos referencias están verificadas en `docs/verificacion_referencias.md` (#100) y entran en
`Informe/referencias.tex` cuando la sección 7 se integre en LaTeX (#39), porque APA solo lista las
obras citadas.

## 4. Modelos de referencia y la barra

Cuatro comparadores, ninguno con información de `t` ni posterior:

| Comparador | Definición |
|---|---|
| Ingenuo | `ŷ(t) = y(t−1)` |
| Ingenuo estacional | `ŷ(t) = y(t−7)`, el mismo día de la semana |
| Media móvil 7 | media de `t−1` a `t−7` |
| Media móvil 28 | media de `t−1` a `t−28` |

Resultados en el conjunto de evaluación (184 días):

| Comparador | MAE | RMSE | MAPE | MASE |
|---|---:|---:|---:|---:|
| Ingenuo | 52,92 | 68,41 | 15,62 % | 0,995 |
| **Ingenuo estacional** | **49,04** | **61,44** | **14,39 %** | **0,922** |
| Media móvil 7 | 49,42 | 61,86 | 14,59 % | 0,929 |
| Media móvil 28 | 55,83 | 70,72 | 16,75 % | 1,050 |

**La barra es el mejor de los cuatro sobre el mismo conjunto de evaluación** (D-04), no un
comparador elegido de antemano. Aquí es el ingenuo estacional: **MAE 49,04, RMSE 61,44, MASE
0,922**. Un modelo que no baje de esos valores no aporta nada sobre repetir el mismo día de la
semana anterior.

### El orden entre comparadores no es estable, y eso importa

MAE de cada comparador en los seis pliegues de la validación rodante:

| Pliegue | Ingenuo | Ingenuo estacional | Media móvil 7 | Media móvil 28 |
|---|---:|---:|---:|---:|
| 1 (nov 23 – feb 24) | **75,48** | 75,57 | 76,38 | 82,00 |
| 2 (feb – may 24) | **54,83** | 58,27 | 55,57 | 62,60 |
| 3 (may – ago 24) | 49,87 | **40,50** | 45,00 | 47,17 |
| 4 (ago – nov 24) | 54,93 | **43,09** | 50,59 | 51,30 |
| 5 (nov 24 – ene 25) | **52,63** | 69,68 | 57,19 | 77,52 |
| 6 (ene – abr 25) | **62,43** | 62,71 | 67,97 | 70,15 |

**El ingenuo gana 4 de los 6 pliegues**, pero en el conjunto de evaluación final gana el ingenuo
estacional. Dos consecuencias para el informe:

1. **Confirma la regla de D-04.** Fijar un comparador de antemano habría puesto la barra en el sitio
   equivocado en la mayoría de las ventanas. Calcularla sobre el conjunto que se evalúa lo resuelve.
2. **Superar la barra una vez no es un resultado robusto.** Si un modelo bate 49,04 en esta ventana,
   hay que decir en qué ventana lo hace y mostrar su comportamiento en los pliegues, no solo el
   número final.

El pliegue 5 explica el patrón: cubre noviembre, diciembre y enero, cuando los festivos y el
cambio de actividad de fin de año rompen la regularidad semanal, y ahí el ingenuo estacional es el
peor de los tres primeros. **La estacionalidad semanal es fuerte pero no constante a lo largo del
año**, y eso es justo lo que un modelo con calendario debería capturar mejor que un comparador fijo.

## 5. Familias de modelos propuestas

Tres familias, de menos a más capacidad, para que la comparación muestre qué aporta cada salto:

**a. Regresión lineal con rezagos y calendario.** El modelo transparente de referencia. Permite leer
los coeficientes y comprobar que las señales que el análisis exploratorio encontró —día de la
semana, festivo— entran con el signo esperado.

**b. Series de tiempo estacionales: SARIMA y ETS.** Se justifican por **la propia serie**, no por
la literatura local: la estacionalidad semanal es la señal dominante del análisis exploratorio
(viernes 403,1 frente a domingo 245,0, un 64 % de diferencia) y esta familia la modela de forma
explícita.

Conviene precisar que **ninguno de los antecedentes verificados usa SARIMA ni ETS**. El antecedente
local más cercano en series de tiempo, Garzón Acosta (2025), es de otra familia: usa un modelo de
corrección de errores frente a un VECM, con pruebas ADF, de Granger y de cointegración, sobre
series **mensuales** de ciudad \[garzon2025\]. Sirve para situar este trabajo frente a un
antecedente econométrico mensual, no para respaldar la elección de SARIMA.

**c. Conjuntos de árboles: Random Forest y potenciación del gradiente.** Capturan interacciones y no
linealidades entre calendario y rezagos sin especificarlas.

En el antecedente más cercano, un modelo espacio-temporal de hurto en Bogotá, **Random Forest
superó a una regresión de Poisson**: MAE 7,13 frente a 9,94 y RMSE 16,62 frente a 21,10
\[martinez2025\]. La comparación es contra ese modelo concreto, no contra «los métodos
estadísticos» en general, que es más de lo que el estudio establece.

Ese antecedente refuerza además una decisión de este trabajo por la vía contraria: **su partición
fue 80/20 y no se describe como temporal**. Con rezagos y medias móviles, una partición no temporal
deja futuro en el entrenamiento, así que sus métricas no son directamente comparables con las de
aquí, donde la evaluación es posterior al entrenamiento por construcción.

Esta progresión responde a la pregunta del proyecto, que no es «cuál es el mejor modelo posible»
sino **cuánto mejora el pronóstico al añadir calendario y rezagos** sobre lo trivial
\[provost2013\].

## 6. Prevención de fuga de información

Todas las predictoras cumplen la regla de disponibilidad de `scripts/features.py`: o son de
calendario, conocidas con años de antelación, o usan solo valores anteriores a `t`. La prueba de
`tests/test_features.py` lo comprueba perturbando la serie desde un día hacia adelante y exigiendo
que la fila de ese día no cambie (#33).

Quedan **excluidas explícitamente** como predictoras, con su motivo:

| Variable | Por qué |
|---|---|
| `fiscalia.a_o_creacion_proceso`, `mes_creacion_proceso` | El proceso puede abrirse meses después del hecho |
| `fiscalia.etapa` | Avanza con el tiempo transcurrido desde el hecho |
| `fiscalia.estado` | Refleja la situación de la investigación al momento de la consulta |
| `pico_revision` | Se calculaba con el percentil de la propia serie, incluido el futuro |
| Cualquier media centrada en `t` | Usa días posteriores a `t` |

## 7. Decisiones de datos que condicionan la evaluación

- **La serie termina el 2025-10-31.** Noviembre y diciembre de 2025 no son comparables (#86), y
  habrían caído justo en el conjunto de evaluación. Incluirlos habría hecho que cualquier modelo
  pareciera acertar un descenso que no ocurrió.
- **2020 entra marcado** con un indicador de año atípico (D-04), porque su nivel está deprimido por
  las restricciones de movilidad: media diaria 227,1 frente a 434,9 en 2023. Se comprueba la
  sensibilidad entrenando también sin ese año.
- **Las fuentes no se suman.** El modelo usa la serie de Policía. Línea 123 y Fiscalía se usan como
  contraste y contexto, en mes × Bogotá, que es la única resolución común.

## 8. Limitaciones

1. **Se pronostica registro, no victimización.** El subregistro no es observable con estas fuentes.
2. **Un paso, un horizonte.** No se evalúan horizontes más largos; hacerlo exigiría decidir qué
   predictoras siguen disponibles a `t+k`.
3. **Sin desglose territorial en la variable objetivo.** El registro de Policía no baja del
   municipio, así que el modelo es de ciudad. Cualquier análisis por localidad sale de Línea 123 y
   no de la serie que se modela.
4. **Una sola ventana de evaluación final.** Los pliegues rodantes dan idea de la variabilidad, pero
   el resultado que se reporta es de 184 días concretos.
