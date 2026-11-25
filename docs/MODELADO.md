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

Esa prueba **no detecta la fuga del mismo día**: altera solo los días posteriores al pliegue, y un
predictor que use `y[t]` para predecir `t` la pasa igual que el ingenuo correcto (lo detectó la
revisión del #110). Para eso está `evaluacion.sin_fuga`: para cada día `t`, altera `y[t:]` y exige
que la predicción de `t` no cambie. **Cada modelo del #43 y del #44 la llama en sus pruebas.** Si el
modelo usa `X` con columnas derivadas de `y` (rezagos, medias móviles), hay que pasar
`construir_X`, que reconstruye `X` desde la serie alterada; sin ella, esas columnas no se alteran y
la prueba no las cubre. Al probar, cada día se prueba con la máscara de entrenamiento de su propio
tramo: con la del tramo final, un día de un pliegue ya estaría dentro del ajuste.

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
