# Guion de la presentación · Hurto a personas en Bogotá, 2020–2025

- **Integrantes:** Juan Diego Rojas · Sara Albarracín
- **Duración planeada:** 23,75 min, sin las preguntas. El límite lo fija el profesor (por confirmar).
- **Fuentes:** `Informe/informe.tex` (main), la presentación de `presentacion/` (#162) y `GUIA_SUSTENTACION.md`
- **Cómo se calcula el tiempo:** 135 palabras por minuto, más 5 s por diapositiva y 3 s por acotación. Se regenera con `npm run guion`.

## Resumen de quién habla

| Bloque | Tema | Diapositivas | Quién | Tiempo |
|---|---|---|---|---|
| 1 | Introducción, pregunta y datos | 1–6 | Juan Diego | 5,25 min |
| 2 | Serie y análisis exploratorio | 7–10 | Sara | 4 min |
| 3 | Método: validación, métricas y modelos | 11–14 | Sara | 3,75 min |
| 4 | Implementación y decisiones | 15–16 | Juan Diego | 1,5 min |
| 5 | Resultados e interpretación | 17–22 | Juan Diego | 5,75 min |
| 6 | Limitaciones, conclusiones y cierre | 23–27 | Juan Diego → Sara → Ambos | 3,5 min |
|  | **Total** |  |  | **23,75 min** |

## Reglas para todos

- **Se pronostica el registro de la Policía, no el hurto ocurrido.** Decirlo siempre así: el hurto que no se denuncia no está en la serie.
- **Solo cifras del informe.** Leer las de la diapositiva, no las de memoria. Si preguntan algo que no se midió, se dice que no se midió.
- **Nunca decir que un modelo «gana».** Los cuatro mejores no se distinguen entre sí; lo sólido es que los cinco superan la barra.
- **Importancia no es causa.** Decir «el modelo depende de», nunca «causa» o «provoca».
- **Las fuentes se comparan, no se suman.** Policía, Línea 123 y Fiscalía cuentan cosas distintas.

---

## Parte 1 · Preparación (antes de exponer)

### 1.1 Instalación (una sola vez)

```bash
cd presentacion
npm install
npm run build
npm run preview      # abre la presentación en http://localhost:4173
```

### 1.2 Antes de empezar

1. **Juan Diego:** abrir la presentación con `npm run preview` en Chrome o Edge, ir a http://localhost:4173 y pulsar **F** para pantalla completa.
2. Tener abierto como respaldo el PDF `entregables/Presentacion_Proyecto.pdf`.
3. **Si el proyector duplica la pantalla, no abrir las notas (N):** se verían proyectadas. Usar este guion impreso o en otro dispositivo.
4. Probar en el equipo de la sala que → y el clic avanzan, y que los botones de la diapositiva 18 cambian el modelo.
5. Zoom del navegador al 100 % (Ctrl + 0): la presentación se escala sola a la pantalla.
6. Cada uno pasa sus propias diapositivas (→ o clic). Al cambiar de bloque se entrega el control con la frase de relevo.

### 1.3 Qué se hace en pantalla

| Diapositiva | Acción | Quién |
|---|---|---|
| 1 · Portada | Juan Diego: presentación en pantalla completa (tecla F) en la diapositiva 1. | Juan Diego |
| 2 · Tres fuentes, tres unidades | Señalar la tarjeta de la Policía. | Juan Diego |
| 2 · Tres fuentes, tres unidades | Señalar las tarjetas de la Línea 123 y de la Fiscalía. | Juan Diego |
| 3 · Pregunta de investigación | Señalar los tres recuadros de la derecha. | Juan Diego |
| 4 · Justificación y alcance | Señalar el recuadro rojo, «Fuera del alcance». | Juan Diego |
| 6 · Auditoría y embudo | Señalar las barras de arriba abajo. | Juan Diego |
| 6 · Auditoría y embudo | Señalar el recuadro «Tres advertencias de la auditoría». | Juan Diego |
| 7 · Serie objetivo | Señalar el sombreado de 2020. | Sara |
| 8 · Ciclo semanal y festivos | Señalar la barra azul del viernes y la roja del domingo. | Sara |
| 8 · Ciclo semanal y festivos | Señalar el recuadro del festivo. | Sara |
| 9 · Las fuentes no se suman | Señalar las líneas azul y ocre. | Sara |
| 9 · Las fuentes no se suman | Señalar la línea verde. | Sara |
| 10 · Territorio: número frente a tasa | Señalar las filas resaltadas: Los Mártires, La Candelaria y Kennedy. | Sara |
| 11 · Pronóstico de un paso y fuga | Señalar la fórmula y luego la tabla de predictoras. | Sara |
| 11 · Pronóstico de un paso y fuga | Señalar el diagrama de la derecha. | Sara |
| 12 · Origen rodante y evaluación final | Recorrer los pliegues de arriba abajo. | Sara |
| 13 · Métricas y barra | Señalar la tabla de comparadores y su fila resaltada. | Sara |
| 14 · Cinco familias de modelos | Señalar la última columna. | Sara |
| 15 · Arquitectura y reproducibilidad | Señalar las cuatro garantías de abajo. | Juan Diego |
| 16 · Decisiones y justificaciones | Señalar la última fila. | Juan Diego |
| 17 · Comparación con la barra | Señalar la línea discontinua roja. | Juan Diego |
| 17 · Comparación con la barra | Señalar la columna p de la tabla. | Juan Diego |
| 18 · Pronóstico frente a observado | Clic en el botón «ETS» y señalar una línea vertical de festivo. | Juan Diego |
| 18 · Pronóstico frente a observado | Clic en «Gradiente por histogramas» para volver. | Juan Diego |
| 19 · Estabilidad en los pliegues | Señalar la línea gris punteada de la barra. | Juan Diego |
| 20 · Diebold-Mariano entre modelos | Señalar la celda roja. | Juan Diego |
| 21 · Errores en festivos | Señalar las barras rojas de SARIMA y ETS. | Juan Diego |
| 22 · Importancia por permutación | Señalar las tres primeras barras. | Juan Diego |
| 22 · Importancia por permutación | Señalar la tabla de la derecha. | Juan Diego |
| 24 · Conclusiones | Señalar el recuadro azul. | Sara |
| 24 · Conclusiones | Señalar el recuadro verde. | Sara |
| 26 · Referencias | No se lee. Dejarla en pantalla unos segundos y pasar a la siguiente. | Sara |
| 27 · Preguntas | Durante las preguntas: tecla O para abrir el índice e ir a la diapositiva que corresponda. | Ambos |

### 1.4 Cuidados durante la exposición

- **Mientras se señala algo, se sigue hablando.** Las acotaciones van entre corchetes y no se leen en voz alta.
- **Si falla el navegador:** abrir el PDF a pantalla completa y seguir con el mismo texto. En la diapositiva 18 el PDF muestra solo el gradiente: se salta el clic y se dice «en ETS, en cambio, el pronóstico no baja en los festivos».
- **Si se acaba el tiempo:** las diapositivas 15 y 16 (arquitectura y decisiones) se reducen a una frase cada una. No se recortan las de resultados (17 a 22) ni la de limitaciones (23).
- **Durante las preguntas:** tecla **O** para abrir el índice y saltar a la diapositiva que corresponda. Las respuestas preparadas están en `GUIA_SUSTENTACION.md`.

---

## Parte 2 · Guion

### BLOQUE 1 · Introducción, pregunta y datos · 🎤 JUAN DIEGO · 5,25 min

#### ▶ Diapositiva 1 · _Portada_ · 0,75 min

**[Juan Diego: presentación en pantalla completa (tecla F) en la diapositiva 1.]**

> Buenos días, profesor. Somos Juan Diego Rojas y Sara Albarracín, y venimos a presentar la tercera entrega del proyecto de Analítica de Datos.
>
> Queremos saber si la historia del hurto a personas en Bogotá permite anticipar cuántas víctimas registrará la Policía al día siguiente, mejor que una regla sencilla.
>
> Trabajamos con 730.870 víctimas registradas en 2.131 días, de enero de 2020 a octubre de 2025.
>
> Antes de hablar de modelos, hay que entender de dónde salen esos datos.

#### ▶ Diapositiva 2 · _Tres fuentes, tres unidades_ · 1 min

> En Bogotá hay tres fuentes oficiales y públicas sobre hurto, y cada una cuenta una cosa distinta.

**[Señalar la tarjeta de la Policía.]**

> La Policía publica una fila por víctima con la fecha del hecho, pero sin la localidad. Es la única fuente diaria, y sus 741.986 registros cumplen por sí solos el requisito de 500.000.

**[Señalar las tarjetas de la Línea 123 y de la Fiscalía.]**

> La Línea 123 publica llamadas mensuales por localidad: permite mirar el territorio, pero mide demanda de atención, no hechos. Y la Fiscalía publica pares proceso–delito, donde un proceso puede repetirse.
>
> Por eso las tres fuentes se comparan, pero nunca se suman: sumarlas contaría varias veces el mismo hecho.
>
> Con esa restricción, la pregunta del proyecto queda así.

#### ▶ Diapositiva 3 · _Pregunta de investigación_ · 1 min

> Nuestra pregunta principal tiene dos partes: identificar los patrones temporales del hurto y pronosticar el número diario de víctimas registradas con menos error que una línea base ingenua.
>
> La pregunta complementaria es sobre las fuentes: qué diferencias de cobertura y de registro impiden compararlas directamente.

**[Señalar los tres recuadros de la derecha.]**

> Tres precisiones. Pronosticamos cuántas víctimas registrará la Policía mañana en toda la ciudad, con lo que se sabe hoy. No pronosticamos el hurto ocurrido: el que no se denuncia no está en la serie. Y un modelo solo aporta si se equivoca menos que repetir el mismo día de la semana anterior.
>
> ¿Por qué vale la pena responder esto, y hasta dónde llega?

#### ▶ Diapositiva 4 · _Justificación y alcance_ · 0,75 min

> La justificación tiene tres frentes: social, tecnológico y académico. Pero lo más importante de esta diapositiva es el alcance.

**[Señalar el recuadro rojo, «Fuera del alcance».]**

> Medimos cuánto se puede anticipar un conteo agregado de toda la ciudad. No anticipamos delitos individuales, no pronosticamos por localidad, porque la Policía no publica la localidad, y no recomendamos dónde patrullar.
>
> Un buen resultado estadístico no es evidencia causal ni justifica decisiones sobre comunidades concretas.
>
> Con ese alcance planteamos cinco objetivos específicos.

#### ▶ Diapositiva 5 · _Objetivos_ · 0,75 min

> El objetivo general es analizar el hurto con varias fuentes y evaluar modelos que pronostiquen el número diario de víctimas.
>
> Los cinco objetivos específicos van de los datos al modelo: auditar las fuentes, construir la serie, comparar las fuentes, implementar los modelos y evaluarlos contra la línea base.
>
> Los cinco están cumplidos, y a la derecha está la evidencia de cada uno. Hay dos matices que decimos de entrada: la serie se cortó en octubre de 2025 y la evaluación no incluye intervalos de predicción.
>
> Empiezo por el primero: la auditoría de los datos.

#### ▶ Diapositiva 6 · _Auditoría y embudo_ · 1 min

> Para la Policía, el embudo arranca con 4,8 millones de filas: todos los delitos del país en los archivos de 2020 a 2025.

**[Señalar las barras de arriba abajo.]**

> Con solo Bogotá quedan 1,4 millones; con solo hurto a personas, 741.986; y en el periodo de la serie, 730.870 víctimas.

**[Señalar el recuadro «Tres advertencias de la auditoría».]**

> Lo más llamativo: 713.344 filas son duplicados exactos, y no es un error. El archivo no trae identificador, así que dos víctimas del mismo perfil el mismo día dan filas idénticas. Borrarlas dejaría 28.642 filas.
>
> Además, noviembre y diciembre de 2025 caen a la mitad sin que lo haga la Línea 123, y por eso se excluyen.
>
> Con esos registros construimos la serie diaria. Sara, ¿cómo se comporta?

---

### BLOQUE 2 · Serie y análisis exploratorio · 🎤 SARA · 4 min

#### ▶ Diapositiva 7 · _Serie objetivo_ · 1 min

> Gracias, Juan Diego. Esta es la serie que vamos a pronosticar, resumida como la media diaria de víctimas de cada mes. La línea punteada es la media de todo el periodo: 343 víctimas por día.

**[Señalar el sombreado de 2020.]**

> En abril de 2020, con las restricciones de movilidad, la serie cae por debajo de la mitad; ese año tiene una media de 227 víctimas al día. Luego sube hasta el pico de 2023, con 435, baja en 2024 y se recupera en 2025.
>
> Los modelos tendrán que seguir ese cambio de nivel. A 2020 no lo eliminamos: entra marcado como atípico, y las conclusiones no dependen de él.
>
> Dentro de cada semana aparece una regularidad mucho más fuerte.

#### ▶ Diapositiva 8 · _Ciclo semanal y festivos_ · 1 min

> El hurto registrado sigue la actividad de la ciudad.

**[Señalar la barra azul del viernes y la roja del domingo.]**

> El viernes es el día más alto, con 403 víctimas de media, y el domingo el más bajo, con 245: el viernes registra un 65 % más.

**[Señalar el recuadro del festivo.]**

> Con los festivos hay una trampa. En Colombia muchos festivos se trasladan al lunes, que ya es un día bajo, así que comparar festivo contra no festivo mezclaría los dos efectos. Por eso comparamos lunes con lunes: un lunes festivo registra un 37,8 % menos que uno laborable.
>
> La estacionalidad por mes existe, pero es mucho más débil. Estas dos señales, el día de la semana y el festivo, son las que después esperamos encontrar dentro de los modelos.
>
> Ahora pongamos las tres fuentes una al lado de la otra.

#### ▶ Diapositiva 9 · _Las fuentes no se suman_ · 1 min

> Para comparar las fuentes sin sumarlas, expresamos cada una como un índice de su propia media, en los 70 meses que tienen en común.

**[Señalar las líneas azul y ocre.]**

> La Policía y la Fiscalía casi se superponen: su correlación es de 0,962. Son dos registros institucionales del mismo proceso.

**[Señalar la línea verde.]**

> La Línea 123 se separa. Su correlación con la Policía es de 0,601, y si quitamos 2020 baja a 0,284: buena parte de la coincidencia era la caída compartida de 2020.
>
> Esto responde la pregunta complementaria: las fuentes no son intercambiables, y cada una se usa en la resolución que publica.
>
> Lo que sí permite la Línea 123 es mirar el territorio.

#### ▶ Diapositiva 10 · _Territorio: número frente a tasa_ · 1 min

> Si contamos llamadas, Kennedy, Engativá y Suba encabezan la lista, pero también son las localidades más pobladas.

**[Señalar las filas resaltadas: Los Mártires, La Candelaria y Kennedy.]**

> Al dividir por población el orden cambia por completo. Los Mártires pasa del puesto 14 al primero, con 3,7 veces la tasa de Kennedy, y La Candelaria, penúltima por número, queda cuarta por tasa. En el mapa se ve que las tasas altas se concentran en el centro.
>
> Pero hay dos cuidados. La tasa usa la población residente, y el centro recibe mucha población flotante, así que ahí está sobrestimada. Y ninguno de los dos órdenes mide peligrosidad: describen dónde se pide atención.
>
> Hasta aquí la descripción. Ahora, cómo planteamos el pronóstico.

---

### BLOQUE 3 · Método: validación, métricas y modelos · 🎤 SARA · 3,75 min

#### ▶ Diapositiva 11 · _Pronóstico de un paso y fuga_ · 1 min

> Formalmente es un pronóstico de un paso: el valor de hoy se predice con la historia hasta ayer y con el calendario de hoy.

**[Señalar la fórmula y luego la tabla de predictoras.]**

> Usamos 21 predictoras en siete grupos: rezagos, medias recientes, día de la semana, festivos y calendario. El calendario se conoce de antemano; lo demás es pasado.

**[Señalar el diagrama de la derecha.]**

> Aquí no sirve barajar los datos: cada día de prueba quedaría rodeado de días de entrenamiento y, con rezagos, el modelo vería la respuesta. Por eso usamos origen rodante: se entrena con el pasado y se predice lo que sigue. Una prueba automática altera el futuro y exige que el pronóstico no cambie.
>
> Así se organiza esa validación en el tiempo.

#### ▶ Diapositiva 12 · _Origen rodante y evaluación final_ · 1 min

> Los datos hasta el 30 de abril de 2025 son el entrenamiento. Los 184 días siguientes, de mayo a octubre, son la evaluación final: la barra roja.

**[Recorrer los pliegues de arriba abajo.]**

> Dentro del entrenamiento hay seis pliegues de 90 días. Cada uno entrena con todo lo anterior y evalúa los 90 días siguientes, y el entrenamiento crece de pliegue en pliegue.
>
> Todos los hiperparámetros se eligen con el error en esas 540 fechas. La evaluación final se calcula una sola vez, al final, y no interviene en ninguna decisión. Así evitamos ajustar los modelos a la ventana con la que los juzgamos.
>
> ¿Con qué medimos el error, y contra qué?

#### ▶ Diapositiva 13 · _Métricas y barra_ · 0,75 min

> La métrica principal es el MAE: cuántas víctimas por día se equivoca el modelo. El RMSE castiga más los errores grandes, y un MASE menor que 1 significa que el modelo mejora al ingenuo estacional.

**[Señalar la tabla de comparadores y su fila resaltada.]**

> La barra no la elegimos a conveniencia: es el mejor de cuatro comparadores triviales en la misma evaluación. Ganó el ingenuo estacional, que repite el valor de hace una semana, con un MAE de 49,04 víctimas por día. Esa es la cifra que hay que batir.
>
> Y estos son los cinco modelos que compiten contra ella.

#### ▶ Diapositiva 14 · _Cinco familias de modelos_ · 1 min

> Los ordenamos de menor a mayor capacidad, para ver qué aporta cada salto.
>
> SARIMA y ETS modelan la propia serie: representan el ciclo semanal, pero no ven el calendario, así que para ellos un festivo es un día normal.
>
> La regresión lineal usa las 21 predictoras con una penalización ridge. Es el modelo transparente: cada coeficiente se lee en víctimas.
>
> El bosque aleatorio promedia 300 árboles, y el gradiente por histogramas encadena árboles que corrigen el error de los anteriores. Los dos captan interacciones sin que tengamos que escribirlas.

**[Señalar la última columna.]**

> Todos se eligieron en los pliegues y se evalúan con la misma función: mismos días, mismas métricas y misma barra.
>
> Juan Diego nos muestra ahora cómo está construido todo esto.

---

### BLOQUE 4 · Implementación y decisiones · 🎤 JUAN DIEGO · 1,5 min

#### ▶ Diapositiva 15 · _Arquitectura y reproducibilidad_ · 0,75 min

> Gracias, Sara. De izquierda a derecha: los datos, los scripts en el orden en que se ejecutan y los productos, el informe y el tablero de Power BI.
>
> Lo importante es que no hay pasos a mano. Cada cifra del informe sale de un archivo de outputs que produce un script.

**[Señalar las cuatro garantías de abajo.]**

> Cuatro garantías: un solo arnés de evaluación, 216 pruebas automáticas, una huella por corrida y una imagen de Docker, porque el gradiente cambia hasta 0,7 de MAE entre sistemas operativos.
>
> Detrás de esto hay decisiones que conviene justificar.

#### ▶ Diapositiva 16 · _Decisiones y justificaciones_ · 0,75 min

> Siete decisiones condicionan los resultados, y todas se tomaron antes de ver la evaluación final.
>
> La fuente es la Policía, la única diaria y por víctima. La barra se elige en la evaluación porque el mejor comparador cambia con la ventana. Y el horizonte es de un día, el único con todas las predictoras disponibles.

**[Señalar la última fila.]**

> Y en la interpretación permutamos grupos de variables, porque los rezagos de 7 y 14 días se suplen entre sí.
>
> Con todo esto fijado, vamos a los resultados.

---

### BLOQUE 5 · Resultados e interpretación · 🎤 JUAN DIEGO · 5,75 min

#### ▶ Diapositiva 17 · _Comparación con la barra_ · 1 min

**[Señalar la línea discontinua roja.]**

> Este es el resultado principal. La línea discontinua es la barra: 49,04 víctimas por día de error.
>
> Los cinco modelos quedan muy por debajo. SARIMA, ETS y los dos árboles, entre 32,72 y 34,22: entre un 30 y un 33 % menos. La regresión lineal, 36,31: un 26 % menos.

**[Señalar la columna p de la tabla.]**

> La columna p es la prueba de Diebold-Mariano, que compara día a día los errores de cada modelo con los de la barra. En los cinco la diferencia es muy significativa. En términos prácticos, el error es de alrededor del 10 % del valor diario, frente al 14 % de la barra.
>
> Veamos qué significa eso día a día.

#### ▶ Diapositiva 18 · _Pronóstico frente a observado_ · 0,75 min

> Aquí están los 184 días: en negro lo observado, en azul el gradiente y en gris punteado la barra.
>
> El modelo sigue el ciclo semanal. La barra, en cambio, repite una semana después cualquier día anómalo: por eso se ven picos y caídas sueltos que aparecen siete días tarde.

**[Clic en el botón «ETS» y señalar una línea vertical de festivo.]**

> Las líneas verticales son los ocho festivos. Si cambiamos a ETS, se ve que en el festivo no baja: no sabe que es festivo.

**[Clic en «Gradiente por histogramas» para volver.]**

> Pero una sola ventana podría engañar. ¿Qué pasa en otras?

#### ▶ Diapositiva 19 · _Estabilidad en los pliegues_ · 1 min

> Por eso repetimos la comparación en los seis pliegues de validación.

**[Señalar la línea gris punteada de la barra.]**

> Los cinco modelos le ganan a la barra en los seis. Su peor pliegue, entre 35 y 45, queda muy por debajo del peor de la barra, 75,57. Y varían mucho menos: su desviación va de 4 a 7,5, frente a 14 de la barra.
>
> El quinto pliegue, de noviembre a enero, es difícil para todos: los festivos de fin de año rompen el ciclo semanal. Y el orden de los modelos cambia entre los pliegues y la evaluación final: otra razón para no hablar de un ganador.
>
> Precisamente: ¿hay un modelo ganador?

#### ▶ Diapositiva 20 · _Diebold-Mariano entre modelos_ · 1 min

> Esta matriz compara los modelos entre sí. Cada celda es el valor p de la prueba de Diebold-Mariano para ese par.
>
> Entre los cuatro primeros, los valores van de 0,17 a 0,91: ninguna diferencia es significativa.

**[Señalar la celda roja.]**

> La única en rojo es gradiente contra regresión: 0,023. Pero con Newey-West, que corrige la correlación entre días seguidos, sube a 0,073, y son diez comparaciones sin corregir.
>
> Así que la conclusión honesta es que con estos 184 días no hay un ganador. Lo que sí se sostiene es que los cinco superan la barra.
>
> Hay un tipo de día, eso sí, en el que los modelos se separan.

#### ▶ Diapositiva 21 · _Errores en festivos_ · 0,75 min

> En los días normales, todos los modelos se equivocan entre 31 y 35 víctimas.

**[Señalar las barras rojas de SARIMA y ETS.]**

> En los ocho festivos se separan. SARIMA y ETS se equivocan en 72 y 69, casi tanto como la barra, y sobrestiman en más de 55 víctimas: no ven el calendario.
>
> Los árboles, que sí tienen la variable de festivo, bajan ese error a 37 y 43, aunque se pasan al otro lado y subestiman. Con solo ocho festivos la magnitud es imprecisa, pero el signo es claro y coincide con lo que ve cada modelo.
>
> ¿Y en qué se apoyan los modelos para pronosticar?

#### ▶ Diapositiva 22 · _Importancia por permutación_ · 1,25 min

> Para los árboles medimos la importancia por permutación: desordenamos un grupo de variables entre los días y medimos cuánto sube el error. Si no sube, el modelo no dependía de ese grupo.

**[Señalar las tres primeras barras.]**

> Tres hallazgos. El ciclo semanal es la señal principal: el gradiente la toma del día de la semana y el bosque, de los rezagos semanales. El día anterior pesa igual, porque recoge el nivel reciente. Y los festivos pesan aunque sean 8 de 184 días.

**[Señalar la tabla de la derecha.]**

> A la derecha comprobamos el sentido. Si marcamos un lunes laborable como festivo, el gradiente baja su pronóstico un 37,3 %, casi exactamente el 37,8 % que medimos en el análisis exploratorio.
>
> Una aclaración importante: esto describe de qué depende el pronóstico, no qué causa el hurto.
>
> Todo esto tiene límites que queremos decir con claridad.

---

### BLOQUE 6 · Limitaciones, conclusiones y cierre · 🎤 JUAN DIEGO → SARA → AMBOS · 3,5 min

#### ▶ Diapositiva 23 · _Limitaciones_ · 1 min

**🎤 JUAN DIEGO**

> La primera limitación es la más importante: modelamos el registro, no la victimización. El hurto que no se denuncia no está en la serie, y con nuestras fuentes no se puede medir.
>
> La evaluación no incluye la temporada de fin de año, donde el error sube. Un cambio en el registro se tomaría como un cambio real. No hay intervalos de predicción, porque los errores conservan autocorrelación. Y el pronóstico es de toda la ciudad y a un día.
>
> Y si se usara para decidir dónde patrullar, podría reforzarse a sí mismo; el nuestro no asigna barrios, pero el riesgo no es nulo.
>
> Sara, con esas precisiones, ¿cuál es la respuesta a la pregunta?

#### ▶ Diapositiva 24 · _Conclusiones_ · 1 min

**🎤 SARA**

> La respuesta tiene dos partes.

**[Señalar el recuadro azul.]**

> Primera: los patrones temporales se identifican con claridad. Hay un ciclo semanal fuerte, un efecto de festivo de casi el 38 % y un nivel que cambia de un año a otro.

**[Señalar el recuadro verde.]**

> Segunda: el pronóstico a un día supera la línea base. Los cinco modelos bajan el error entre un 26 y un 33 %, en todos los pliegues y con o sin 2020. Pero entre los cuatro mejores no hay un ganador.
>
> Y los modelos se apoyan en las señales del análisis exploratorio: no es una caja negra que acierta por casualidad.
>
> Lo que quedó abierto lo convertimos en trabajo futuro.

#### ▶ Diapositiva 25 · _Trabajo futuro_ · 0,75 min

> Cada propuesta ataca un límite concreto de los que vimos.
>
> La más directa es darle a SARIMA los festivos como variables externas, porque es exactamente su debilidad. La más útil para un uso real son los intervalos de predicción y los horizontes de 7 y 14 días. Y la escala de localidad solo tendría sentido si la Policía publicara la localidad, y con salvaguardas.
>
> Ninguna de estas extensiones está implementada.
>
> Ahí quedan las referencias en las que nos apoyamos.

#### ▶ Diapositiva 26 · _Referencias_ · 0,25 min

**[No se lee. Dejarla en pantalla unos segundos y pasar a la siguiente.]**

> Juan Diego cierra.

#### ▶ Diapositiva 27 · _Preguntas_ · 0,5 min

**🎤 AMBOS**

> En resumen: cinco modelos superan a la regla ingenua entre un 26 y un 33 %, ninguno se distingue de los demás, y lo que pronosticamos es el registro, no el hurto ocurrido.

**[Durante las preguntas: tecla O para abrir el índice e ir a la diapositiva que corresponda.]**

> Muchas gracias. Quedamos atentos a sus preguntas.

---

## Parte 3 · Registro del ensayo

Lo llena quien no está hablando, con cronómetro. Criterio: el límite que fije el profesor.

| Ensayo | Bloque 1 | Bloque 2 | Bloque 3 | Bloque 4 | Bloque 5 | Bloque 6 | Total |
|---|---|---|---|---|---|---|---|
| Planeado | 5,25 min | 4 min | 3,75 min | 1,5 min | 5,75 min | 3,5 min | 23,75 min |
| 1 |   |   |   |   |   |   |   |
| 2 |   |   |   |   |   |   |   |

Notas (qué se recortó y por qué):
