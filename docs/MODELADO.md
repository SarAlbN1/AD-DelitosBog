# Entorno de modelado (#41)

Base de la tercera entrega. El protocolo lo fija D-04 y este entorno lo **codifica una sola vez**,
en `config/modelado.json`.

## Por qué la configuración está centralizada

No es preferencia de estilo. La ruta de Línea 123 ya estuvo escrita en dos scripts y divergió sin
que nadie lo notara hasta que alguien la buscó (#34). Con la partición pasaría lo mismo y sería
peor: un modelo evaluado con otra partición da otro número y **nada avisa**. Si el protocolo cambia,
se cambia en `config/modelado.json` y ningún script hay que tocar.

```
config/modelado.json          el protocolo, con el motivo de cada valor
scripts/modelado/
├── config.py                 lo carga y lo valida
├── semillas.py               fija la aleatoriedad
├── registro.py               registra cada corrida
└── comprobar_entorno.py      demuestra que dos corridas iguales dan lo mismo
```

## La semilla es 42, y fijarla no basta

`fijar_semillas` toca los tres sitios de los que depende la reproducibilidad: `random`, el generador
global de NumPy y `PYTHONHASHSEED`, que afecta al orden de iteración de conjuntos y diccionarios con
claves de texto.

Pero **eso no es suficiente**, y conviene no confiarse: muchos estimadores de scikit-learn no leen
el estado global y necesitan recibir `random_state` explícitamente. Por eso `fijar_semillas`
devuelve el valor, para pasarlo:

```python
semilla = fijar_semillas(cfg.semilla)
modelo = RandomForestRegressor(random_state=semilla, n_jobs=1, **hiperparametros)
```

`n_jobs=1` también importa: con varios hilos, el orden de reducción de punto flotante puede variar y
mover los últimos decimales.

## El registro de experimentos

Cada corrida deja `outputs/modelado/corridas/<huella>.json` y una fila en `experimentos.csv`.

La **huella** es lo que hace verificable el criterio de aceptación de la issue. Es el SHA-256 de lo
que determina el resultado —configuración, modelo, hiperparámetros, semilla y hash de los datos—, no
del momento en que se lanzó. Dos corridas con la misma huella **deben** dar las mismas métricas, y:

- `registrar` **falla** si ya existe esa huella con métricas distintas, en lugar de sobrescribir.
  Guardar dos verdades para la misma corrida es peor que fallar;
- repetir una corrida idéntica no duplica la fila del índice;
- `comprobar_determinismo` devuelve el resultado sin lanzar, para quien prefiera decidir.

Se guardan además las versiones de las bibliotecas. Un cambio de versión puede mover la cuarta cifra
decimal con la misma semilla, y sin esa información la diferencia parece un error del código.

## Comprobar que el entorno es reproducible

```sh
python scripts/modelado/comprobar_entorno.py
```

Ajusta **dos veces el mismo bosque aleatorio con la misma semilla** y exige que las métricas
coincidan. Usa un modelo de verdad, no una simulación: si un estimador no recibe `random_state` o
una biblioteca introduce no determinismo, esto lo detecta.

Resultado en este equipo (macOS, Python 3.9.6, pandas 2.3.3, scikit-learn 1.6.1):

```
dos corridas con la semilla 42 dan las mismas métricas:
{'n': 184, 'MAE': 36.68, 'RMSE': 45.62, 'MAPE': 10.67, 'MASE': 0.693}
```

> **Esa cifra no es un resultado del proyecto.** Es un modelo de humo: se ajusta una sola vez sobre
> todo el entrenamiento, sin selección de hiperparámetros por validación rodante y sin prueba de
> sensibilidad a 2020. Que caiga por debajo de la barra (MAE 49,04, MASE 0,922) es **indicativo y
> alentador**, no concluyente. Los resultados que el informe puede citar salen de #42, #43, #44 y
> #46, siguiendo el protocolo completo.

## Las validaciones que atrapan errores silenciosos

`config.py` no valida por formalidad. Rechaza exactamente lo que daría números plausibles y falsos:

| Qué rechaza | Por qué |
|---|---|
| Un esquema de validación que no sea `origen_rodante` | Una validación aleatoria pone futuro en el entrenamiento y el error sale optimista |
| Una métrica principal que no está entre las reportadas | Se decidiría con una métrica que el informe no muestra |
| Una métrica que el proyecto no sabe calcular | Falla al ejecutar, no al configurar |
| Una fecha de partición mal formada | `pandas` la interpretaría de otra forma sin avisar |
| Una partición fuera del rango de la serie | Deja un lado vacío |
| Pliegues que no caben en el entrenamiento | Se recortarían en silencio y la validación tendría menos pliegues de los que el informe dice |

## xgboost necesita una dependencia de sistema

En macOS, `xgboost` se instala pero **no se puede importar** sin `libomp`:

```
Library not loaded: @rpath/libomp.dylib
```

Se resuelve con `brew install libomp`. En este equipo no está instalado, así que el registro anota
`xgboost: no disponible`.

**No es un bloqueo.** La familia de conjuntos de árboles que propone `METODOLOGIA.md` se cubre con
`RandomForestRegressor` y `HistGradientBoostingRegressor`, los dos de scikit-learn y sin
dependencias de sistema. `HistGradientBoostingRegressor` es una implementación de potenciación del
gradiente por histogramas, equivalente en enfoque a xgboost para este tamaño de datos.

Si se decide usar xgboost, hay que instalar `libomp` **y dejarlo escrito en la guía de
reproducción**, porque un entorno limpio sin esa biblioteca falla al importar y el mensaje no es
evidente.


## El arnés de evaluación compartido (#42)

El criterio de aceptación de #42 era que **los comparadores usen exactamente los mismos pliegues que
los modelos**. «Seguir el mismo protocolo» no es comprobable; producir los mismos límites de
pliegue, sí.

`scripts/modelado/evaluacion.py` es **la única** definición de los pliegues, la partición y las
métricas. `baselines.py` importa de ahí en lugar de reimplementarlas, y `modelado/referencia.py`
expresa los cuatro comparadores como predictores con la misma firma que tendrá cualquier modelo.
Así pasan por `evaluar()` igual que un bosque aleatorio.

`tests/test_evaluacion.py` lo comprueba comparando los límites de pliegue de un modelo lineal real
contra los de los cuatro comparadores: si un día divergen, falla antes de que los números se
publiquen.

### Un predictor recibe la serie completa, y por qué

El contrato es: `predictor(y, X, entrena, indice)`, con `y` la serie observada completa. Puede usar
`y[s]` solo para `s` anterior al día que predice, y ajustar parámetros solo con `entrena`.

Mi primera versión retenía el tramo de evaluación, pensando que así era imposible la fuga. **Estaba
mal, y lo delató comparar contra las cifras conocidas**: el comparador ingenuo daba MAE 13,00 con
n = 1 en lugar de 52,92 con n = 184, porque solo el primer día de la ventana recibía predicción.

El fondo es que el horizonte es de un día: para predecir `t` se usa el conteo de `t-1`, que **ya es
pasado** y está observado, también dentro de la ventana de evaluación. Es lo que fija el protocolo.
Retener esos datos rompe el pronóstico en lugar de protegerlo.

Lo que impide el uso indebido no es ocultar la serie, es la **prueba de perturbación**: alterar `y`
desde un día hacia adelante no puede cambiar la métrica de ese pliegue. Con su comprobación
inversa, para que no pase por vacuidad.

### La versión del arnés

`VERSION_ARNES` se sube **a mano** cuando cambia cómo se calcula un resultado.

Existe por un hueco que apareció al corregir el error de arriba: el registro identifica una corrida
por su huella, y la huella no puede mirar el código. Así que el arreglo produjo la misma huella con
métricas distintas, y el registro **se negó a continuar** — correctamente, pero sin salida. Con la
versión en la huella, un cambio de semántica es otra corrida y las dos quedan registradas.

No se sube por cambios de comentarios ni de nombres: solo si el número resultante puede cambiar.

### Resultado de los comparadores con el arnés

| Comparador | Final MAE | MASE | Pliegues: MAE medio | Desv. | Peor |
|---|---:|---:|---:|---:|---:|
| Ingenuo | 52,92 | 0,995 | 58,36 | 9,37 | 75,48 |
| **Ingenuo estacional** | **49,04** | **0,922** | 58,30 | 14,11 | 75,57 |
| Media móvil 7 | 49,42 | 0,929 | 58,78 | 11,52 | 76,38 |
| Media móvil 28 | 55,83 | 1,050 | 65,12 | 14,03 | 82,00 |

Idénticas a las de `baselines.py`, que es lo que confirma que el refactor no cambió el cálculo.

El resumen por pliegue añade algo que la cifra final esconde: **el ingenuo estacional es el que más
varía entre pliegues** (desviación 14,11 frente a 9,37 del ingenuo) y gana solo 2 de los 6, aunque
sea el mejor en la evaluación final. Un modelo que lo bata en la ventana final debería además ser
más estable, y el informe tiene que reportar las dos cosas.

## Lo que este entorno no hace

- **No ajusta ningún modelo del informe.** Eso es #43 y #44. #42 dejó el arnés y los
  comparadores.
- **No selecciona hiperparámetros.** Es #45, y debe recorrer la rejilla dentro de los pliegues
  rodantes, nunca tocando los 184 días de evaluación.
- **No registra el entrenamiento sin 2020.** La prueba de sensibilidad que pide D-04 se ejecuta en
  #46, y el registro ya la admite: es otra corrida con otra huella.

## Modelos estadísticos de series de tiempo (#43)

`scripts/modelado/estadisticos.py` ajusta **SARIMA** y **ETS** (`statsmodels`) y los evalúa con el
mismo arnés que los comparadores: mismos pliegues, misma evaluación final.

```sh
python scripts/modelado/estadisticos.py
```

Salidas en `outputs/modelado/estadisticos/`: `estacionariedad.csv`, `seleccion_por_pliegue.csv`,
`diagnostico_residuos.csv`, `metricas_finales.csv`, `metricas_por_pliegue.csv`,
`predicciones_por_pliegue.csv` y `resumen_estadisticos.json`. El script tarda unos dos minutos.

### Cómo se predice un día sin mirarlo

El modelo se ajusta con el entrenamiento del tramo y se aplica con parámetros fijos a la serie
observada hasta el último día a predecir. La predicción de `t` es el valor ajustado un paso
adelante, que depende de `y[:t]` y no de `y[t]`. `evaluacion.sin_fuga` lo comprueba para los dos
modelos en `tests/test_estadisticos.py`, con un control que falla cuando el predictor sí mira `y[t]`.

### La selección de órdenes se repite en cada tramo

Es el criterio de aceptación: la selección no usa el conjunto de prueba. Hay una trampa que
conviene dejar escrita: **los pliegues de validación están dentro del periodo de entrenamiento
final**. Elegir los órdenes una vez con todo ese periodo haría que cada pliegue se evaluara con un
modelo elegido viendo sus propios días. Por eso la selección ocurre dentro de cada llamada al
predictor, con el entrenamiento de ese tramo. Una prueba lo verifica alterando la serie fuera del
entrenamiento: ni el criterio ni la especificación elegida cambian.

* **Estacionariedad (ADF y KPSS), entrenamiento final.** El nivel no es estacionario (ADF p = 0,091;
  KPSS p = 0,01). La primera diferencia, la estacional de 7 días y la combinación sí lo son. De ahí
  sale `d = 1`.
* **`D`** sale de la fuerza de la estacionalidad semanal (STL, umbral 0,64). Salió `D = 0`: la fuerza
  queda por debajo, y la estacionalidad entra por los términos autorregresivos y de media móvil
  estacionales.
* **`(p, q)` y `(P, Q)`:** malla de 9 × 3 por AIC, con `d` y `D` ya fijados, porque el AIC no es
  comparable entre distintas diferenciaciones. **ETS:** cuatro configuraciones por AICc.

### Resultados (evaluación final, 184 días)

| Modelo | MAE final | MASE final | MAE medio por pliegue | Peor pliegue |
|---|---|---|---|---|
| Barra (ingenuo estacional) | 49,04 | 0,922 | | |
| SARIMA | 33,53 | 0,630 | 36,16 | 43,11 |
| SARIMA, desde 2021 | 33,78 | 0,635 | 36,27 | 43,55 |
| ETS | 32,96 | 0,620 | 36,70 | 44,61 |
| ETS, desde 2021 | 32,99 | 0,620 | 52,72 | 84,00 |

La variante «desde 2021» es la prueba de sensibilidad a 2020: en un modelo de series no se pueden
quitar las filas de un año sin romper la continuidad, así que se entrena desde el 2021-01-01. En la
evaluación final casi no cambia nada.

### Un hallazgo que no es un error: el criterio de información elige mal en un pliegue

`ETS, desde 2021` tiene MAE 84,00 y 79,51 en los pliegues 2 y 3, frente a 36 y 31 del ETS normal. Se
investigó: en esos pliegues la selección elige la estacionalidad **multiplicativa**, que gana por
AICc en entrenamiento (12.352 frente a 12.363 de la aditiva) y falla fuera de muestra. Todos los
ajustes convergen y no hay fuga. Es el criterio de información, no el código: **ganar en
entrenamiento no predice ganar en el pliegue siguiente en esta serie**. No se corrige aquí porque
cambiar el criterio de selección es una decisión de #45, y porque ocultarlo mejoraría la tabla y
empeoraría la lectura. Es un dato para #45 y #46.

### La selección por pliegue puede cambiar entre plataformas

La revisión del #118 repitió el script en Windows (Python 3.14, statsmodels 0.15.0). **La evaluación
final se reproduce** con una diferencia de hasta 0,01 de MAE (SARIMA 33,53 frente a 33,54; las demás
cifras iguales), y `estacionariedad.csv` sale idéntico. Lo que cambia es la **elección por pliegue**
cuando dos candidatas están casi empatadas por AICc:

| Modelo, pliegue | Esta corrida | Windows | MAE del pliegue (esta → Windows) |
|---|---|---|---|
| SARIMA desde 2021, 1 | (2,1,2) | (1,1,2) | 43,55 → 42,30 |
| ETS desde 2021, 1 | aditivo con tendencia amortiguada | aditivo sin tendencia | 44,61 → 44,66 |
| ETS desde 2021, 4 | estacionalidad aditiva | multiplicativa | 29,82 → 29,85 |
| ETS desde 2021, 6 | multiplicativa | aditiva | 39,42 → **43,22** |

(Cifras de la revisión de Juan Diego en Windows.) En esos casos el AICc de la ganadora difiere en
menos de 4 puntos entre las dos corridas, así que una diferencia numérica mínima del optimizador
basta para cambiar la ganadora. Las cifras finales no se mueven, pero **las métricas por pliegue sí**,
y el #45 va a ajustar sobre ellas. Se recomienda una regla de desempate para el #45 (por ejemplo,
preferir la configuración más simple si ΔAICc < 2), de modo que la selección no dependa del entorno.

Dos precisiones a lo escrito arriba: «la multiplicativa falla fuera de muestra» vale para los
pliegues 2 y 3 de `ETS, desde 2021`, no en general (en el pliegue 6 la aditiva sale peor); y «salidas
idénticas byte a byte» se cumple en la misma máquina.

### Diagnóstico de residuos (Ljung-Box, ajuste final con el entrenamiento)

| Modelo | Especificación elegida | p (rezago 7) | p (14) | p (28) |
|---|---|---|---|---|
| SARIMA | (1,1,2)(1,0,1,7) | 0,0000 | 0,0000 | 0,0001 |
| ETS | error aditivo, sin tendencia, estacionalidad multiplicativa | 0,0000 | 0,0000 | 0,0000 |

**En los dos queda autocorrelación sin modelar** (p < 0,05 en los tres rezagos). Los residuos tienen
desviación de unos 52 casos, mucho más que el MAE de evaluación (33): el ajuste sobre todo el
entrenamiento arrastra los años 2020 y 2021, de nivel muy distinto. Los modelos solo cubren la
estacionalidad semanal; la anual y los festivos, que los modelos con variables derivadas (#44) sí
usan, quedan en el residuo. Es una lectura para la sección de resultados y no invalida las
métricas, que se calculan fuera de muestra.
