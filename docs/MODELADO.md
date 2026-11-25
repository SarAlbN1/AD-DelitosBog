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

## Modelos de árboles con rezagos (#44)

`scripts/modelado/arboles.py` entrena un `RandomForestRegressor` y un `HistGradientBoostingRegressor`
con las 21 variables derivadas de `features.py`, y los evalúa con **el mismo arnés** que los
comparadores: mismos pliegues, misma evaluación final.

```sh
python scripts/modelado/arboles.py
```

Salidas en `outputs/modelado/arboles/`: `metricas_finales.csv`, `metricas_por_pliegue.csv`,
`predicciones_por_pliegue.csv` (real y predicción de cada día de cada pliegue y de la evaluación
final) y `resumen_arboles.json`.

**Los hiperparámetros son fijos, no ajustados.** La selección con validación temporal es el #45. Lo
que sigue es el punto de partida que el ajuste tiene que superar, no el resultado final.

| Modelo | MAE final | MASE final | MAE medio por pliegue | Peor pliegue |
|---|---|---|---|---|
| Barra (ingenuo estacional) | 49,04 | 0,922 | | |
| Bosque aleatorio | 34,22 | 0,643 | 34,89 | 43,12 |
| Bosque aleatorio, sin 2020 | 33,82 | 0,636 | 34,87 | 43,51 |
| Gradiente por histogramas | 32,89 | 0,618 | 31,51 | 36,19 |
| Gradiente por histogramas, sin 2020 | 32,94 | 0,619 | 32,56 | 38,41 |

Los cuatro quedan por debajo de la barra en la evaluación final. Es una sola partición de 184 días y
una sola semilla, así que **no es una conclusión de estabilidad**; la comparación con el resto de
modelos y la lectura de los pliegues van en el #46.

### El gradiente por histogramas no se reproduce entre plataformas

La revisión del #117 repitió la corrida con la misma semilla (42) en otros entornos. MAE de la
evaluación final:

| Entorno | Gradiente, con 2020 | Gradiente, sin 2020 | Bosque, con 2020 | Bosque, sin 2020 |
|---|---|---|---|---|
| macOS arm64, Python 3.9.6, scikit-learn 1.6.1 (este registro) | 32,89 | 32,94 | 34,22 | 33,82 |
| Linux x86 (Docker), **las mismas versiones** | 32,89 | 33,17 | | |
| Windows, Python 3.14, scikit-learn 1.9.1 | 32,77 | 33,68 | 34,22 | 33,82 |

(Las cifras de Linux y Windows son las que reportó la revisión de Juan Diego; la corrida de
este registro es la de macOS.)

* **El bosque aleatorio se reproduce exacto** en Windows, el único entorno distinto donde se probó.
* **El gradiente no.** En cada entorno el resultado es determinista (en Windows da lo mismo con 1 y
  con 8 hilos), así que la diferencia viene de la plataforma y de la versión, no del azar. Se mueve
  hasta 0,7 de MAE, mucho más que la cuarta cifra decimal que la sección de la semilla da por
  esperable, y la versión sin 2020 cambia incluso con las mismas versiones.
* **Consecuencia 1:** el criterio «las predicciones se reproducen con la semilla» se cumple en la
  misma máquina, no entre máquinas. Las cifras del registro valen para el entorno que guarda cada
  corrida (`versiones` en `outputs/modelado/corridas/`).
* **Consecuencia 2:** la sensibilidad a 2020 del gradiente depende del entorno. Quitar 2020 empeora
  el MAE final 0,05 en macOS, 0,28 en Linux y 0,91 en Windows. **Se presenta como no concluyente**
  hasta fijar un entorno de referencia; es la comparación que interpreta el #46. El bosque, en
  los dos entornos donde se corrió, mueve su MAE menos de 0,5 al quitar 2020; no se probó en Linux.
* **Pendiente de equipo, antes del #46:** fijar un entorno de referencia para las cifras del informe
  (por ejemplo, una imagen con versiones fijas). Con Python 3.9 no se puede instalar scikit-learn
  1.9, ni con 3.14 la 1.6.1, así que fijar versiones en `requirements.txt` no basta para los dos
  equipos.

### Los dos criterios de aceptación

* **La prueba anti-fuga pasa.** `evaluacion.sin_fuga` altera `y[t:]`, reconstruye las 21 variables
  desde la serie alterada (`construir_X`) y exige que la predicción de `t` no cambie.
  `tests/test_arboles.py` la aplica a los dos modelos sobre días de un pliegue y de la evaluación
  final, y comprueba con un modelo que sí usa `y[t]` que la prueba **falla** cuando debe.
* **Las predicciones se reproducen con la semilla.** Dos corridas dan las mismas predicciones y
  `outputs/modelado/arboles/` sale idéntico byte a byte al repetir el script en el mismo equipo. El
  registro de experimentos se niega a guardar dos resultados distintos para la misma huella.

El ajuste descarta las filas sin historia para los rezagos (los primeros 28 días; la primera fila
completa es el 2020-01-29). Con `sin_2020` se descartan además las filas del año atípico.
