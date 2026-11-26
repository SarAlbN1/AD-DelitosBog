# AD-DelitosBog · Segunda entrega

> **Este documento ya no describe el proyecto.** Se escribió en #8, antes de las decisiones D-01 y
> D-04 y antes del hallazgo de #86, y sus cifras contradicen lo vigente. Se conserva como índice:
> cada sección remite abajo a su fuente actual. **No lo use como referencia de nada** (#102).

## Dónde está ahora cada sección

| Sección | Fuente vigente |
|---|---|
| 5. Preprocesamiento | [`Informe/secciones/05_preprocesamiento.tex`](../Informe/secciones/05_preprocesamiento.tex), generado desde `scripts/preprocesamiento.py` y `outputs/preprocesamiento/` |
| 6. Análisis exploratorio | [`EDA_HALLAZGOS.md`](EDA_HALLAZGOS.md), generado desde `scripts/eda.py` y `outputs/eda/` |
| 7. Metodología | [`METODOLOGIA.md`](METODOLOGIA.md), con los comparadores de `scripts/baselines.py` y `outputs/baselines/` |
| Decisiones que mandan sobre todo lo anterior | [`decisiones.md`](decisiones.md) |

## Qué cambió respecto a lo que decía este documento

No son matices de redacción: cambió la serie que se modela y cambió el protocolo.

| Lo que decía | Lo vigente | Por qué |
|---|---|---|
| Serie del agregado de MinDefensa, 2.922 días, 2018–2025 | Registro de la Policía, **2.131 días**, 2020-01-01 a 2025-10-31 | D-01 fija el registro como población, y el agregado solo tiene 2.922 filas. #86 recorta noviembre y diciembre de 2025 |
| Línea base única, `cantidad[t−7]` | La barra es **el mejor de los cuatro comparadores** sobre el mismo conjunto de evaluación | El orden entre comparadores cambia con la ventana: el rezago 1 gana 4 de 6 pliegues (D-04) |
| Validación en tres bloques anuales: 2022, 2023, 2024 | Partición hasta 2025-04-30 y **seis pliegues de origen rodante** de 90 días | D-04 |
| Evaluación en las 365 fechas de 2025 | **184 días**, del 2025-05-01 al 2025-10-31 | La serie termina el 2025-10-31 (#86) |
| MAE y RMSE | MAE principal, RMSE, MAPE informativa y **MASE** | D-04 y #38. MASE es la única adimensional, así que compara entre ventanas |
| `LinearRegression` y `DecisionTreeRegressor` | Dos familias: SARIMA y ETS, y conjuntos de árboles. La regresión lineal quedó como trabajo futuro | `METODOLOGIA.md`, sección 5 |

## Lo que sí sigue vigente de este documento

### Pregunta de investigación y aporte

¿Cuánto mejora el pronóstico de hurtos registrados para el día siguiente en Bogotá al usar
calendario y rezagos frente a repetir lo trivial? El aporte es medir esa mejora con una línea base
explícita, un flujo reproducible y las mismas fechas de evaluación.

Con un matiz que la propia evidencia obligó a añadir: el documento proponía batir «el conteo del
mismo día de la semana anterior», y ese comparador **no es el más exigente**. De ahí la regla de
D-04 de calcular la barra sobre el conjunto en que se evalúa.

### Flujo CRISP-DM

| Fase | Aplicación |
|---|---|
| Comprensión del negocio | Estimar víctimas registradas para el día siguiente en Bogotá y describir la distribución territorial. |
| Comprensión de los datos | Verificar cobertura, unidades, calidad y patrones descriptivos de cada fuente. |
| Preparación de los datos | Limpiar, auditar y construir atributos temporales con Python y pandas; figuras con Matplotlib y mapas con GeoPandas. |
| Modelado | Ajustar las dos familias de `METODOLOGIA.md` y compararlas con los cuatro comparadores triviales. |
| Evaluación | Validación de origen rodante dentro del entrenamiento; evaluación final una sola vez, en los 184 días posteriores al corte. |
| Despliegue | Documentar cómo emitir el pronóstico con el calendario del día objetivo y los conteos disponibles al cierre del día anterior. |

### Una limitación que sigue sin resolverse

**La oportunidad de publicación de los datos no está verificada.** El protocolo supone que el conteo
del día `t−1` está disponible para predecir `t`, y eso es cierto en la evaluación retrospectiva
porque se usan conteos ya publicados. Para un uso operativo habría que comprobar con qué retraso
publica la Policía cada día, y eso no está medido.

El #86 no lo resuelve: concluye que noviembre y diciembre de 2025 **están incompletos o afectados
por un cambio de registro, y que la causa no está establecida**. Un retraso de consolidación es una
de las dos explicaciones compatibles, no un hecho demostrado. Así que el pendiente es medir el
retraso, no darlo por existente.

## Piezas trasladadas

Tres detalles de modelado de este documento pertenecen a la tercera entrega y quedan registrados en
sus issues, para no perderlos ni mantenerlos aquí:

| Pieza | Dónde queda |
|---|---|
| Rejilla del árbol: `max_depth` 3, 5 u 8; `min_samples_leaf` 7 o 14; desempate por menor profundidad y luego mayor hoja | #45, ajuste de hiperparámetros |
| Recortar las predicciones a cero como mínimo y conservar decimales para evaluar | #42, modelos de referencia |
| Omitir el indicador de fin de semana en los modelos, porque se deriva del día de la semana | #33, donde `features.py` lo produce |
