# Guía de sustentación · Hurto a personas en Bogotá, 2020–2025

Guía para preparar la exposición de la tercera entrega. Cada cifra sale del informe (`Informe/informe.tex`) y de los archivos de `outputs/` que lo sostienen. Si una pregunta pide un dato que no está aquí ni en el informe, la respuesta correcta es decirlo, no estimarlo en el momento.

El guion y los tiempos de la sección 3 se generan desde las notas de las diapositivas (`npm run guia`). Es el mismo texto que aparece en el panel de notas de la presentación (tecla **N**).

---

## 1. Resumen ejecutivo

**Problema.** ¿La historia del hurto a personas en Bogotá permite anticipar cuántas víctimas registrará la Policía al día siguiente con menos error que una regla ingenua? Se pronostica el **registro**: el hurto que no se denuncia no está en la serie.

**Datos.** El registro de la Policía Nacional tiene 741.986 filas de hurto a personas en Bogotá para 2020–2025, una víctima por fila. Esas filas sostienen el mínimo de 500.000 registros (D-01). Agregadas por día dan una serie de 2.131 días, del 2020-01-01 al 2025-10-31, con 730.870 víctimas y una media de 343,0 por día. Noviembre y diciembre de 2025 se excluyen porque el registro cae a la mitad sin que lo haga la Línea 123. La Línea 123 y la Fiscalía son complementarias: se comparan, no se suman.

**Método.**
- La partición es temporal. El entrenamiento va hasta el 2025-04-30; la evaluación final son 184 días, de mayo a octubre de 2025, y se calcula una sola vez.
- Los hiperparámetros se eligen en seis pliegues de origen rodante de 90 días (540 fechas).
- La barra a superar es el mejor de cuatro comparadores triviales: el ingenuo estacional, que repite el valor de hace una semana, con un MAE de 49,04.
- Se comparan cinco modelos: SARIMA, ETS, regresión lineal ridge, bosque aleatorio y gradiente por histogramas.
- La prueba de Diebold-Mariano dice si las diferencias superan el azar de una sola ventana.

**Resultado.**
- Los cinco modelos bajan el MAE de la barra:
  - SARIMA, ETS y los árboles, a entre 32,72 y 34,22, entre un 30 y un 33 % menos, con p < 10⁻⁷;
  - la regresión, a 36,31, un 26 % menos (p = 7·10⁻⁶).
- La mejora se repite en los seis pliegues y no depende de cómo se trate 2020.
- Entre los cuatro mejores no hay un ganador: los valores p van de 0,17 a 0,91.
- Los modelos se apoyan en el ciclo semanal, el festivo y el nivel del día anterior.

**Límite principal.** La evaluación final no incluye noviembre a enero, cuando el ciclo semanal se rompe; en los pliegues que cubren esa temporada el MAE llega a 44,61. El pronóstico es de toda la ciudad, a un día y sin intervalos de predicción.

---

## 2. Reparto y uso de la presentación

| Bloque | Diapositivas | Expone |
|---|---|---|
| Apertura, contexto, planteamiento, objetivos, auditoría | 1–6 | Juan Diego |
| Serie, análisis exploratorio, fuentes, territorio | 7–10 | Sara |
| Fundamentos, validación, métricas, modelos | 11–14 | Sara |
| Arquitectura, decisiones, resultados, validación, interpretación, limitaciones | 15–23 | Juan Diego |
| Conclusiones | 24 | Ambos |
| Trabajo futuro, referencias, preguntas | 25–27 | Sara y ambos |

El reparto sigue la responsabilidad de cada uno en el proyecto (`CLAUDE.md`). Pueden cambiarlo; si lo hacen, actualicen el campo `expone` de cada diapositiva y ejecuten `npm run guia`.

**Atajos durante la exposición:** → o Espacio avanzan; ← retrocede; **Inicio**/**Fin**; **F** pantalla completa; **N** notas; **O** índice para saltar a una diapositiva durante las preguntas. En la diapositiva 18 hay botones para cambiar el modelo que se superpone a lo observado (gradiente, ETS o regresión).

---

## 3. Guion de exposición

<!-- guion:inicio -->

### Tiempos por diapositiva

Duración total sugerida: **36:30 min**, sin contar las preguntas.

| # | Diapositiva | Expone | Duración | Empieza en |
|---|---|---|---|---|
| 1 | Apertura · Portada | Ambos | 0:30 | 0:00 |
| 2 | Contexto · Tres fuentes, tres unidades | Juan Diego | 1:30 | 0:30 |
| 3 | Planteamiento · Pregunta de investigación | Juan Diego | 1:30 | 2:00 |
| 4 | Justificación · Justificación y alcance | Juan Diego | 1:00 | 3:30 |
| 5 | Objetivos · Objetivos | Juan Diego | 1:00 | 4:30 |
| 6 | Datos · Auditoría y embudo | Juan Diego | 1:30 | 5:30 |
| 7 | Datos · Serie objetivo | Sara | 1:30 | 7:00 |
| 8 | Análisis exploratorio · Ciclo semanal y festivos | Sara | 1:30 | 8:30 |
| 9 | Análisis exploratorio · Las fuentes no se suman | Sara | 1:15 | 10:00 |
| 10 | Análisis exploratorio · Territorio: número frente a tasa | Sara | 1:15 | 11:15 |
| 11 | Fundamentos · Pronóstico de un paso y fuga | Sara | 1:30 | 12:30 |
| 12 | Metodología · Origen rodante y evaluación final | Sara | 1:30 | 14:00 |
| 13 | Metodología · Métricas y barra | Sara | 1:30 | 15:30 |
| 14 | Modelos · Cinco familias de modelos | Sara | 2:00 | 17:00 |
| 15 | Implementación · Arquitectura y reproducibilidad | Juan Diego | 1:45 | 19:00 |
| 16 | Decisiones · Decisiones y justificaciones | Juan Diego | 1:45 | 20:45 |
| 17 | Resultados · Comparación con la barra | Juan Diego | 2:00 | 22:30 |
| 18 | Resultados · Pronóstico frente a observado | Juan Diego | 1:15 | 24:30 |
| 19 | Validación · Estabilidad en los pliegues | Juan Diego | 1:30 | 25:45 |
| 20 | Validación · Diebold-Mariano entre modelos | Juan Diego | 1:30 | 27:15 |
| 21 | Resultados · Errores en festivos | Juan Diego | 1:15 | 28:45 |
| 22 | Interpretación · Importancia por permutación | Juan Diego | 2:00 | 30:00 |
| 23 | Limitaciones · Limitaciones | Juan Diego | 1:30 | 32:00 |
| 24 | Conclusiones · Conclusiones | Ambos | 1:30 | 33:30 |
| 25 | Trabajo futuro · Trabajo futuro | Sara | 1:00 | 35:00 |
| 26 | Referencias · Referencias | Ambos | 0:15 | 36:00 |
| 27 | Cierre · Preguntas | Ambos | 0:15 | 36:15 |

### Guion por diapositiva

#### 1. Portada · Ambos · 0:30

Buenos días. Somos Juan Diego Rojas y Sara Albarracín, y presentamos la tercera entrega del proyecto de Analítica de Datos.

La pregunta del título es literal: queremos saber si la historia del hurto a personas en Bogotá permite anticipar cuántas víctimas registrará la Policía al día siguiente.

Las dos cifras de la derecha son la serie con la que trabajamos: 730.870 víctimas en 2.131 días, de enero de 2020 a octubre de 2025.

**Enfatizar:**

- Se pronostica el registro de la Policía, no el hurto ocurrido.
- La serie termina el 31 de octubre de 2025, y más adelante explicamos por qué.

**Transición:** _Antes de hablar de modelos, hay que entender de dónde salen los datos._

#### 2. Tres fuentes, tres unidades · Juan Diego · 1:30

En Bogotá hay tres fuentes oficiales públicas sobre hurto, y cada una cuenta una cosa distinta.

La Policía publica una fila por víctima, con la fecha exacta del hecho, pero solo identifica el municipio. Es la única con resolución diaria y la que sostiene el requisito de 500.000 registros.

La Línea 123 publica conteos mensuales de llamadas tramitadas por localidad y UPZ. Es la única que permite mirar el territorio, pero mide demanda de atención, no hechos.

La Fiscalía publica pares proceso–delito por mes. Un proceso puede repetirse en varias filas, así que tampoco son víctimas ni hechos.

**Enfatizar:**

- Sumar las tres fuentes contaría varias veces el mismo hecho: se comparan en la escala común, mes por Bogotá, pero no se suman.
- Ninguna combinación de fuentes permite construir una serie diaria por localidad.

**Transición:** _Con esa restricción en mente, la pregunta queda así._

#### 3. Pregunta de investigación · Juan Diego · 1:30

La pregunta principal tiene dos partes: identificar patrones temporales y pronosticar el número diario de víctimas con menos error que una línea base ingenua.

La pregunta complementaria es sobre las fuentes: qué diferencias de cobertura y registro impiden compararlas directamente.

A la derecha están las tres precisiones que hay que fijar desde el principio: qué se pronostica, qué no, y contra qué se compara.

**Enfatizar:**

- Un pronóstico de un día, de toda la ciudad, con la información disponible al cerrar el día anterior.
- La línea base no se elige a conveniencia: es el mejor de cuatro comparadores triviales.

**Transición:** _¿Por qué vale la pena responder esta pregunta, y hasta dónde llega?_

#### 4. Justificación y alcance · Juan Diego · 1:00

La justificación tiene tres frentes: social, tecnológico y académico.

Pero lo importante es el alcance. El proyecto mide cuánto se puede anticipar un conteo agregado; no anticipa delitos individuales ni sirve para decidir dónde patrullar.

La literatura sobre subregistro y equidad en Bogotá (Riascos y colegas, Urcuqui y colegas) muestra por qué estas precauciones no son decorativas.

**Enfatizar:**

- Las importancias de los modelos describen de qué información depende el pronóstico, no qué causa el hurto.

**Transición:** _Con ese alcance definimos cinco objetivos específicos._

#### 5. Objetivos · Juan Diego · 1:00

El objetivo general es analizar el hurto con varias fuentes y evaluar modelos de pronóstico diario.

Los cinco objetivos específicos van de los datos al modelo. A la derecha está la evidencia de cada uno; el informe los da por cumplidos solo si hay una sección y un archivo de resultados que los respalden.

Dos matices: la serie se cortó en octubre de 2025 y el quinto objetivo se cumplió sin intervalos de predicción.

**Enfatizar:**

- Cada cifra de esta presentación sale de un archivo de outputs/ producido por un script.

**Transición:** _Empezamos por el primer objetivo: auditar los datos._

#### 6. Auditoría y embudo · Juan Diego · 1:30

El primer objetivo fue auditar. Para la Policía, el embudo parte de 4,8 millones de filas de todo el país.

Filtrando Bogotá quedan 1,4 millones; filtrando hurto a personas, 741.986. Ese número es el que sostiene el requisito de 500.000 registros.

Al restringir al periodo de la serie, que termina el 31 de octubre de 2025, quedan 730.870 víctimas.

La auditoría deja tres advertencias. La más llamativa: 713.344 filas son duplicados exactos, y no es un error. El archivo no trae identificador, así que dos víctimas con el mismo perfil el mismo día producen filas idénticas. Deduplicar dejaría 28.642 filas y destruiría la serie.

**Enfatizar:**

- Contamos filas en una sola unidad de observación: una víctima por fila.
- Cada archivo tiene su huella SHA-256 en el apéndice, para que cualquiera compruebe que usa los mismos datos.

**Transición:** _Con esos registros se construye la serie diaria._

#### 7. Serie objetivo · Sara · 1:30

Esta es la serie objetivo: la media diaria de víctimas por mes. La línea discontinua es la media de todo el periodo, 343 víctimas por día.

2020 cae por debajo de la mitad en abril, en las restricciones de movilidad. Su media anual es 227,1.

Después la serie sube hasta el pico de 2023, con 434,9 por día, baja en 2024 y se recupera en 2025.

Ese cambio de nivel es importante: los modelos tendrán que seguirlo, y veremos que lo hacen con el día anterior.

**Enfatizar:**

- 2020 no se elimina: entra con un indicador de año atípico y se prueba la sensibilidad sin él.
- Con un año truncado se comparan medias diarias, nunca totales.

**Transición:** _Dentro de cada semana aparece una regularidad mucho más fuerte._

#### 8. Ciclo semanal y festivos · Sara · 1:30

El hurto registrado sigue la actividad de la ciudad. El viernes es el día más alto, con 403 víctimas de media; el domingo, el más bajo, con 245. Es un 65 % más.

El festivo tiene una trampa: la Ley Emiliani pasa muchos festivos al lunes, que ya es un día bajo. Comparar festivo contra no festivo mezclaría los dos efectos. Por eso comparamos lunes con lunes: un lunes festivo registra un 37,8 % menos.

La estacionalidad por mes existe, pero es mucho más débil.

**Enfatizar:**

- El festivo es una variable que se conoce con años de antelación: no hay riesgo de fuga al usarla.
- Estas dos señales son la hipótesis que después contrastamos con lo que aprendieron los modelos.

**Transición:** _¿Y qué pasa cuando se ponen las tres fuentes una al lado de la otra?_

#### 9. Las fuentes no se suman · Sara · 1:15

Para comparar tendencias sin sumar conteos, cada fuente se expresa como índice de su propia media en los 70 meses comunes.

La Policía y la Fiscalía casi se superponen: correlación de 0,962. Son dos registros institucionales del mismo proceso.

La Línea 123 se separa: 0,601 con la Policía, y solo 0,284 si se quita 2020. Buena parte de la coincidencia era la caída compartida de la pandemia.

**Enfatizar:**

- Esto responde la pregunta complementaria: las fuentes no son intercambiables y cada una se usa en su resolución.

**Transición:** _La Línea 123 sí permite algo que las otras no: mirar el territorio._

#### 10. Territorio: número frente a tasa · Sara · 1:15

Por número de llamadas, Kennedy, Engativá y Suba encabezan la lista, pero son también las localidades más pobladas.

Al dividir por población el orden cambia por completo: Los Mártires pasa del puesto 14 al primero, con 3,7 veces la tasa de Kennedy. La Candelaria, penúltima por número, es cuarta por tasa.

El mapa muestra que las tasas altas se concentran en el centro.

**Enfatizar:**

- La tasa usa población residente y el centro recibe mucha población flotante: la tasa allí está sobrestimada.
- Ninguno de los dos órdenes mide peligrosidad ni dice nada de quienes viven en cada localidad.

**Transición:** _Hasta aquí, la descripción. Ahora, cómo se plantea el pronóstico._

#### 11. Pronóstico de un paso y fuga · Sara · 1:30

Formalmente, el problema es un pronóstico de un paso: la predicción de hoy es una función de la historia hasta ayer y del calendario de hoy.

Las 21 predictoras se agrupan en siete familias. El calendario se conoce de antemano; todo lo demás es pasado.

La validación cruzada habitual, que baraja los datos, no sirve aquí. Si se barajan los días, cada día de prueba tiene a sus vecinos en el entrenamiento, y con rezagos el modelo prácticamente ve la respuesta. El error saldría optimista.

Por eso usamos origen rodante: se entrena con el pasado y se predice lo que sigue. Y lo comprobamos con una prueba automática que altera el futuro y exige que el pronóstico no cambie.

**Enfatizar:**

- La fuga de información es el error más común en series de tiempo; aquí está bloqueada por diseño y por prueba.

**Transición:** _Así se organiza esa validación en el tiempo._

#### 12. Origen rodante y evaluación final · Sara · 1:30

Los datos hasta el 30 de abril de 2025 son entrenamiento. Los 184 días siguientes, de mayo a octubre de 2025, son la evaluación final, en rojo.

Dentro del entrenamiento hay seis pliegues de 90 días. Cada uno entrena con todo lo anterior a su origen y evalúa los 90 días siguientes; el entrenamiento crece de pliegue en pliegue.

Todos los hiperparámetros se eligen con el MAE de esas 540 fechas. La evaluación final se calcula una sola vez, al final, y no interviene en ninguna decisión.

**Enfatizar:**

- Separar elección y evaluación evita sobreajustar a la ventana de evaluación.
- Los pliegues además muestran la variabilidad: un buen resultado en una sola ventana no basta.

**Transición:** _¿Con qué medimos el error, y contra qué?_

#### 13. Métricas y barra · Sara · 1:30

La métrica principal es el MAE, porque se lee directamente: cuántas víctimas por día se equivoca el modelo.

El RMSE castiga más los errores grandes, y el MASE escala el error por el del ingenuo estacional dentro del entrenamiento, así que permite comparar ventanas.

A la derecha, los cuatro comparadores triviales. Ninguno usa información del día que predice. En la evaluación final, el mejor es el ingenuo estacional, que repite el valor de hace una semana: MAE de 49,04. Esa es la barra.

**Enfatizar:**

- La barra es el mejor comparador en el mismo conjunto de evaluación, no uno elegido de antemano.
- El MAPE no decide: no está acotado por arriba y castiga más la sobreestimación.

**Transición:** _Estos son los cinco modelos que compiten contra esa barra._

#### 14. Cinco familias de modelos · Sara · 2:00

Los modelos están ordenados de menor a mayor capacidad, para ver qué aporta cada salto.

SARIMA y ETS modelan la propia serie: representan el ciclo semanal con términos de periodo 7, pero no ven el calendario. Un festivo es para ellos un día normal.

La regresión lineal usa las 21 predictoras con penalización ridge. Es el modelo transparente: cada coeficiente se lee en víctimas.

El bosque aleatorio promedia 300 árboles; el gradiente por histogramas encadena árboles que corrigen el error de los anteriores. Los dos captan interacciones sin que haya que escribirlas.

La última columna dice cómo se eligió cada configuración, siempre en los pliegues. En SARIMA y ETS no se eligió un orden fijo, sino la regla con que se eligen los órdenes dentro de cada tramo.

**Enfatizar:**

- Todos pasan por la misma función de evaluación: mismos días, mismas métricas, misma barra.

**Transición:** _Ahora, cómo está construido todo esto por dentro._

#### 15. Arquitectura y reproducibilidad · Juan Diego · 1:45

Esta es la arquitectura del proyecto. A la izquierda, los datos originales y la configuración; en el centro, los scripts en el orden en que se ejecutan; a la derecha, los productos.

Lo importante es que no hay pasos a mano: cada cifra del informe sale de un archivo de outputs/ que produce un script.

Abajo están las cuatro garantías. Un solo arnés de evaluación, para que ningún modelo se evalúe en días distintos. 216 pruebas automáticas, 152 del modelado. Una huella por corrida: si dos corridas con la misma huella dan cifras distintas, el registro falla. Y una imagen de Docker.

¿Por qué Docker? Porque con la misma semilla y las mismas versiones, el gradiente por histogramas cambia hasta 0,7 de MAE entre macOS, Linux y Windows. Fijamos el entorno para que las cifras sean reproducibles.

**Enfatizar:**

- Antes de escribir sus tablas, comparacion.py recalcula cada métrica desde las predicciones guardadas y se detiene si alguna no coincide: así se cotejaron 616 cifras.

**Transición:** _Detrás de esa arquitectura hay decisiones que conviene justificar una por una._

#### 16. Decisiones y justificaciones · Juan Diego · 1:45

Siete decisiones condicionan los resultados. Las tres primeras son de datos y de evaluación, y se tomaron antes de entrenar ningún modelo.

La fuente es el registro de la Policía porque es la única con una fila por víctima y resolución diaria. El agregado de MinDefensa llega a 2018, pero tiene una fila por día: no sirve para el requisito de registros.

La barra se elige en la evaluación porque el mejor comparador cambia de una ventana a otra.

Y la interpretación usa permutación agrupada porque los rezagos de 7 y 14 días llevan casi la misma información: si se permuta solo uno, el modelo usa el otro y ambos parecen irrelevantes.

**Enfatizar:**

- Ninguna decisión se tomó después de ver la evaluación final.

**Transición:** _Con todo esto fijado, vamos a los resultados._

#### 17. Comparación con la barra · Juan Diego · 2:00

Este es el resultado principal. La línea discontinua roja es la barra: el ingenuo estacional, con 49,04 víctimas por día de error.

Los cinco modelos quedan muy por debajo. SARIMA, ETS y los dos árboles entre 32,72 y 34,22: entre un 30 y un 33 % menos. La regresión lineal, 36,31: un 26 % menos.

La columna p es la prueba de Diebold-Mariano contra la barra: compara día a día la pérdida de los dos pronósticos. En los cinco la diferencia es muy significativa, y se mantiene con pérdida cuadrática y con Newey-West.

En términos prácticos, el error es de alrededor del 10 % del valor diario, frente al 14 % de la barra.

**Enfatizar:**

- La evaluación final se calculó una sola vez, después de elegir todo con los pliegues.
- El MASE menor que 1 significa que el modelo se equivoca menos que repetir la semana anterior.

**Transición:** _Veamos qué significa eso día a día._

#### 18. Pronóstico frente a observado · Juan Diego · 1:15

Aquí están los 184 días. En negro lo observado, en azul el gradiente y en gris discontinuo la barra.

El modelo sigue el ciclo semanal. La barra, en cambio, repite con una semana de retraso cualquier día anómalo: se ven picos y caídas aislados que aparecen siete días tarde.

Las líneas verticales son los ocho festivos. Con los botones de arriba se puede cambiar a ETS o a la regresión.

**Enfatizar:**

- Mostrar ETS en un festivo: el modelo no baja, porque no sabe que es festivo.

**Transición:** _¿Y si la ventana de evaluación hubiera sido otra?_

#### 19. Estabilidad en los pliegues · Juan Diego · 1:30

Batir la barra en una sola ventana no basta. Aquí está el MAE en los seis pliegues.

Los cinco modelos ganan a la barra en los seis. Su peor pliegue, entre 35,49 y 44,61, queda muy por debajo del peor de la barra, 75,57.

También varían mucho menos: la desviación entre pliegues va de 4,34 a 7,46, frente a 14,11 de la barra.

El pliegue 5, noviembre a enero, es difícil para todos: los festivos de fin de año rompen el ciclo semanal.

**Enfatizar:**

- El orden de los modelos cambia entre pliegues y evaluación: otra razón para no hablar de un ganador.

**Transición:** _Precisamente: ¿hay un modelo ganador?_

#### 20. Diebold-Mariano entre modelos · Juan Diego · 1:30

Esta matriz compara los modelos entre sí. Cada celda es el valor p de la prueba de Diebold-Mariano para ese par.

Entre los cuatro primeros, los valores van de 0,17 a 0,91: ninguna diferencia es significativa.

La única celda en rojo es el gradiente frente a la regresión: 0,023. Pero con Newey-West sube a 0,073, y son diez comparaciones sin corregir por multiplicidad.

La conclusión honesta es que con estos 184 días no hay un ganador.

**Enfatizar:**

- Lo robusto no es el orden entre modelos, sino que todos superan la barra.

**Transición:** _Pero hay un tipo de día en que los modelos sí se separan._

#### 21. Errores en festivos · Juan Diego · 1:15

En los días no festivos, todos los modelos están entre 31 y 35 de MAE.

En los ocho festivos se separan. SARIMA y ETS se equivocan en 72 y 69, casi tanto como la barra, y sobrestiman en 56 y 59: no ven el calendario.

Los árboles bajan ese error a 37 y 43, aunque se pasan al otro lado y subestiman. La regresión queda en medio.

**Enfatizar:**

- Con solo ocho festivos la magnitud es imprecisa, pero el signo es claro y coincide con la estructura de cada modelo.

**Transición:** _¿En qué se apoyan los modelos para pronosticar?_

#### 22. Importancia por permutación · Juan Diego · 2:00

Para los árboles medimos la importancia por permutación: se desordena un grupo de variables entre los días y se mide cuánto sube el MAE. Si no sube, el modelo no dependía de ese grupo.

Tres hallazgos. Primero, el ciclo semanal es la señal principal, y cada modelo la toma por un camino distinto: el gradiente del día de la semana, el bosque de los rezagos de 7, 14 y 28 días.

Segundo, el día anterior pesa tanto como el ciclo semanal. El análisis exploratorio no lo destacó, pero sí lo anticipaba que el ingenuo de un día ganara cuatro pliegues: recoge el nivel reciente de la serie.

Tercero, los festivos pesan aunque sean solo 8 de 184 días.

A la derecha comprobamos el sentido: al marcar un lunes laborable como festivo, el gradiente baja su pronóstico un 37,3 %, casi exactamente el 37,8 % del análisis exploratorio.

**Enfatizar:**

- Importancia no es causa: que el modelo use el día anterior no significa que un día con muchos hurtos provoque otro.
- El indicador de 2020 da cero por construcción: en la evaluación vale cero en todos los días.

**Transición:** _Todo esto tiene límites que hay que decir con claridad._

#### 23. Limitaciones · Juan Diego · 1:30

Seis limitaciones, y conviene decirlas antes de que las pregunten.

La primera es la más importante: modelamos el registro. Riascos y colegas estiman para Bogotá precisamente esa brecha de subregistro; con nuestras fuentes no se puede observar.

La evaluación final va de mayo a octubre: no incluye la temporada de fin de año, donde el error sube.

No reportamos intervalos de predicción, porque los residuos conservan autocorrelación.

Y si un pronóstico así se usara para decidir dónde patrullar, podría reforzarse a sí mismo. El nuestro es de toda la ciudad, así que no concentra vigilancia en barrios, pero el riesgo no es nulo.

**Enfatizar:**

- Los resultados valen para Bogotá, 2020–2025, el registro de la Policía tal como se descargó y un horizonte de un día.

**Transición:** _Con esas precisiones, la respuesta a la pregunta._

#### 24. Conclusiones · Ambos · 1:30

La respuesta tiene dos partes.

Sí, los patrones temporales se identifican con claridad: un ciclo semanal fuerte, un efecto de festivo de casi el 38 % y un nivel que cambia de un año a otro.

Y sí, el pronóstico a un día supera la línea base: los cinco modelos bajan el error entre un 26 y un 33 %, en todos los pliegues y con o sin 2020. Pero no hay un modelo ganador.

La pregunta complementaria se responde con la auditoría: las fuentes no son intercambiables, así que se comparan sin sumarse.

Los cinco objetivos específicos están cumplidos, con la serie cortada en octubre de 2025 y sin intervalos de predicción.

**Enfatizar:**

- Que los modelos se apoyen en las mismas señales del análisis exploratorio da coherencia al resultado: no es una caja negra que acierta por casualidad.

**Transición:** _Lo que queda abierto lo convertimos en trabajo futuro._

#### 25. Trabajo futuro · Sara · 1:00

Cada propuesta ataca un límite concreto de los que acabamos de ver.

La más directa: dar a SARIMA los festivos como regresores externos, porque es exactamente su debilidad.

La más útil para un uso real: intervalos de predicción con cobertura medida y horizontes de 7 y 14 días.

Y la escala de localidad solo tendría sentido si la Policía publicara la localidad, y con salvaguardas.

**Enfatizar:**

- Nada de esto está implementado: son extensiones, no resultados.

**Transición:** _Estas son las referencias en que se apoya lo que presentamos._

#### 26. Referencias · Ambos · 0:15

No se lee. Se deja en pantalla mientras se pasa a preguntas.

**Enfatizar:**

- Las referencias metodológicas clave son Hyndman y Athanasopoulos (validación y MASE), Diebold y Mariano con Harvey et al. (comparación de pronósticos) y Breiman (bosques y permutación).

**Transición:** _Muchas gracias. Quedamos atentos a sus preguntas._

#### 27. Preguntas · Ambos · 0:15

Resumen en una frase: cinco modelos superan a la regla ingenua entre un 26 y un 33 %, sin un ganador entre ellos, y lo que se pronostica es el registro.

Para responder, volver con el índice (tecla O) a la diapositiva que corresponda.

**Enfatizar:**

- Si una pregunta pide una cifra que no está en el informe, decirlo: no improvisar resultados.

**Transición:** _Fin de la exposición._

<!-- guion:fin -->

### Versión corta (unos 20 minutos)

Si el tiempo es menor, mantengan el hilo pregunta → datos → protocolo → resultado → límites y condensen así:

- **Contexto y justificación (2 y 4):** en un minuto entre las dos.
- **Serie y patrones (7 y 8):** en una sola explicación.
- **Fuentes y territorio (9 y 10):** las dos correlaciones y el caso Kennedy frente a Los Mártires, en un minuto.
- **Fundamentos y validación (11 y 12):** decir por qué no se baraja y mostrar la línea de tiempo.
- **Arquitectura y decisiones (15 y 16):** solo las cuatro garantías y la decisión de la barra.
- **Pronóstico y festivos (18 y 21):** una frase cada una.
- **Trabajo futuro (25):** se menciona desde conclusiones.

No se recortan **3, 13, 17, 19, 20, 22, 23 y 24**: son las que sostienen la respuesta.

---

## 4. Conceptos que hay que dominar

**Pronóstico de un paso.** Predecir el valor de mañana (t) con la información disponible al cerrar hoy (t−1). El horizonte de un día es el único en que todas las predictoras están disponibles sin suponer nada sobre los retrasos de publicación (D-04).

**Fuga de información.** Un modelo que, al entrenarse o predecir, usa datos que no estarían disponibles en el momento del pronóstico. Con series de tiempo aparece al barajar los días, porque cada día de prueba queda rodeado de días de entrenamiento y los rezagos le muestran a sus vecinos. Se evita con validación temporal y se comprueba con la prueba `sin_fuga`: se altera la serie desde *t* en adelante y la predicción de *t* no puede cambiar.

**Validación de origen rodante.** Se entrena con todo lo anterior a un origen, se evalúan los 90 días siguientes y el origen avanza (Hyndman y Athanasopoulos, 2021). Aquí son seis pliegues, de noviembre de 2023 a abril de 2025. Sirve para elegir hiperparámetros sin tocar la evaluación final y para medir la variabilidad entre ventanas.

**MAE, RMSE, MAPE y MASE.**
- **MAE:** error absoluto medio, en víctimas al día. Es la métrica principal.
- **RMSE:** raíz del error cuadrático medio; penaliza más los errores grandes.
- **MAPE:** error porcentual. Es solo informativo porque es asimétrico: si el pronóstico se queda corto, el error no pasa del 100 %; si se pasa, no tiene cota.
- **MASE:** el MAE dividido por el MAE del ingenuo estacional dentro del entrenamiento (53,20). Menor que 1 significa mejor que repetir la semana anterior.

**Ingenuo estacional.** ŷₜ = yₜ₋₇: repite el valor del mismo día de la semana anterior. En la evaluación final es el mejor de los cuatro comparadores, y por eso es la barra.

**SARIMA.** Modelo autorregresivo integrado de media móvil, con términos estacionales.
- Con ADF (p = 0,091) y KPSS (p = 0,01) el nivel no es estacionario; la primera diferencia sí. De ahí sale d = 1.
- La fuerza estacional (STL) queda por debajo del umbral de 0,64. Por eso D = 0, y la estacionalidad semanal entra por los términos AR y MA estacionales de periodo 7.
- Los órdenes (p, q)(P, Q) se eligen por AIC en una malla de 9 × 3, dentro de cada tramo.
- La regla elegida en los pliegues es «desempate»: entre las candidatas a menos de 2 puntos de AIC, la más simple.

**ETS.** Suavizado exponencial con componentes de error, tendencia y estacionalidad. Se comparan cuatro configuraciones por AICc. La regla elegida en los pliegues fue «MAE interno»: elegir por el MAE de un paso en los últimos 90 días del tramo.

**Regresión lineal ridge.**
- Mínimos cuadrados con una penalización sobre el tamaño de los coeficientes.
- Usa las 21 predictoras, con día de la semana y mes en codificación one-hot, y escalado estándar.
- α = 0,1, elegido entre seis valores. Empata con α = 0 y gana por la regla de desempate (la más regularizada). Con unas 1.900 filas y 38 columnas apenas sobreajusta.

**Bosque aleatorio.** Promedio de 300 árboles, cada uno entrenado con una muestra con reemplazo y un subconjunto de variables en cada corte (Breiman, 2001). Ganó la configuración base de #44: hoja mínima 3, 50 % de las variables.

**Potenciación del gradiente por histogramas.** Árboles en secuencia, cada uno ajustado al error de los anteriores, con las variables discretizadas en histogramas para que sea rápido. Configuración elegida: 300 iteraciones, tasa de aprendizaje 0,05, profundidad 8, hoja mínima 7 y 15 hojas máximas.

**Prueba de Diebold-Mariano.**
- Para dos pronósticos, toma la diferencia diaria de sus pérdidas (aquí, el error absoluto) y contrasta si su media es cero.
- **HLN** (Harvey, Leybourne y Newbold, 1997) corrige la prueba para muestras pequeñas.
- **Newey-West** (1987), con 7 rezagos, estima la varianza teniendo en cuenta que los errores de días consecutivos están correlacionados; es la versión más conservadora.

**Importancia por permutación agrupada.**
- Se desordenan entre los días los valores de un grupo de variables y se mide cuánto sube el MAE. Si no sube, el modelo no dependía de ese grupo.
- Se agrupan variables porque las sustitutas, como los rezagos de 7 y 14 días, se suplen entre sí cuando se permutan por separado.
- Mide dependencia, no causalidad.

**Ljung-Box.** Contrasta si los residuos tienen autocorrelación. En los SARIMA y ETS de referencia la rechaza a 7, 14 y 28 rezagos (p < 0,001). Queda estructura sin modelar, y un intervalo de predicción que supusiera independencia sería demasiado estrecho.

---

## 5. Preguntas difíciles y respuestas

### Sobre los datos

**¿Por qué no usar 2018–2025, si el agregado de MinDefensa llega a 2018?**
Porque a nivel de registro la Policía solo publica 2020–2025. El agregado tiene una fila por día (2.922 en total): no sirve para el requisito de registros, y mezclar microdato y agregado en la misma serie cambiaría la unidad de observación. 2018 y 2019 se usan solo como contexto.

**¿Por qué no deduplicaron las 713.344 filas idénticas?**
Porque son víctimas distintas. El archivo no trae identificador, así que dos víctimas del mismo perfil el mismo día producen filas idénticas. La suma diaria coincide con el agregado de MinDefensa: exacta en 2020, 2021, 2022, 2023 y 2025, y con una unidad de diferencia en 2024. Deduplicar dejaría 28.642 filas.

**¿No es arbitrario cortar la serie en octubre de 2025?**
- Noviembre y diciembre caen un 51,6 % y un 49,1 % frente a la media de los diez meses anteriores. En los mismos meses, la Línea 123 se mueve +1,0 % y −5,4 %.
- La causa no está establecida: puede ser una consolidación incompleta o un cambio en el registro.
- Con esos meses dentro de la evaluación, un modelo parecería acertar una caída que no es del fenómeno.
- La decisión no depende de la causa, y está documentada en `docs/verificacion_caida_2025.md`.

**Si la Policía y la Fiscalía tienen correlación 0,962, ¿por qué no sumarlas para tener más datos?**
Porque cuentan cosas distintas: víctimas frente a pares proceso–delito. Probablemente parte de los mismos hechos aparece en las dos, así que sumarlas contaría dos veces. La correlación alta solo dice que se mueven juntas.

**¿Por qué la tasa por localidad no mide riesgo?**
- La Línea 123 cuenta llamadas tramitadas, que dependen de que alguien decida llamar.
- El denominador es la población residente, y las localidades del centro reciben mucha población flotante; por eso su tasa está sobrestimada.
- Los dos órdenes, por número y por tasa, describen dónde se pide atención, no dónde es más peligroso.

### Sobre el protocolo

**¿No hicieron trampa al elegir la barra con la evaluación final?**
No. Elegir el mejor de los cuatro comparadores en el mismo conjunto hace la barra más exigente, no más fácil. Si se fijara de antemano, podría quedar en el lugar equivocado: en los pliegues, el ingenuo gana cuatro de seis y el ingenuo estacional, solo dos.

**¿Cómo saben que no sobreajustaron la ventana de evaluación?**
- Toda elección (hiperparámetros, reglas de selección, regularización) se hizo con las 540 fechas de los pliegues.
- `ajuste.py` se detiene si recibe un día posterior al 2025-04-30.
- Una prueba altera los días de evaluación y exige que la selección no cambie.
- La evaluación final se calculó una sola vez.

**¿Por qué MAE y no MAPE para decidir?**
El MAE se lee en víctimas por día y trata igual los errores por exceso y por defecto. El MAPE castiga más la sobreestimación y su distribución se sesga cerca de cero (Hyndman y Koehler, 2006). Se reporta, pero no decide.

**¿Por qué no comparar los MAE directamente?**
Porque con una sola ventana de 184 días una diferencia de una o dos víctimas puede ser azar. Diebold-Mariano contrasta si la diferencia diaria de pérdidas tiene media cero, teniendo en cuenta su variabilidad.

### Sobre los modelos

**¿Por qué no redes neuronales (LSTM) o Prophet?**
No se evaluaron, y conviene decirlo así. La pregunta del proyecto era cuánto aportan calendario y rezagos frente a una regla ingenua, y la progresión elegida (series, regresión, árboles) ya la responde: los cuatro mejores empatan estadísticamente. Con unos 1.900 días de entrenamiento, un modelo con más capacidad tendría más riesgo de sobreajustar. Sería una extensión posible con el mismo protocolo y la misma barra.

**Son conteos: ¿por qué no un modelo de Poisson o binomial negativa?**
No se evaluaron. Con una media de 343 víctimas al día, los conteos están lejos de cero, y los modelos usados los tratan como continuos sin problema práctico. Una regresión de conteos sería una alternativa válida, comparable con el mismo arnés.

**¿Por qué ridge y no lasso?**
Ridge estabiliza los coeficientes cuando hay predictoras correlacionadas, como los rezagos y las variables de calendario, sin eliminar ninguna. En la práctica la regularización casi no importa hasta α = 100. Lasso no se evaluó.

**¿Por qué permutación y no SHAP?**
La permutación agrupada mide la dependencia en la misma unidad que el resultado (aumento del MAE) y permite agrupar variables sustitutas. SHAP no se usó. Daría una descomposición por predicción, pero no resolvería por sí solo el problema de las variables sustitutas.

**¿Qué modelo recomiendan?**
Con la evidencia disponible, ninguno destaca: entre los cuatro primeros los valores p van de 0,17 a 0,91. Si hubiera que elegir, un modelo con calendario tiene la ventaja en festivos. El informe deja la elección abierta y reporta el orden como propio de esta ventana.

**¿Por qué la regresión es segunda en los pliegues y última en la evaluación?**
Porque el orden cambia con la ventana; justamente por eso no se habla de ganador. En la evaluación, la regresión sobrestima mayo (sesgo de 28,51) y subestima los festivos (−30,70). Como no tiene interacciones, aplica el mismo efecto de festivo a cualquier día de la semana.

**¿Por qué el gradiente da cifras distintas en otro computador?**
Con las mismas versiones, el gradiente por histogramas cambia hasta 0,7 de MAE entre macOS, Linux y Windows, y la selección por AICc puede cambiar de candidata cuando hay casi empate. Por eso las cifras del informe se generan en una imagen de Docker con Python 3.12.8, versiones exactas y la arquitectura fijada. Las diferencias son de centésimas o décimas y no cambian ninguna conclusión.

### Sobre los resultados

**¿Un error de 33 víctimas al día es bueno?**
Es un 33 % menos que la mejor regla trivial y alrededor del 10 % del valor diario, frente al 14 % de la barra. Si alcanza para un uso concreto depende del uso. El proyecto no evalúa uso operativo: para eso faltarían intervalos de predicción y medir el retraso de publicación.

**Gradiente frente a regresión: p = 0,023. ¿No es significativo?**
- Con la corrección HLN, sí, al 5 %.
- Con la varianza de Newey-West, que tiene en cuenta la autocorrelación de los errores, sube a 0,073.
- Además son diez comparaciones sin corrección por multiplicidad.
- Por eso el informe dice que la regresión es la más débil sin que eso se pueda afirmar con solidez.

**¿Qué pasa si se quita 2020?**
El MAE final cambia entre −0,57 (gradiente, 32,15) y +0,79 (regresión, 37,10). Las cinco variantes siguen ganando a la barra en los seis pliegues. Ninguna conclusión depende de 2020.

**¿Por qué el indicador de 2020 tiene importancia cero?**
Por construcción: en la evaluación vale cero todos los días, así que permutarlo no cambia nada. Su papel es otro, decidir cómo usa el modelo los días de 2020 al entrenar, y eso se mide con la prueba de sensibilidad.

**¿El viernes «causa» más hurtos?**
No. El modelo depende del día de la semana para predecir; eso no dice qué produce el hurto. Una lectura compatible es que el hurto registrado acompaña la actividad de la ciudad, pero el proyecto no lo prueba.

**¿Por qué el día anterior importa tanto?**
Recoge el nivel reciente de la serie, que cambia de un año a otro y que el calendario no puede dar. Ya lo anticipaba la validación de los comparadores: el ingenuo de un día gana cuatro de los seis pliegues.

### Sobre el alcance y la ética

**¿Esto serviría para decidir dónde patrullar?**
- No está pensado para eso, y el modelo no puede hacerlo: pronostica un solo total diario para la ciudad.
- Ensign et al. (2018) muestran que un sistema que asigna policía por zonas y se actualiza con lo que esa misma policía descubre puede reforzarse a sí mismo.
- Los órdenes de la Línea 123 son descriptivos y no deberían usarse para asignar patrullaje.

**¿Cómo afecta el subregistro?**
Se modela el conteo oficial, no la victimización. Riascos Villegas et al. (2023) estiman esa brecha para Bogotá. Con nuestras fuentes no se puede observar, así que un buen pronóstico del registro no lo es necesariamente del hurto ocurrido.

**¿Cómo reproduzco una cifra?**
Con las instrucciones de `docs/REPRODUCIBILIDAD.md`: descargar las fuentes, verificar sus huellas SHA-256 (apéndice B del informe) y ejecutar los scripts en el orden indicado, con el modelado dentro de la imagen de Docker. `comparacion.py` recalcula cada métrica desde las predicciones guardadas; así se cotejaron 616 cifras.

---

## 6. Decisiones y su justificación

| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| Registro de la Policía como fuente de la variable objetivo (D-01) | Una víctima por fila, resolución diaria, 741.986 registros | Agregado de MinDefensa 2018–2025 |
| Serie hasta el 2025-10-31 | Noviembre y diciembre caen a la mitad sin que baje la Línea 123 | Evaluar sobre una caída que no es del fenómeno |
| Barra = mejor comparador en la evaluación (D-04) | El orden de los comparadores cambia con la ventana | Fijar el comparador de antemano |
| Horizonte de un día (D-04) | Todas las predictoras disponibles sin suponer retrasos | 7 o 14 días (trabajo futuro) |
| 2020 marcado, con sensibilidad | No se puede separar menos hechos de menos registro | Eliminar el año |
| Fuentes comparadas, no sumadas | Unidades de observación distintas | Una serie combinada |
| Una imagen de Docker | Cifras que dependen de la plataforma | Cifras de cualquier equipo |
| Permutación agrupada | Variables sustitutas | Permutación por variable |

---

## 7. Limitaciones que hay que reconocer sin esperar a que las pregunten

1. **Se pronostica el registro, no la victimización.**
2. **La evaluación final no cubre noviembre a enero.** En los pliegues de esa temporada el MAE de los modelos sube a entre 32,95 y 44,61.
3. **Un cambio en la forma de registrar se trasladaría al pronóstico** como si fuera un cambio real del hurto, porque los modelos aprenden el nivel desde el día anterior.
4. **No hay intervalos de predicción:** los residuos conservan autocorrelación.
5. **Hay un solo horizonte (un día) y una sola escala (toda la ciudad).**
6. **Una sola ventana de evaluación final.** Los pliegues dan la variabilidad, pero la cifra reportada son 184 días concretos.
7. **No se midió el retraso de publicación:** se supone que el dato de ayer está disponible hoy.
8. **La interpretación es parcial y no causal.** La permutación solo se aplica a los árboles, y la dependencia del gradiente respecto al día del mes queda sin explicar.

---

## 8. Cifras clave para tener a mano

| Cifra | Valor | Dónde |
|---|---|---|
| Registros de hurto a personas, Bogotá 2020–2025 | 741.986 | Sección 4, `outputs/auditoria_policia/` |
| Días y víctimas de la serie | 2.131 días · 730.870 víctimas · media 343,0 | Sección 4, `outputs/serie_objetivo/` |
| Viernes frente a domingo | +65 % (403,1 frente a 245,0) | Sección 6 |
| Lunes festivo frente a laborable | −37,8 % (201,5 frente a 323,9) | Sección 6 |
| Media diaria 2020 / 2023 / 2024 / 2025 | 227,1 / 434,9 / 356,6 / 368,1 | Sección 6 |
| Correlación Policía–Fiscalía / Policía–Línea 123 / sin 2020 | 0,962 / 0,601 / 0,284 | Sección 6 |
| Barra (ingenuo estacional) | MAE 49,04 · RMSE 61,44 · MASE 0,922 | Sección 7 |
| Gradiente / ETS / SARIMA / bosque / regresión | MAE 32,72 / 32,95 / 33,57 / 34,22 / 36,31 | Tabla de resultados, sección 9 |
| Mejora frente a la barra | −33,3 % a −26,0 % | Sección 9 |
| Peor pliegue de los modelos frente a la barra | 35,49–44,61 frente a 75,57 | Sección 9 |
| Desviación entre pliegues | 4,34–7,46 frente a 14,11 | Sección 9 |
| DM entre los cuatro mejores | p de 0,17 a 0,91 | Sección 9 |
| Gradiente frente a regresión | p = 0,023 (HLN) · 0,073 (Newey-West) | Sección 9 |
| MAE en festivos: SARIMA / ETS / bosque / gradiente | 72,41 / 68,81 / 36,68 / 42,73 | Sección 9 |
| Importancia del rezago de 1 día: gradiente / bosque | 39,2 % / 29,6 % | Sección 10 |
| Efecto del festivo en el gradiente frente al EDA | −37,3 % frente a −37,8 % | Sección 10 |

---

## 9. Ensayo

El criterio de aceptación de #56 es un ensayo con los tiempos medidos. Antes de cerrarla:

- [ ] Confirmar con el profesor la duración y si la presentación es obligatoria.
- [ ] Ensayar completa con cronómetro y anotar el tiempo real de cada bloque.
- [ ] Ajustar el campo `minutos` de las diapositivas a lo medido y regenerar la guía (`npm run guia`).
- [ ] Probar la presentación en el equipo y el proyector de la sustentación, con el PDF como respaldo.
