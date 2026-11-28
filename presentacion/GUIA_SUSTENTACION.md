# Guía de sustentación · Hurto a personas en Bogotá, 2020–2025

Guía para preparar la exposición de la tercera entrega. Cada cifra sale del informe (`Informe/informe.tex`) y de los archivos de `outputs/` que lo sostienen. Si una pregunta pide un dato que no está aquí ni en el informe, la respuesta correcta es decirlo, no estimarlo en el momento.

El guion de la exposición está aparte, en [`GUION.md`](GUION.md). Esta guía reúne lo que hay que saber para las preguntas.

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

El reparto por bloques y los tiempos están en el «Resumen de quién habla» de [`GUION.md`](GUION.md). Sigue la responsabilidad de cada uno en el proyecto (`CLAUDE.md`). Para cambiarlo, editen el campo `expone` de cada diapositiva y ejecuten `npm run guion`.

**Atajos durante la exposición:**
- → o Espacio avanzan; ← retrocede; **Inicio** y **Fin** van a la primera y la última.
- **F**: pantalla completa. **N**: notas. **O**: índice, para saltar a una diapositiva durante las preguntas.
- La exposición son las diapositivas 1 a 17. Las 18 a 28 son el anexo: solo se abren si una pregunta lo pide.
- En la diapositiva 25 (anexo, pronóstico frente a observado) hay botones para cambiar el modelo que se superpone (gradiente, ETS o regresión).

---

## 3. Guion de exposición

El guion completo está en [`GUION.md`](GUION.md) y, para imprimir, en [`entregables/Guion_presentacion.pdf`](entregables/Guion_presentacion.pdf). Trae:

- quién habla en cada bloque y cuánto dura;
- las reglas para todos y la preparación antes de exponer;
- el texto de cada diapositiva, con acotaciones de qué señalar o en qué hacer clic;
- la tabla para registrar el ensayo.

Se genera desde las notas de las diapositivas con `npm run guion`: es el mismo texto del panel de notas (tecla **N**).

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

- [x] Duración confirmada: 15 minutos en total, 10 de presentación y 5 de Power BI.
- [ ] Ensayar completa con cronómetro y anotar el tiempo real de cada bloque.
- [ ] Anotar los tiempos medidos en la Parte 3 de `GUION.md` y, si hay que recortar, ajustar el texto de las notas y regenerar el guion (`npm run guion`).
- [ ] Probar la presentación en el equipo y el proyector de la sustentación, con el PDF como respaldo.
