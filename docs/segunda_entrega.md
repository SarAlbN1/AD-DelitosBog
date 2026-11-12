# AD-DelitosBog · Segunda entrega

Sara Albarracín y Juan Diego Rojas  
Analítica de Datos · Ingeniería de Sistemas · Pontificia Universidad Javeriana

## 5. Preprocesamiento de datos

La variable objetivo es el número de víctimas de hurto a personas registradas para una fecha en Bogotá. Se filtró el código municipal 11001 y el intervalo del 1 de enero de 2018 al 31 de diciembre de 2025. La unidad territorial es localidad–año. La unidad de Línea 123 es una fila agregada por mes, tipo y zona, con su propio campo de conteo.

| Fuente y corte | Filas | Suma del campo de conteo |
|---|---:|---:|
| MinDefensa nacional, toda la cobertura publicada | 654.716 | — |
| MinDefensa, CSV filtrado en el portal y verificado localmente | 2.922 | 975.793 víctimas |
| Capa distrital, 21 filas originales transformadas a localidad–año | 168 | 1.286.517 registros en los campos anuales |
| Línea 123, archivo bruto enero de 2015 a septiembre de 2026, todos los tipos | 1.117.394 | 33.079.787 incidentes |
| Línea 123, 2015–2025, todos los tipos | 1.044.332 | 31.098.079 incidentes |
| Línea 123, 2018–2025, todos los tipos | 763.074 | 20.996.584 incidentes |
| Línea 123, 2018–2025, categorías con la palabra «hurto» | 25.144 | 1.094.313 incidentes |

Las 2.922 filas, las 2.922 fechas únicas y las 975.793 víctimas de MinDefensa coinciden con la referencia. Los dos cortes históricos de Línea 123 también coinciden en número de filas. El umbral académico de un millón de filas depende de que el profesor acepte el volumen bruto de esta fuente complementaria. El pronóstico se construye con 2.922 observaciones diarias.

El CSV de MinDefensa presentó cero nulos, duplicados exactos, fechas duplicadas, fechas faltantes y conteos inválidos. Se convirtió la fecha al tipo temporal y se validó que los conteos fueran enteros no negativos. El flujo se detiene ante huecos, fechas duplicadas o conteos inválidos para resolverlos con la fuente. Se marcaron 26 días por encima del percentil 99 de 2018–2024 (587,44 víctimas). Todos conservaron su valor. La marca se usa para revisión descriptiva.

Para la fecha objetivo se derivaron mes, día de semana, indicador de fin de semana, rezagos de 1, 7 y 14 días y media de los siete días anteriores. La media desplaza la serie un día antes de calcular la ventana. Los primeros 1, 7 y 14 días quedan vacíos en sus respectivos rezagos y la media deja siete valores iniciales vacíos, pues esos días carecen de la historia requerida. Se conservan las fechas y se excluyen los primeros 14 días de la muestra común de modelado.

Los ocho campos territoriales, de `CMHP18CONT` a `CMHP25CONT`, se verificaron y pasaron a formato largo. Los conteos se mantuvieron en su escala anual, con Sin Localización como categoría aparte. Línea 123 presentó cero duplicados exactos y 2.633 repeticiones de ID en el archivo completo. Se conservaron las filas distintas porque el ID repetido por sí solo no establece que el registro sea un duplicado. Se verificaron los campos de mes, año, tipo, localidad y cantidad, con cero periodos o conteos inválidos.

## 6. Análisis exploratorio de datos

En Bogotá se registraron en promedio 333,95 víctimas diarias (mediana de 334,5). El máximo diario fue de 718 el 23 de septiembre de 2022. Octubre de 2022 tuvo el mayor total mensual, con 16.098 víctimas en 31 días. Abril de 2020 tuvo el menor, con 2.574 en 30 días. Los viernes tuvieron el mayor promedio diario por día de la semana (398,04) y los domingos el menor (230,96). La serie diaria, los totales mensuales y la comparación semanal se generan en el notebook 02.

En la capa territorial de 2025, Suba (10.149), Engativá (9.538) y Kennedy (8.906) encabezaron los conteos entre localidades. El total distrital de esa capa fue 99.665, con 4.406 en Sin Localización. El mapa de 2025 usa 20 polígonos válidos. El resumen anual incluye la categoría sin ubicación, que se deja fuera del mapa. Los conteos describen registros absolutos. Las fuentes se tabulan por separado porque sus totales difieren y esta entrega no ha reconciliado sus criterios de registro.

La exploración mensual de Línea 123 agrupa por código y nombre de tipo, y por código y nombre de localidad. Entre 2018 y 2025, el filtro textual encontró «HURTO EN PROCESO» (574.155 incidentes), «HURTO EFECTUADO» (328.546) y «ATRACO / HURTO EN PROCESO» (191.612). La tabla conserva las etiquetas del archivo, incluso cuando dos etiquetas comparten el código 905. Estos conteos corresponden a trámites de Línea 123 y se presentan en una gráfica separada.

## 7. Metodología

### Comprensión del problema y aporte

¿Cuánto mejora el pronóstico de hurtos registrados para el día siguiente en Bogotá al usar calendario y rezagos frente a repetir el conteo del mismo día de la semana anterior?

Frente a los antecedentes sobre patrones espaciales, aprendizaje automático y pronóstico econométrico descritos en el encargo, el aporte es medir esa mejora con una línea base explícita, un flujo reproducible y las mismas fechas de evaluación. La distribución de conteos anuales entre localidades es una pregunta descriptiva complementaria.

### Flujo CRISP-DM

| Fase | Aplicación |
|---|---|
| Comprensión del negocio | Estimar víctimas registradas para el día siguiente en Bogotá y describir la distribución anual por localidad. |
| Comprensión de los datos | Verificar cobertura, unidades, calidad y patrones descriptivos de cada fuente. |
| Preparación de los datos | Usar Python y pandas para limpiar, auditar, construir atributos temporales y calcular estadística descriptiva. Usar Matplotlib para las figuras y GeoPandas para leer y mapear los polígonos. |
| Modelado | Usar scikit-learn para ajustar regresión lineal y árbol de regresión y compararlos con el rezago semanal. |
| Evaluación | Validar cronológicamente en 2018–2024, fijar el protocolo y evaluar en 2025. |
| Despliegue | Documentar cómo emitir el pronóstico con el calendario del día objetivo y los conteos disponibles al cierre del día anterior. Verificar la oportunidad de publicación antes de una aplicación operativa. |

### Protocolo predictivo para la tercera entrega

1. **Horizonte y disponibilidad.** Para predecir el día `t`, usar su calendario y conteos de fechas hasta `t−1`. Evaluar retrospectivamente con los conteos históricos publicados. Registrar que la disponibilidad operativa al cierre de cada día aún debe verificarse.
2. **Comparadores.** La línea base devuelve `cantidad[t−7]`. La regresión lineal usa `LinearRegression` con mes y día de semana codificados como categorías, más los tres rezagos y la media previa. El árbol usa `DecisionTreeRegressor(random_state=42)` con las mismas entradas. El indicador de fin de semana queda disponible para exploración y se omite en los modelos porque se deriva del día de semana. Ajustar la codificación dentro de un `Pipeline` por partición. Recortar las predicciones de los modelos a cero como mínimo y conservar sus decimales para evaluar.
3. **Validación.** Usar tres bloques anuales de validación, 2022, 2023 y 2024. Para cada bloque, entrenar desde 2018 hasta el 31 de diciembre del año anterior. Mantener los parámetros de la regresión lineal y elegir para el árbol `max_depth` entre 3, 5 y 8, y `min_samples_leaf` entre 7 y 14. Seleccionar por MAE sobre todas las fechas de validación combinadas. En caso de empate, elegir menor profundidad y luego mayor tamaño mínimo de hoja. Conservar el histórico previo al inicio de cada bloque para construir rezagos. Usar las mismas fechas objetivo en los tres comparadores.
4. **Evaluación final.** Fijar atributos, hiperparámetros y reglas después de validar. Reentrenar con 2018–2024 y mantener los parámetros fijos en las 365 fechas de 2025. Avanzar un día a la vez usando el conteo observado del día anterior cuando ya pertenece al pasado del pronóstico. La exploración de 2025 en esta entrega es descriptiva. Las decisiones de ajuste se restringen a 2018–2024.
5. **Métricas.** Reportar MAE como promedio de los errores absolutos y RMSE como raíz del promedio de los errores cuadrados. Ambas métricas se expresan en víctimas por día. Reportar la mejora de MAE como `MAE_base − MAE_modelo` y su porcentaje como `100 × (MAE_base − MAE_modelo) / MAE_base` cuando el MAE de la base sea positivo. Comparar con fechas idénticas y reportar la cobertura.

La comparación final y los resultados predictivos se producirán en la tercera entrega.
