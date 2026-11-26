#!/usr/bin/env python3
"""Modelos estadísticos de series de tiempo: SARIMA y ETS, con diagnóstico de residuos (#43).

Los dos pasan por el mismo arnés que los comparadores de #42 (`evaluacion.evaluar`): mismos
pliegues, misma evaluación final, mismo contrato de predictor. Predicen el día `t` con la serie hasta
`t-1`, que es el horizonte de un día que fija D-04.

## Cómo se predice un día sin mirar ese día

El modelo se ajusta **solo con el entrenamiento** del tramo. Después se aplica con parámetros fijos
a la serie observada hasta el último día a predecir, y la predicción de `t` es el valor ajustado un
paso adelante: en un modelo de espacio de estados ese valor depende de `y[:t]` y nunca de `y[t]`. Es
lo mismo que hacer un pronóstico de un día repetido con cada nuevo dato, sin reajustar cada día.
`evaluacion.sin_fuga` lo comprueba alterando `y[t:]` (ver `tests/test_estadisticos.py`).

## Selección con datos de entrenamiento solamente

Es el criterio de aceptación de la issue, y tiene una trampa: los pliegues de validación están
**dentro** del periodo de entrenamiento final. Si se eligieran los órdenes una vez con todo ese
periodo, cada pliegue se evaluaría con un modelo elegido viendo sus propios días. Por eso la
selección se repite **dentro de cada llamada al predictor**, con el entrenamiento de ese tramo. La
evaluación final elige con el entrenamiento final y nunca ve los 184 días de prueba.

* **Diferenciación.** `d` sale de las pruebas ADF y KPSS sobre el entrenamiento; `D`, de la fuerza de
  la estacionalidad semanal (STL, umbral 0,64 de Wang, Smith y Hyndman, 2006). Se fijan **antes** de
  buscar los demás órdenes porque el AIC no es comparable entre modelos con distinta diferenciación.
* **Órdenes** `(p, q)` y `(P, Q)`: malla pequeña por AIC.
* **ETS:** las configuraciones por AICc.

## Qué no cubre

Solo modela la estacionalidad semanal. No incluye la anual ni los festivos como regresores: son
parte de lo que los modelos con variables derivadas (#44) sí usan, y es una diferencia a leer en
la comparación del #46, no un defecto de este script.

## Sensibilidad a 2020

D-04 pide comprobar qué pasa sin 2020. En un modelo de series no se pueden quitar las filas de un año
sin romper la continuidad, así que la variante entrena **desde 2021-01-01**.

Uso::

    python scripts/modelado/estadisticos.py
"""

from __future__ import annotations

import argparse
import dataclasses
import itertools
import json
import logging
import sys
import warnings
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "scripts", RAIZ / "scripts" / "modelado"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from modelado import cargar, fijar_semillas, registrar  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import VERSION_ARNES, evaluar, huella_pliegues, particion  # noqa: E402
from modelado.referencia import evaluar_todos  # noqa: E402
from modelado.registro import sha256_archivo  # noqa: E402

log = logging.getLogger("modelado.estadisticos")

PERIODO = 7
#: Fuerza de la estacionalidad por encima de la cual se diferencia estacionalmente.
UMBRAL_ESTACIONALIDAD = 0.64
#: Malla de órdenes. `d` y `D` no entran: se fijan antes con las pruebas de estacionariedad.
MALLA_PQ = [(p, q) for p in (0, 1, 2) for q in (0, 1, 2)]
MALLA_PQ_ESTACIONAL = [(0, 1), (1, 0), (1, 1)]
#: Configuraciones ETS: (error, tendencia, tendencia amortiguada, estacionalidad).
CONFIG_ETS = [("add", None, False, "add"),
              ("add", "add", True, "add"),
              ("add", None, False, "mul"),
              ("add", "add", True, "mul")]


def _silenciar():
    warnings.filterwarnings("ignore")


def _con_frecuencia(s: pd.Series) -> pd.Series:
    s = s.copy()
    s.index = pd.DatetimeIndex(s.index, freq="D")
    return s


# ------------------------------------------------------------------ estacionariedad
def pruebas_estacionariedad(y: pd.Series) -> pd.DataFrame:
    """ADF y KPSS sobre la serie y sus diferencias. Se usa solo el entrenamiento.

    ADF: H0 = raíz unitaria (no estacionaria); se rechaza con p < 0,05.
    KPSS: H0 = estacionaria alrededor de un nivel; se rechaza con p < 0,05.
    Una serie se considera estacionaria si ADF rechaza y KPSS no.
    """
    from statsmodels.tsa.stattools import adfuller, kpss
    _silenciar()
    variantes = {
        "nivel": y,
        "diferencia_1": y.diff(),
        f"diferencia_estacional_{PERIODO}": y.diff(PERIODO),
        f"diferencia_1_y_estacional_{PERIODO}": y.diff().diff(PERIODO),
    }
    filas = []
    for nombre, s in variantes.items():
        s = s.dropna()
        adf_p = float(adfuller(s, autolag="AIC")[1])
        kpss_p = float(kpss(s, regression="c", nlags="auto")[1])
        filas.append({"serie": nombre, "n": len(s), "adf_p": round(adf_p, 4),
                      "kpss_p": round(kpss_p, 4),
                      "estacionaria": bool(adf_p < 0.05 and kpss_p >= 0.05)})
    return pd.DataFrame(filas)


def elegir_diferenciacion(y: pd.Series) -> tuple[int, int, float]:
    """`(d, D, fuerza)` con solo el entrenamiento.

    `D` = 1 si la estacionalidad semanal es fuerte. `d` = 0 si, tras la diferenciación estacional
    elegida, la serie ya pasa ADF y KPSS; si no, 1.
    """
    from statsmodels.tsa.seasonal import STL
    from statsmodels.tsa.stattools import adfuller, kpss
    _silenciar()
    r = STL(_con_frecuencia(y), period=PERIODO, robust=True).fit()
    fuerza = float(max(0.0, 1 - np.var(r.resid) / np.var(r.resid + r.seasonal)))
    D = int(fuerza > UMBRAL_ESTACIONALIDAD)
    s = (y.diff(PERIODO) if D else y).dropna()
    estacionaria = adfuller(s, autolag="AIC")[1] < 0.05 and kpss(s, regression="c",
                                                                  nlags="auto")[1] >= 0.05
    return (0 if estacionaria else 1), D, round(fuerza, 3)


# ------------------------------------------------------------------ SARIMA
def _ajustar_sarima(y: pd.Series, orden, estacional):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    return SARIMAX(_con_frecuencia(y), order=orden, seasonal_order=estacional,
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def seleccionar_sarima(y: pd.Series) -> dict:
    """Elige `(p,d,q)(P,D,Q,7)` por AIC sobre `y`, con `d` y `D` fijados antes por las pruebas."""
    _silenciar()
    d, D, fuerza = elegir_diferenciacion(y)
    candidatos = []
    for (p, q), (P, Q) in itertools.product(MALLA_PQ, MALLA_PQ_ESTACIONAL):
        try:
            m = _ajustar_sarima(y, (p, d, q), (P, D, Q, PERIODO))
        except Exception:  # un orden que no converge no se elige
            continue
        if np.isfinite(m.aic):
            candidatos.append({"orden": (p, d, q), "estacional": (P, D, Q, PERIODO),
                               "aic": float(m.aic)})
    if not candidatos:
        raise RuntimeError("ningún orden SARIMA convergió")
    mejor = min(candidatos, key=lambda c: c["aic"])
    return {**mejor, "d": d, "D": D, "fuerza_estacional": fuerza, "candidatos": len(candidatos)}


def predictor_sarima(orden=None, estacional=None, desde: pd.Timestamp | None = None,
                     registro: list | None = None) -> Callable:
    """Predictor con la firma del arnés. Sin `orden`, selecciona con el entrenamiento del tramo."""

    def _predecir(y: pd.Series, X, entrena: np.ndarray, indice: pd.DatetimeIndex) -> pd.Series:
        tr = y[entrena]
        if desde is not None:
            tr = tr[tr.index >= desde]
        sel = ({"orden": orden, "estacional": estacional} if orden is not None
               else seleccionar_sarima(tr))
        modelo = _ajustar_sarima(tr, sel["orden"], sel["estacional"])
        # Parámetros fijos sobre la serie observada hasta el último día a predecir: el valor
        # ajustado de `t` es la predicción un paso adelante y no usa y[t].
        hasta = _con_frecuencia(y[:indice.max()])
        pred = modelo.apply(hasta).fittedvalues.reindex(indice)
        if registro is not None:
            registro.append({"espec": {"orden": list(sel["orden"]),
                                       "estacional": list(sel["estacional"])},
                             "criterio": sel.get("aic", float(modelo.aic)), "pred": pred})
        return pred

    return _predecir


# ------------------------------------------------------------------ ETS
def _modelo_ets(y: pd.Series, cfg_ets):
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    error, tendencia, amortiguada, estacion = cfg_ets
    return ETSModel(_con_frecuencia(y), error=error, trend=tendencia, damped_trend=amortiguada,
                    seasonal=estacion, seasonal_periods=PERIODO)


def seleccionar_ets(y: pd.Series) -> dict:
    _silenciar()
    candidatos = []
    for c in CONFIG_ETS:
        try:
            r = _modelo_ets(y, c).fit(disp=False)
        except Exception:
            continue
        if np.isfinite(r.aicc):
            candidatos.append({"config": c, "aicc": float(r.aicc)})
    if not candidatos:
        raise RuntimeError("ninguna configuración ETS convergió")
    return {**min(candidatos, key=lambda c: c["aicc"]), "candidatos": len(candidatos)}


def predictor_ets(config=None, desde: pd.Timestamp | None = None,
                  registro: list | None = None) -> Callable:
    def _predecir(y: pd.Series, X, entrena: np.ndarray, indice: pd.DatetimeIndex) -> pd.Series:
        _silenciar()
        tr = y[entrena]
        if desde is not None:
            tr = tr[tr.index >= desde]
        sel = {"config": config} if config is not None else seleccionar_ets(tr)
        ajustado = _modelo_ets(tr, sel["config"]).fit(disp=False)
        hasta = y[:indice.max()]
        pred = _modelo_ets(hasta, sel["config"]).smooth(ajustado.params).fittedvalues.reindex(indice)
        if registro is not None:
            registro.append({"espec": {"config": list(sel["config"])},
                             "criterio": sel.get("aicc", float(ajustado.aicc)), "pred": pred})
        return pred

    return _predecir


# ------------------------------------------------------------------ evaluación y diagnóstico
def evaluar_modelo(cfg, y: pd.Series, familia: str, desde_2021: bool = False) -> dict:
    """Evalúa SARIMA o ETS con el protocolo completo, y devuelve predicciones y órdenes elegidos."""
    desde = pd.Timestamp(year=cfg.anio_atipico + 1, month=1, day=1) if desde_2021 else None
    llamadas: list[dict] = []
    fabrica = {"sarima": predictor_sarima, "ets": predictor_ets}[familia]
    etiqueta = familia + ("_desde_2021" if desde_2021 else "")
    r = evaluar(cfg, y, fabrica(desde=desde, registro=llamadas), nombre=etiqueta)
    n = len(r["por_pliegue"])
    if len(llamadas) != n + 1:
        raise RuntimeError(f"se esperaban {n + 1} llamadas al predictor y hubo {len(llamadas)}")
    numeros = [p["pliegue"] for p in r["por_pliegue"]] + ["final"]
    filas, elegidos = [], []
    for numero, ll in zip(numeros, llamadas):
        for fecha, valor in ll["pred"].items():
            filas.append({"modelo": etiqueta, "pliegue": numero, "fecha": fecha.date().isoformat(),
                          "real": float(y.loc[fecha]), "prediccion": round(float(valor), 4)})
        elegidos.append({"modelo": etiqueta, "pliegue": numero,
                         "especificacion": json.dumps(ll["espec"]),
                         "criterio": round(ll["criterio"], 2)})
    r["predicciones"] = pd.DataFrame(filas)
    r["elegidos"] = pd.DataFrame(elegidos)
    return r


def diagnostico_residuos(cfg, y: pd.Series, familia: str, especificacion,
                         lags=(7, 14, 28)) -> dict:
    """Ljung-Box sobre los residuos del ajuste final, con el entrenamiento solamente.

    Los grados de libertad se descuentan con los parámetros de dinámica (no con los estados
    iniciales). Un p pequeño dice que queda autocorrelación sin modelar.
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox
    _silenciar()
    tr_f, _ = particion(cfg, y.index)
    tr = y[tr_f]
    if familia == "sarima":
        orden, estacional = especificacion
        m = _ajustar_sarima(tr, orden, estacional)
        residuos = m.resid.iloc[PERIODO + orden[1] + estacional[1] * PERIODO:]
        gl = orden[0] + orden[2] + estacional[0] + estacional[2]
    else:
        m = _modelo_ets(tr, especificacion).fit(disp=False)
        residuos = m.resid.iloc[PERIODO:]
        gl = sum(1 for k in m.param_names if not k.startswith("initial"))
    lb = acorr_ljungbox(residuos, lags=list(lags), model_df=min(gl, min(lags) - 1))
    return {"modelo": familia, "n_residuos": int(len(residuos)),
            "media": round(float(residuos.mean()), 3), "desv": round(float(residuos.std()), 3),
            "grados_de_libertad": int(gl),
            **{f"ljung_box_p_{k}": round(float(lb.loc[k, "lb_pvalue"]), 4) for k in lags},
            "autocorrelacion_residual": bool((lb["lb_pvalue"] < 0.05).any()),
            "criterio": "p < 0,05 en algún rezago: queda autocorrelación sin modelar"}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=None,
                   help="Carpeta de las tablas. Con ella, el registro de corridas también va a "
                        "<salida>/registro. Por defecto, outputs/modelado/estadisticos.")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _silenciar()

    cfg = cargar()
    fijar_semillas(cfg.semilla)
    if not cfg.serie.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", cfg.serie)
        return 2
    y = (pd.read_csv(cfg.serie, parse_dates=["fecha"]).set_index("fecha")[cfg.objetivo]
         .astype(float).sort_index())
    validar_contra_serie(cfg, y.index)

    salida = a.salida or (cfg.carpeta_registro / "estadisticos")
    salida.mkdir(parents=True, exist_ok=True)
    if a.salida is not None:
        cfg = dataclasses.replace(cfg, carpeta_registro=a.salida / "registro")

    tr_final, _ = particion(cfg, y.index)
    est = pruebas_estacionariedad(y[tr_final])
    est.to_csv(salida / "estacionariedad.csv", index=False)
    log.info("estacionariedad (entrenamiento final):\n%s", est.to_string(index=False))

    barra = evaluar_todos(cfg, y)["barra"]
    resultados: dict[str, dict] = {}
    for familia in ("sarima", "ets"):
        for desde in (False, True):
            r = evaluar_modelo(cfg, y, familia, desde_2021=desde)
            resultados[r["nombre"]] = r
            log.info("  %-14s final MAE %6.2f MASE %.3f", r["nombre"], r["final"]["MAE"],
                     r["final"]["MASE"])

    pd.concat([r["predicciones"] for r in resultados.values()]).to_csv(
        salida / "predicciones_por_pliegue.csv", index=False)
    pd.concat([r["elegidos"] for r in resultados.values()]).to_csv(
        salida / "seleccion_por_pliegue.csv", index=False)
    pd.DataFrame([{"modelo": n, "pliegue": q["pliegue"], **{k: q[k] for k in cfg.metricas}}
                  for n, r in resultados.items() for q in r["por_pliegue"]]).to_csv(
        salida / "metricas_por_pliegue.csv", index=False)
    finales = pd.DataFrame({n: r["final"] for n, r in resultados.items()}).T
    finales["MAE_vs_barra"] = (finales["MAE"] - barra["MAE"]).round(2)
    finales.to_csv(salida / "metricas_finales.csv", index_label="modelo")

    # Diagnóstico de los residuos con la especificación elegida en la evaluación final.
    diag = []
    for familia in ("sarima", "ets"):
        fila = resultados[familia]["elegidos"].query("pliegue == 'final'").iloc[0]
        espec = json.loads(fila["especificacion"])
        arg = (tuple(espec["orden"]), tuple(espec["estacional"])) if familia == "sarima" \
            else tuple(espec["config"])
        diag.append({**diagnostico_residuos(cfg, y, familia, arg),
                     "especificacion": fila["especificacion"]})
    pd.DataFrame(diag).to_csv(salida / "diagnostico_residuos.csv", index=False)

    (salida / "resumen_estadisticos.json").write_text(json.dumps({
        "barra": barra,
        "malla": {"pq": MALLA_PQ, "pq_estacional": MALLA_PQ_ESTACIONAL, "ets": CONFIG_ETS,
                  "umbral_estacionalidad": UMBRAL_ESTACIONALIDAD},
        "diagnostico_residuos": diag,
        "modelos": {n: {"final": r["final"], "resumen_pliegues": r["resumen_pliegues"],
                        "por_pliegue": r["por_pliegue"]} for n, r in resultados.items()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    datos = {"serie": cfg.serie.name, "serie_sha256": sha256_archivo(cfg.serie),
             "huella_pliegues": huella_pliegues(cfg, y.index), "version_arnes": VERSION_ARNES}
    for n, r in resultados.items():
        registrar(cfg, f"estadisticos.{n}", {"familia": n.split("_")[0],
                                             "desde_2021": n.endswith("_desde_2021"),
                                             "periodo": PERIODO,
                                             "seleccion": "por tramo, solo con su entrenamiento"},
                  r["final"], datos, extra={"resumen_pliegues": r["resumen_pliegues"]})

    log.info("barra: %s, MAE %.2f, MASE %.3f", barra["mejor_por_MAE"], barra["MAE"],
             barra["MASE_a_superar"])
    log.info("residuos:\n%s", pd.DataFrame(diag).drop(columns=["criterio", "especificacion"])
             .to_string(index=False))
    log.info("salidas en %s", salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
