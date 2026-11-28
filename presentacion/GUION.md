# Guion de la presentación · Hurto a personas en Bogotá, 2020–2025

- **Integrantes:** Juan Diego Rojas · Sara Albarracín
- **Duración planeada:** 8,75 min de presentación + 5 min de Power BI = 13,75 min (límite: 10 + 5 = 15 min, preguntas aparte).
- **Fuentes:** `Informe/informe.tex` (main), la presentación de `presentacion/` (#162) y `GUIA_SUSTENTACION.md`
- **Cómo se calcula el tiempo:** 135 palabras por minuto, más 5 s por diapositiva y 3 s por acotación. Se regenera con `npm run guion`.

## Resumen de quién habla

| Bloque | Tema | Diapositivas | Quién | Tiempo |
|---|---|---|---|---|
| 1 | Introducción, pregunta y datos | 1–4 | Juan Diego | 2,5 min |
| 2 | Serie, validación y modelos | 5–9 | Sara | 2,75 min |
| 3 | Resultados, validación, interpretación y límites | 10–14 | Juan Diego → Sara → Juan Diego | 2,75 min |
| 4 | Conclusiones | 15 | Sara | 0,75 min |
| 5 | Demo del tablero de Power BI | 16 | Sara | 5 min |
| 6 | Preguntas | 17 | Ambos | el tiempo que quede |
|  | **Presentación (bloques 1–4)** |  |  | **8,75 min** |
|  | **Presentación + Power BI** |  |  | **13,75 min** |

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
2. **Sara:** abrir antes `powerbi/Tablero-DelitosBOG.pbip` en Power BI Desktop, con `RutaRepo` apuntando a la copia local del repositorio, pulsar **Actualizar** y dejarlo en la página Panorama, con el filtro en todos los años.
3. Tener la presentación y Power BI abiertos para pasar de uno a otro con **Alt + Tab**.
4. Tener abierto como respaldo el PDF `entregables/Presentacion_Proyecto.pdf`.
5. **Si el proyector duplica la pantalla, no abrir las notas (N):** se verían proyectadas. Usar este guion impreso o en otro dispositivo.
6. Cada uno pasa sus propias diapositivas (→ o clic). Al cambiar de bloque se entrega el control con la frase de relevo.

### 1.3 Qué se hace en pantalla

| Diapositiva | Acción | Quién |
|---|---|---|
| 1 · Portada | Juan Diego: pantalla completa (tecla F) en la diapositiva 1. | Juan Diego |
| 2 · Pregunta de investigación | Señalar los tres recuadros de la derecha. | Juan Diego |
| 4 · Auditoría y embudo | Señalar las barras de arriba abajo. | Juan Diego |
| 5 · Serie objetivo | Señalar el sombreado de 2020. | Sara |
| 6 · Ciclo semanal y festivos | Señalar el viernes y el domingo. | Sara |
| 7 · Origen rodante y evaluación final | Señalar los pliegues y luego la barra roja. | Sara |
| 8 · Métricas y barra | Señalar la fila resaltada de la tabla. | Sara |
| 10 · Comparación con la barra | Señalar la línea discontinua roja. | Juan Diego |
| 11 · Estabilidad en los pliegues | Señalar la línea gris de la barra. | Sara |
| 12 · Diebold-Mariano entre modelos | Señalar la celda roja. | Sara |
| 13 · Importancia por permutación | Señalar las tres primeras barras. | Juan Diego |
| 16 · Demo del tablero de Power BI | Sara: Alt + Tab a Power BI Desktop, ya abierto y actualizado, en la página Panorama. | Sara |
| 16 · Demo del tablero de Power BI | Panorama: señalar la serie mes a mes y la media diaria por año. | Sara |
| 16 · Demo del tablero de Power BI | Cambiar el filtro de año a 2023 y volver a todos los años. | Sara |
| 16 · Demo del tablero de Power BI | Página ¿Cuándo?: señalar el reparto por día y el mapa de calor día × mes. | Sara |
| 16 · Demo del tablero de Power BI | Página ¿Dónde?: señalar volumen frente a tasa y el mapa. | Sara |
| 16 · Demo del tablero de Power BI | Página Pronóstico: señalar lo observado frente al mejor modelo y el error por modelo. | Sara |
| 17 · Preguntas | Alt + Tab de vuelta a la presentación, en la diapositiva de preguntas. | Ambos |
| 17 · Preguntas | Para responder: tecla O e ir a la diapositiva que corresponda, incluido el anexo. | Ambos |

### 1.4 Cuidados durante la exposición

- **Los 10 minutos son la meta, no el promedio.** Si en el ensayo pasan de 10, se acorta el texto de las diapositivas 3 y 11, que son de apoyo.
- **Mientras se señala algo, se sigue hablando.** Las acotaciones van entre corchetes y no se leen en voz alta.
- **Si falla Power BI:** se dice «seguimos con las capturas» y se muestran las diapositivas del anexo con el mismo contenido: territorio (localidades) y pronóstico frente a observado. Las cifras son las mismas.
- **Si falla el navegador:** abrir el PDF a pantalla completa y seguir con el mismo texto.
- **Durante las preguntas:** tecla **O** para abrir el índice. El anexo tiene diapositivas de respaldo para las preguntas más probables; las respuestas preparadas están en `GUIA_SUSTENTACION.md`.

---

## Parte 2 · Guion

### BLOQUE 1 · Introducción, pregunta y datos · 🎤 JUAN DIEGO · 2,5 min

#### ▶ Diapositiva 1 · _Portada_ · 0,5 min

**[Juan Diego: pantalla completa (tecla F) en la diapositiva 1.]**

> Buenos días, profesor. Somos Juan Diego Rojas y Sara Albarracín. En diez minutos les contamos si la historia del hurto a personas en Bogotá permite anticipar cuántas víctimas registrará la Policía mañana, y después Sara les muestra el tablero de Power BI.
>
> Empiezo por la pregunta.

#### ▶ Diapositiva 2 · _Pregunta de investigación_ · 0,75 min

> La pregunta tiene dos partes: identificar los patrones temporales del hurto y pronosticar las víctimas del día siguiente con menos error que una regla ingenua.

**[Señalar los tres recuadros de la derecha.]**

> Tres precisiones: pronosticamos el registro de la Policía para toda la ciudad, no el hurto ocurrido; usamos solo lo que se sabe al cerrar el día; y un modelo solo aporta si se equivoca menos que repetir el mismo día de la semana anterior.
>
> ¿De dónde salen los datos?

#### ▶ Diapositiva 3 · _Tres fuentes, tres unidades_ · 0,5 min

> Hay tres fuentes oficiales, y cada una cuenta algo distinto. La Policía publica una víctima por fila, con la fecha del hecho pero sin localidad. La Línea 123 cuenta llamadas por localidad, y la Fiscalía, procesos judiciales.
>
> Por eso se comparan, pero nunca se suman. La Policía es la fuente principal: es la única diaria.
>
> Y estos son sus números.

#### ▶ Diapositiva 4 · _Auditoría y embudo_ · 0,75 min

**[Señalar las barras de arriba abajo.]**

> De 4,8 millones de filas de todo el país quedan 741.986 registros de hurto a personas en Bogotá, que cumplen por sí solos el requisito de 500.000. En el periodo de la serie son 730.870 víctimas.
>
> Dos advertencias: 713.344 filas son duplicados legítimos, porque el archivo no trae identificador; y noviembre y diciembre de 2025 caen a la mitad, así que se excluyen.
>
> Sara, ¿cómo se comporta la serie?

---

### BLOQUE 2 · Serie, validación y modelos · 🎤 SARA · 2,75 min

#### ▶ Diapositiva 5 · _Serie objetivo_ · 0,75 min

> Gracias, Juan Diego. Esta es la media diaria de víctimas por mes: 343 de media en todo el periodo.

**[Señalar el sombreado de 2020.]**

> En 2020, con las restricciones de movilidad, la serie cae a la mitad. Luego sube hasta el pico de 2023, con 435 víctimas diarias, y baja en 2024. Los modelos tendrán que seguir ese cambio de nivel; 2020 entra marcado como año atípico.
>
> Dentro de cada semana hay una regularidad más fuerte.

#### ▶ Diapositiva 6 · _Ciclo semanal y festivos_ · 0,5 min

**[Señalar el viernes y el domingo.]**

> El viernes registra un 65 % más víctimas que el domingo: el hurto registrado acompaña la actividad de la ciudad.
>
> Y un lunes festivo registra un 37,8 % menos que un lunes laborable. Comparamos lunes con lunes porque muchos festivos se trasladan al lunes. Estas son las dos señales que esperamos ver dentro de los modelos.
>
> ¿Cómo evaluamos esos modelos?

#### ▶ Diapositiva 7 · _Origen rodante y evaluación final_ · 0,5 min

> No barajamos los datos: con rezagos, el modelo vería la respuesta. Entrenamos con el pasado y predecimos lo que sigue.

**[Señalar los pliegues y luego la barra roja.]**

> Los hiperparámetros se eligen en seis pliegues de 90 días dentro del entrenamiento. Los últimos 184 días, de mayo a octubre de 2025, son la evaluación final, y se calcula una sola vez.
>
> ¿Y contra qué medimos el error?

#### ▶ Diapositiva 8 · _Métricas y barra_ · 0,5 min

> La métrica principal es el MAE: cuántas víctimas por día se equivoca el modelo.

**[Señalar la fila resaltada de la tabla.]**

> La barra es el mejor de cuatro comparadores triviales: el ingenuo estacional, que repite el valor de hace una semana, con 49,04 víctimas por día. Esa es la cifra que hay que batir.
>
> Estos son los cinco modelos que compiten.

#### ▶ Diapositiva 9 · _Cinco familias de modelos_ · 0,5 min

> SARIMA y ETS modelan la propia serie, con su ciclo semanal, pero no ven el calendario. La regresión lineal, el bosque aleatorio y el gradiente por histogramas usan 21 predictoras: rezagos, día de la semana, festivos y calendario.
>
> Todos se eligen en los pliegues y se evalúan en los mismos días, contra la misma barra.
>
> Juan Diego, ¿qué resultados dieron?

---

### BLOQUE 3 · Resultados, validación, interpretación y límites · 🎤 JUAN DIEGO → SARA → JUAN DIEGO · 2,75 min

#### ▶ Diapositiva 10 · _Comparación con la barra_ · 0,75 min

**🎤 JUAN DIEGO**

**[Señalar la línea discontinua roja.]**

> Gracias, Sara. La línea discontinua es la barra: 49,04. Los cinco modelos quedan muy por debajo. SARIMA, ETS y los árboles, entre 32,72 y 34,22: entre un 30 y un 33 % menos. La regresión, 36,31: un 26 % menos.
>
> La prueba de Diebold-Mariano confirma que la diferencia con la barra es significativa en los cinco. El error queda en torno al 10 % del valor diario.
>
> Sara, ¿y si la ventana hubiera sido otra?

#### ▶ Diapositiva 11 · _Estabilidad en los pliegues_ · 0,5 min

**🎤 SARA**

**[Señalar la línea gris de la barra.]**

> Gracias, Juan Diego. Los cinco modelos le ganan a la barra en los seis pliegues, y su peor pliegue queda muy por debajo del peor de la barra. La mejora no depende de una ventana concreta.
>
> Pero, ¿hay un modelo ganador?

#### ▶ Diapositiva 12 · _Diebold-Mariano entre modelos_ · 0,5 min

> No. Entre los cuatro mejores, la prueba de Diebold-Mariano da valores p entre 0,17 y 0,91.

**[Señalar la celda roja.]**

> La única diferencia es gradiente contra regresión, 0,023, y deja de ser significativa al corregir la autocorrelación: 0,073. Lo sólido es que todos superan la barra.
>
> Juan Diego, ¿en qué se apoyan para pronosticar?

#### ▶ Diapositiva 13 · _Importancia por permutación_ · 0,5 min

**🎤 JUAN DIEGO**

**[Señalar las tres primeras barras.]**

> Gracias, Sara. Al desordenar cada grupo de variables, el error sube sobre todo con el día anterior, que recoge el nivel reciente, y con el ciclo semanal. Los festivos también pesan.
>
> Y al marcar un lunes como festivo, el gradiente baja su pronóstico un 37,3 %, casi el 37,8 % del análisis exploratorio. Esto describe dependencia, no causa.
>
> Esto tiene límites claros.

#### ▶ Diapositiva 14 · _Limitaciones_ · 0,5 min

> Pronosticamos el registro, no la victimización: el hurto que no se denuncia no está. La evaluación no cubre la temporada de fin de año, no hay intervalos de predicción, y el pronóstico es de toda la ciudad y a un día. No sirve para decidir dónde patrullar.
>
> Sara, ¿cuál es la respuesta a la pregunta?

---

### BLOQUE 4 · Conclusiones · 🎤 SARA · 0,75 min

#### ▶ Diapositiva 15 · _Conclusiones_ · 0,75 min

> La respuesta tiene dos partes. Los patrones se identifican con claridad: un ciclo semanal fuerte, un efecto festivo de casi el 38 % y un nivel que cambia de un año a otro.
>
> Y el pronóstico a un día supera la línea base entre un 26 y un 33 %, en todos los pliegues, aunque sin un modelo ganador. Como trabajo futuro: dar el calendario a SARIMA y calcular intervalos de predicción.
>
> Ahora les muestro todo esto en el tablero de Power BI.

---

### BLOQUE 5 · Demo del tablero de Power BI · 🎤 SARA · 5 min

#### ▶ Diapositiva 16 · _Demo del tablero de Power BI_ · 5 min

**[Sara: Alt + Tab a Power BI Desktop, ya abierto y actualizado, en la página Panorama.]**

> El tablero lee las mismas salidas del proyecto, así que sus cifras son las del informe. Tiene cuatro páginas y un filtro de año común.

**[Panorama: señalar la serie mes a mes y la media diaria por año.]**

> Panorama responde cuánto hurto hay y hacia dónde va: la serie mensual, la media diaria por año y la nota que advierte que 2020 es atípico y que 2025 llega hasta octubre.

**[Cambiar el filtro de año a 2023 y volver a todos los años.]**

> Con el filtro de año, las cifras y la nota de hallazgo se recalculan.

**[Página ¿Cuándo?: señalar el reparto por día y el mapa de calor día × mes.]**

> La página ¿Cuándo? muestra el ciclo semanal, el mapa de calor por día y mes, y el efecto del lunes festivo.

**[Página ¿Dónde?: señalar volumen frente a tasa y el mapa.]**

> ¿Dónde? es la parte territorial, con la Línea 123. El orden por número de llamadas y por tasa cambia por completo: Kennedy es la primera por número y la decimotercera por tasa. Las tasas altas se concentran en el centro, que recibe mucha población flotante.

**[Página Pronóstico: señalar lo observado frente al mejor modelo y el error por modelo.]**

> Y Pronóstico compara lo observado con el mejor modelo en los 184 días de evaluación, y el error medio de cada modelo frente a la barra.
>
> Con esto terminamos. Muchas gracias; quedamos atentos a sus preguntas.

---

### BLOQUE 6 · Preguntas · 🎤 AMBOS · el tiempo que quede

#### ▶ Diapositiva 17 · _Preguntas_ · 0,25 min

**[Alt + Tab de vuelta a la presentación, en la diapositiva de preguntas.]**

**[Para responder: tecla O e ir a la diapositiva que corresponda, incluido el anexo.]**

---

### ANEXO · no se expone

Diapositivas de respaldo, después de «Preguntas». Se abren con la tecla **O** solo si una pregunta lo pide:

- 18 · Justificación y alcance
- 19 · Objetivos
- 20 · Las fuentes no se suman
- 21 · Territorio: número frente a tasa
- 22 · Pronóstico de un paso y fuga
- 23 · Arquitectura y reproducibilidad
- 24 · Decisiones y justificaciones
- 25 · Pronóstico frente a observado
- 26 · Errores en festivos
- 27 · Trabajo futuro
- 28 · Referencias

## Parte 3 · Registro del ensayo

Lo llena quien no está hablando, con cronómetro. Criterio: presentación (bloques 1 a 4) en 10 minutos o menos, y con Power BI, 15 o menos.

| Ensayo | Bloque 1 | Bloque 2 | Bloque 3 | Bloque 4 | Bloque 5 | Total |
|---|---|---|---|---|---|---|
| Planeado | 2,5 min | 2,75 min | 2,75 min | 0,75 min | 5 min | 13,75 min |
| 1 |   |   |   |   |   |   |
| 2 |   |   |   |   |   |   |

Notas (qué se recortó y por qué):
