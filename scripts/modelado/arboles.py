#!/usr/bin/env python3
"""Modelos de aprendizaje automático con rezagos: bosque aleatorio y potenciación del gradiente (#44).

Los dos modelos pasan por el mismo arnés que los comparadores de #42 (`evaluacion.evaluar`), así que
usan **exactamente los mismos pliegues y la misma evaluación final**. Predicen el día `t` con las 21
variables derivadas de `scripts/features.py`: calendario y pasado (rezagos de 1, 7, 14 y 28 días,
medias y desviaciones previas). Ninguna usa `y[t]`.

## Lo que garantiza que no hay fuga

El predictor recibe la serie observada completa, así que no se garantiza ocultándola sino
**comprobándola**: `evaluacion.sin_fuga` altera `y[t:]`, reconstruye las variables desde la serie
alterada y exige que la predicción de `t` no cambie. `tests/test_arboles.py` lo aplica a cada modelo.

## Qué no es esto

Los hiperparámetros son **fijos y razonables, no ajustados**. La selección con validación temporal
es el #45. Por eso estas cifras no son todavía el resultado final del modelo: son el punto de partida
contra el que el ajuste tiene que mejorar.

## Sensibilidad a 2020

D-04 exige comprobar qué pasa al entrenar sin 2020. Cada modelo se entrena dos veces: con 2020
marcado (`anio_atipico_2020`) y sin las filas de 2020. La evaluación es la misma.

Uso::

    python scripts/modelado/arboles.py
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "scripts", RAIZ / "scripts" / "modelado"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import features as feat  # noqa: E402
from modelado import cargar, fijar_semillas, registrar  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import (VERSION_ARNES, evaluar, huella_pliegues,  # noqa: E402
                                 particion, pliegues)
from modelado.referencia import evaluar_todos  # noqa: E402
from modelado.registro import sha256_archivo  # noqa: E402

log = logging.getLogger("modelado.arboles")

#: Hiperparámetros fijos (no ajustados: eso es #45). `random_state` y `n_jobs` se añaden al construir.
HIPERPARAMETROS: dict[str, dict] = {
    "bosque_aleatorio": {"n_estimators": 300, "min_samples_leaf": 3, "max_features": 0.5},
    "gradiente_histogramas": {"max_iter": 300, "learning_rate": 0.05, "max_leaf_nodes": 15,
                              "min_samples_leaf": 20},
}


def construir_X(y: pd.Series) -> pd.DataFrame:
    """Las predictoras, reconstruidas desde una serie. Es lo que `sin_fuga` necesita para alterar `y`."""
    X = feat.construir(y.to_frame(y.name or "victimas"), objetivo=y.name or "victimas")
    return X[feat.predictoras(X, objetivo=y.name or "victimas")]


def crear_modelo(nombre: str, semilla: int, hiperparametros: dict | None = None):
    """Un estimador con semilla explícita. `n_jobs=1` evita variaciones de punto flotante."""
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    hp = dict(HIPERPARAMETROS[nombre] if hiperparametros is None else hiperparametros)
    if nombre == "bosque_aleatorio":
        return RandomForestRegressor(random_state=semilla, n_jobs=1, **hp)
    if nombre == "gradiente_histogramas":
        return HistGradientBoostingRegressor(random_state=semilla, **hp)
    raise KeyError(f"modelo desconocido: {nombre}")


def predictor_arbol(nombre: str, semilla: int, sin_2020: bool = False,
                    indicador: str = "anio_atipico_2020",
                    hiperparametros: dict | None = None,
                    registro: list | None = None) -> Callable:
    """Predictor con la firma del arnés: ajusta solo con `entrena` y predice `indice`.

    Las filas con nulos (los primeros 28 días, sin historia para los rezagos) no entran al ajuste.
    Con `sin_2020=True` tampoco entran las filas marcadas como año atípico. Si `registro` es una
    lista, cada llamada añade ahí sus predicciones, en el orden en que el arnés las pide.
    """

    def _predecir(y: pd.Series, X: pd.DataFrame | None, entrena: np.ndarray,
                  indice: pd.DatetimeIndex) -> pd.Series:
        if X is None:
            raise ValueError("el modelo necesita las variables derivadas (X)")
        tr = X[entrena]
        tr = tr.loc[tr.notna().all(axis=1)]
        if sin_2020:
            tr = tr[tr[indicador] == 0]
        modelo = crear_modelo(nombre, semilla, hiperparametros).fit(tr, y.loc[tr.index])
        pred = pd.Series(modelo.predict(X.loc[indice]), index=indice)
        if registro is not None:
            registro.append(pred)
        return pred

    return _predecir


def evaluar_modelo(cfg, y: pd.Series, nombre: str, semilla: int, sin_2020: bool = False,
                   hiperparametros: dict | None = None) -> dict:
    """Evalúa un modelo con el protocolo completo y devuelve también sus predicciones por tramo."""
    llamadas: list[pd.Series] = []
    pred = predictor_arbol(nombre, semilla, sin_2020, cfg.indicador_atipico, hiperparametros,
                           llamadas)
    etiqueta = nombre + ("_sin_2020" if sin_2020 else "")
    r = evaluar(cfg, y, pred, X=construir_X(y), nombre=etiqueta)
    n = len(r["por_pliegue"])
    # El arnés llama al predictor una vez por pliegue con evaluación y, al final, una por la
    # evaluación final: n + 1 llamadas.
    if len(llamadas) != n + 1:
        raise RuntimeError(f"se esperaban {n + 1} llamadas al predictor y hubo {len(llamadas)}")
    numeros = [p["pliegue"] for p in r["por_pliegue"]] + ["final"]
    filas = []
    for numero, p in zip(numeros, llamadas):
        for fecha, valor in p.items():
            filas.append({"modelo": etiqueta, "pliegue": numero, "fecha": fecha.date().isoformat(),
                          "real": float(y.loc[fecha]), "prediccion": round(float(valor), 4)})
    r["predicciones"] = pd.DataFrame(filas)
    return r


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=None,
                   help="Carpeta de las tablas. Con ella, el registro de corridas también va a "
                        "<salida>/registro. Por defecto, outputs/modelado/arboles.")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = cargar()
    semilla = fijar_semillas(cfg.semilla)
    if not cfg.serie.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", cfg.serie)
        return 2
    y = (pd.read_csv(cfg.serie, parse_dates=["fecha"]).set_index("fecha")[cfg.objetivo]
         .astype(float).sort_index())
    validar_contra_serie(cfg, y.index)

    salida = a.salida or (cfg.carpeta_registro / "arboles")
    salida.mkdir(parents=True, exist_ok=True)
    if a.salida is not None:
        cfg = dataclasses.replace(cfg, carpeta_registro=a.salida / "registro")

    barra = evaluar_todos(cfg, y)["barra"]
    resultados: dict[str, dict] = {}
    for nombre in HIPERPARAMETROS:
        for sin in (False, True):
            r = evaluar_modelo(cfg, y, nombre, semilla, sin_2020=sin)
            resultados[r["nombre"]] = r

    pd.concat([r["predicciones"] for r in resultados.values()]).to_csv(
        salida / "predicciones_por_pliegue.csv", index=False)
    pd.DataFrame([{"modelo": n, "pliegue": q["pliegue"], **{k: q[k] for k in cfg.metricas}}
                  for n, r in resultados.items() for q in r["por_pliegue"]]).to_csv(
        salida / "metricas_por_pliegue.csv", index=False)
    finales = pd.DataFrame({n: r["final"] for n, r in resultados.items()}).T
    finales["MAE_vs_barra"] = (finales["MAE"] - barra["MAE"]).round(2)
    finales.to_csv(salida / "metricas_finales.csv", index_label="modelo")
    (salida / "resumen_arboles.json").write_text(json.dumps({
        "barra": barra,
        "hiperparametros": HIPERPARAMETROS,
        "nota": ("hiperparámetros fijos, sin ajustar: la selección con validación temporal es "
                 "el #45. Las cifras son el punto de partida, no el resultado final"),
        "modelos": {n: {"final": r["final"], "resumen_pliegues": r["resumen_pliegues"],
                        "por_pliegue": r["por_pliegue"]} for n, r in resultados.items()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    datos = {"serie": cfg.serie.name, "serie_sha256": sha256_archivo(cfg.serie),
             "huella_pliegues": huella_pliegues(cfg, y.index), "version_arnes": VERSION_ARNES}
    for n, r in resultados.items():
        base = n.removesuffix("_sin_2020")
        registrar(cfg, f"arboles.{n}", {**HIPERPARAMETROS[base], "sin_2020": n.endswith("_sin_2020")},
                  r["final"], datos, extra={"resumen_pliegues": r["resumen_pliegues"]})

    log.info("barra: %s, MAE %.2f, MASE %.3f", barra["mejor_por_MAE"], barra["MAE"],
             barra["MASE_a_superar"])
    for n, r in resultados.items():
        f, s = r["final"], r["resumen_pliegues"]
        log.info("  %-34s final MAE %6.2f MASE %.3f · pliegues MAE medio %6.2f peor %6.2f",
                 n, f["MAE"], f["MASE"], s["MAE_medio"], s["MAE_peor"])
    log.info("salidas en %s", salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
