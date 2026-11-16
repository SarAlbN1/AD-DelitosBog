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
entrenamiento crece y nunca contiene días posteriores a los que evalúa. Es el esquema estándar para
series temporales y equivale a `TimeSeriesSplit` sin barajado.

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
| **MAPE** | `(100/n) Σ |yᵢ − ŷᵢ| / yᵢ` | Informativa. **Asimétrica**: castiga más la sobreestimación que la subestimación, así que no se usa para decidir |
| **MASE** | `MAE / MAE_ingenuo_estacional(entrenamiento)` | Adimensional. Menor que 1 mejora al ingenuo estacional; mayor que 1 lo empeora |

**Por qué MASE y no solo MAE.** MAE depende de la escala y de la ventana: un MAE de 49 no dice si es
bueno sin saber contra qué. MASE es un cociente, así que es comparable entre ventanas y entre
series, y su umbral es interpretable: **1 es el ingenuo estacional**. Es la métrica que Hyndman y
Koehler proponen precisamente para evitar los problemas de MAPE con valores pequeños y su asimetría.

**El denominador del MASE se calcula sobre el entrenamiento**, no sobre la evaluación. Si se
calculara sobre la evaluación, la métrica dependería del tramo que se quiere medir y dejaría de ser
comparable entre modelos evaluados en ventanas distintas. En esta serie el denominador es **53,20**.

> Pendiente: la referencia de Hyndman y Koehler (2006), *Another look at measures of forecast
> accuracy*, hay que añadirla a la bibliografía con el mismo proceso de verificación que las otras
> ocho (#24, #26). No se cita en el `.tex` hasta entonces.

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

**b. Series de tiempo estacionales: SARIMA y ETS.** Modelan explícitamente la estacionalidad
semanal, que es la señal dominante de la serie (viernes 403,1 frente a domingo 245,0). La
literatura local sobre hurto en Bogotá usa modelos de esta familia en series mensuales
\[garzon2025\], así que incluirlos permite situar el trabajo frente a ese antecedente, aunque aquí
la resolución es diaria.

**c. Conjuntos de árboles: Random Forest y potenciación del gradiente.** Capturan interacciones y no
linealidades entre calendario y rezagos sin especificarlas. Es la familia que mejor resultado dio
en el antecedente más cercano a este trabajo, un modelo espacio-temporal de hurto en Bogotá donde
Random Forest superó a los métodos estadísticos \[martinez2025\].

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
