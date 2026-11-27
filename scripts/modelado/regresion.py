#!/usr/bin/env python3
"""Regresión lineal con rezagos y calendario (#144).

Es la tercera familia de modelos que propone la sección 7 y que el enunciado del laboratorio exige:
el modelo **transparente**, cuyos coeficientes se pueden leer. Usa las mismas 21 predictoras de
`scripts/features.py` que los árboles y pasa por el mismo arnés que todos los demás modelos
(`evaluacion.evaluar`): mismos pliegues, misma evaluación final, misma prueba `sin_fuga`.

## Cómo se arma la matriz

Dentro de un `Pipeline`, que se ajusta **por partición** para no filtrar información entre pliegues:

* `dia_semana` y `mes` son categorías, no cantidades: un martes no es «dos veces» un lunes. Se
  codifican en indicadores. El resto se escala (media 0 y desviación 1 con el entrenamiento) para que
  los coeficientes se puedan comparar entre sí.
* Las 21 predictoras entran todas. Algunas son redundantes (`fin_de_semana` es función de
  `dia_semana`, y `semana_del_anio` casi lo es de `mes`): la regularización ridge lo tolera, y por eso
  es la regresión de esta familia.

## Elección de la regularización

Con los seis pliegues de origen rodante, dentro del entrenamiento, **sin tocar los 184 días de
evaluación**, como en #45. `alpha = 0` es la regresión de mínimos cuadrados. Gana el menor MAE sobre
las fechas de validación combinadas; a igualdad, la más regularizada (la más simple).

## Qué se guarda

Además de las métricas y las predicciones, `coeficientes.csv`: es la razón de ser de esta familia. Hay
dos columnas porque dicen cosas distintas. El coeficiente **estandarizado** compara variables entre sí
(cuántas víctimas por día cambia el pronóstico cuando la variable sube una desviación). El
**coeficiente por unidad** es el efecto de pasar de 0 a 1 en un indicador, como el festivo.

Un coeficiente describe cómo usa el modelo la variable **junto con las demás**: con rezagos
correlacionados entre sí no es un efecto aislado ni causal.

Uso::

    python scripts/modelado/regresion.py [--salida DIR]
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

from modelado import ajuste  # noqa: E402
from modelado import cargar, fijar_semillas, registrar  # noqa: E402
from modelado.arboles import construir_X  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import (VERSION_ARNES, evaluar, huella_pliegues,  # noqa: E402
                                 particion)
from modelado.referencia import evaluar_todos  # noqa: E402
from modelado.registro import sha256_archivo  # noqa: E402

log = logging.getLogger("modelado.regresion")

#: Variables que son categorías y no cantidades.
CATEGORICAS = ["dia_semana", "mes"]
#: Regularización ridge a probar. 0 es mínimos cuadrados ordinarios.
ALPHAS = [0.0, 0.1, 1.0, 10.0, 100.0, 1000.0]


def crear_modelo(alpha: float, columnas: list[str]):
    """`Pipeline`: indicadores para las categorías, escalado para el resto y ridge (o MCO si alpha = 0)."""
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    numericas = [c for c in columnas if c not in CATEGORICAS]
    pre = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAS),
         ("num", StandardScaler(), numericas)])
    reg = LinearRegression() if alpha == 0 else Ridge(alpha=alpha)
    return Pipeline([("pre", pre), ("reg", reg)])


def _entrenamiento(X: pd.DataFrame, y: pd.Series, entrena: np.ndarray, sin_2020: bool,
                   indicador: str) -> pd.DataFrame:
    """Filas completas del entrenamiento; sin las del año atípico si se pide la sensibilidad."""
    tr = X[entrena]
    tr = tr.loc[tr.notna().all(axis=1)]
    if sin_2020:
        tr = tr[tr[indicador] == 0]
    return tr


def predictor_regresion(alpha: float, sin_2020: bool = False,
                        indicador: str = "anio_atipico_2020",
                        registro: list | None = None) -> Callable:
    """Predictor con la firma del arnés: ajusta solo con `entrena` y predice `indice`.

    Si `registro` es una lista, cada llamada añade ahí sus predicciones, en el orden en que el arnés
    las pide.
    """

    def _predecir(y: pd.Series, X: pd.DataFrame | None, entrena: np.ndarray,
                  indice: pd.DatetimeIndex) -> pd.Series:
        if X is None:
            raise ValueError("el modelo necesita las variables derivadas (X)")
        tr = _entrenamiento(X, y, entrena, sin_2020, indicador)
        # numpy 2.0.2 con Accelerate (macOS) emite avisos falsos de «divide by zero / overflow /
        # invalid» en el producto de matrices, con resultados correctos (se comprobó resolviendo las
        # ecuaciones normales sin BLAS). Se silencian solo aquí, y la comprobación de que todo es finito
        # impide que oculten un fallo real.
        with np.errstate(all="ignore"):
            modelo = crear_modelo(alpha, list(X.columns)).fit(tr, y.loc[tr.index])
            valores = modelo.predict(X.loc[indice])
        if not np.isfinite(valores).all():
            raise RuntimeError("la regresión produjo predicciones no finitas")
        pred = pd.Series(valores, index=indice)
        if registro is not None:
            registro.append(pred)
        return pred

    return _predecir


def evaluar_modelo(cfg, y: pd.Series, alpha: float, sin_2020: bool = False) -> dict:
    """Evalúa la regresión con el protocolo completo y devuelve también sus predicciones por tramo."""
    llamadas: list[pd.Series] = []
    pred = predictor_regresion(alpha, sin_2020, cfg.indicador_atipico, llamadas)
    etiqueta = "regresion_lineal" + ("_sin_2020" if sin_2020 else "")
    r = evaluar(cfg, y, pred, X=construir_X(y), nombre=etiqueta)
    n = len(r["por_pliegue"])
    if len(llamadas) != n + 1:
        raise RuntimeError(f"se esperaban {n + 1} llamadas al predictor y hubo {len(llamadas)}")
    numeros = [p["pliegue"] for p in r["por_pliegue"]] + ["final"]
    filas = [{"modelo": etiqueta, "pliegue": numero, "fecha": fecha.date().isoformat(),
              "real": float(y.loc[fecha]), "prediccion": round(float(valor), 4)}
             for numero, p in zip(numeros, llamadas) for fecha, valor in p.items()]
    r["predicciones"] = pd.DataFrame(filas)
    return r


def buscar_alpha(cfg, y_sel: pd.Series, X_sel: pd.DataFrame) -> tuple[list[dict], dict]:
    """Recorre `ALPHAS` en los pliegues. `y_sel` llega recortada al fin del entrenamiento."""
    resultados = []
    for a in ALPHAS:
        r = ajuste.validar_en_pliegues(cfg, y_sel, predictor_regresion(a, indicador=cfg.indicador_atipico),
                                       X_sel)
        resultados.append({"alpha": a, **r})
        log.info("  alpha %-7g MAE validación %.2f", a, r["MAE_combinado"])
    # Menor MAE; a igualdad, la más regularizada.
    elegido = min(resultados, key=lambda c: (c["MAE_combinado"], -c["alpha"]))
    return resultados, elegido


def tabla_coeficientes(modelo) -> pd.DataFrame:
    """Coeficientes de un `Pipeline` ajustado, estandarizados y por unidad de la variable original.

    En las numéricas, `coef_por_unidad` = `coef_estandarizado` / desviación usada para escalar. En los
    indicadores ya está por unidad (pasar de 0 a 1).
    """
    pre, reg = modelo.named_steps["pre"], modelo.named_steps["reg"]
    nombres = list(pre.get_feature_names_out())
    est = np.ravel(reg.coef_)
    escala = iter(pre.named_transformers_["num"].scale_)
    por_unidad = [est[i] if n.startswith("cat__") else est[i] / next(escala)
                  for i, n in enumerate(nombres)]
    t = pd.DataFrame({"variable": [n.split("__", 1)[1] for n in nombres],
                      "tipo": ["indicador" if n.startswith("cat__") else "numerica" for n in nombres],
                      "coef_estandarizado": est, "coef_por_unidad": por_unidad})
    t = t.reindex(t["coef_estandarizado"].abs().sort_values(ascending=False).index)
    intercepto = float(np.ravel(reg.intercept_)[0])
    fila = pd.DataFrame([{"variable": "(intercepto)", "tipo": "intercepto",
                          "coef_estandarizado": intercepto, "coef_por_unidad": intercepto}])
    return pd.concat([fila, t], ignore_index=True).round(4)


def coeficientes(cfg, y: pd.Series, alpha: float) -> pd.DataFrame:
    """Coeficientes del ajuste final: todo el entrenamiento, con 2020 marcado."""
    X = construir_X(y)
    tr_mask, _ = particion(cfg, y.index)
    tr = _entrenamiento(X, y, tr_mask, False, cfg.indicador_atipico)
    with np.errstate(all="ignore"):
        modelo = crear_modelo(alpha, list(X.columns)).fit(tr, y.loc[tr.index])
    return tabla_coeficientes(modelo)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=None,
                   help="Carpeta de las tablas. Con ella, el registro de corridas también va a "
                        "<salida>/registro. Por defecto, outputs/modelado/regresion.")
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

    salida = a.salida or (cfg.carpeta_registro / "regresion")
    salida.mkdir(parents=True, exist_ok=True)
    if a.salida is not None:
        cfg = dataclasses.replace(cfg, carpeta_registro=a.salida / "registro")

    fin = pd.Timestamp(cfg.fin_entrenamiento)
    y_sel = y[y.index <= fin]
    X_sel = ajuste.predictoras_seleccion(y, fin)
    log.info("búsqueda de la regularización en los pliegues")
    busqueda, elegido = buscar_alpha(cfg, y_sel, X_sel)
    alpha = elegido["alpha"]

    barra = evaluar_todos(cfg, y)["barra"]
    resultados = {}
    for sin in (False, True):
        r = evaluar_modelo(cfg, y, alpha, sin_2020=sin)
        resultados[r["nombre"]] = r

    pd.DataFrame([{"alpha": c["alpha"], "MAE_validacion": c["MAE_combinado"],
                   "n_validacion": c["n_validacion"], "elegida": c["alpha"] == alpha,
                   **{f"MAE_pliegue_{q['pliegue']}": q["MAE"] for q in c["por_pliegue"]}}
                  for c in busqueda]).to_csv(salida / "busqueda.csv", index=False)
    pd.concat([r["predicciones"] for r in resultados.values()]).to_csv(
        salida / "predicciones_por_pliegue.csv", index=False)
    pd.DataFrame([{"modelo": n, "pliegue": q["pliegue"], **{k: q[k] for k in cfg.metricas}}
                  for n, r in resultados.items() for q in r["por_pliegue"]]).to_csv(
        salida / "metricas_por_pliegue.csv", index=False)
    finales = pd.DataFrame({n: r["final"] for n, r in resultados.items()}).T
    finales["alpha"] = alpha
    finales["MAE_vs_barra"] = (finales["MAE"] - barra["MAE"]).round(2)
    finales.to_csv(salida / "metricas_finales.csv", index_label="modelo")
    coef = coeficientes(cfg, y, alpha)
    coef.to_csv(salida / "coeficientes.csv", index=False)
    (salida / "resumen_regresion.json").write_text(json.dumps({
        "barra": barra,
        "alphas": ALPHAS, "alpha_elegido": alpha,
        "criterio": "menor MAE sobre las fechas de validación combinadas de los pliegues; "
                    "a igualdad, la regularización más alta; la evaluación final no interviene",
        "MAE_validacion_elegido": elegido["MAE_combinado"],
        "categoricas": CATEGORICAS,
        "modelos": {n: {"final": r["final"], "resumen_pliegues": r["resumen_pliegues"],
                        "por_pliegue": r["por_pliegue"]} for n, r in resultados.items()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    datos = {"serie": cfg.serie.name, "serie_sha256": sha256_archivo(cfg.serie),
             "huella_pliegues": huella_pliegues(cfg, y.index), "version_arnes": VERSION_ARNES}
    import os
    datos["entorno"] = os.environ.get("AD_ENTORNO", "local")
    for n, r in resultados.items():
        registrar(cfg, f"regresion.{n}", {"alpha": alpha, "sin_2020": n.endswith("_sin_2020"),
                                          "categoricas": CATEGORICAS},
                  r["final"], datos, extra={"resumen_pliegues": r["resumen_pliegues"]})

    log.info("barra: %s, MAE %.2f, MASE %.3f", barra["mejor_por_MAE"], barra["MAE"],
             barra["MASE_a_superar"])
    for n, r in resultados.items():
        f, s = r["final"], r["resumen_pliegues"]
        log.info("  %-24s alpha %-6g final MAE %6.2f MASE %.3f · pliegues MAE medio %6.2f peor %6.2f",
                 n, alpha, f["MAE"], f["MASE"], s["MAE_medio"], s["MAE_peor"])
    log.info("salidas en %s", salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
