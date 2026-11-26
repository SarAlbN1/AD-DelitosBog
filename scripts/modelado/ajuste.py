#!/usr/bin/env python3
"""Ajuste de hiperparámetros con validación temporal (#45).

Elige la configuración de cada familia de modelos con los **seis pliegues de origen rodante** y
después evalúa **una sola vez** la elegida en los 184 días finales. Reutiliza sin modificarlos el
arnés (`evaluacion`), los árboles de #44 (`arboles`) y SARIMA/ETS de #43 (`estadisticos`).

## Qué conjunto interviene en cada nivel

* **Selección (nivel externo).** Cada candidata se evalúa en los seis pliegues, que están dentro
  del entrenamiento (hasta `fin_entrenamiento`). Se le pasa la serie **recortada** a ese día, así
  que la selección no puede ver los días de evaluación ni por error. Gana el menor MAE sobre las
  540 fechas de validación combinadas.
* **Ajuste de cada candidata (nivel interno).** En cada pliegue, la candidata se ajusta solo con el
  entrenamiento de ese pliegue. Para SARIMA y ETS, los órdenes o la configuración también se eligen
  ahí dentro, con la regla que se esté probando (ver abajo).
* **Evaluación final.** Solo la candidata elegida pasa por `evaluacion.evaluar`, que entrena con
  todo el entrenamiento y predice los 184 días. Sus métricas no deciden nada.

## Espacio de búsqueda

* **Árboles.** La rejilla de #45: `max_depth` en {3, 5, 8} y `min_samples_leaf` en {7, 14}, sobre los
  demás hiperparámetros de #44. La configuración fija de #44 entra también como candidata, para
  saber si el ajuste la mejora. Desempate: menor profundidad y después mayor hoja mínima.
* **SARIMA y ETS.** Lo que se ajusta es la **regla de selección** dentro de cada tramo, con la malla
  de órdenes y configuraciones de #43:
  - `minimo`: el menor AIC (SARIMA) o AICc (ETS), que es la regla de #43;
  - `desempate`: entre las candidatas a menos de 2 puntos de la mejor, la de menos parámetros. Así
    la elección no depende de diferencias numéricas mínimas entre plataformas (revisión de #118);
  - `mae_interno`: reserva los últimos 90 días del entrenamiento del tramo, elige la candidata con
    menor MAE de un paso en ellos y la reajusta con todo el tramo. Responde a que en «ETS, desde
    2021» la candidata que gana por AICc falla fuera de muestra (#118).
  Si dos reglas empatan, gana la más simple, en ese orden.

La sensibilidad a 2020 de D-04 se corre con la configuración elegida: árboles sin las filas de 2020
y modelos de series desde 2021.

Uso::

    python scripts/modelado/ajuste.py [--salida <carpeta>] [--solo arboles|estadisticos]
"""

from __future__ import annotations

import argparse
import dataclasses
import itertools
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "scripts", RAIZ / "scripts" / "modelado"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from modelado import arboles  # noqa: E402
from modelado import estadisticos as est  # noqa: E402
from modelado import cargar, fijar_semillas, registrar  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import (VERSION_ARNES, evaluar, huella_pliegues,  # noqa: E402
                                 mae_ingenuo_estacional, metricas, pliegues)
from modelado.referencia import evaluar_todos  # noqa: E402
from modelado.registro import sha256_archivo, versiones  # noqa: E402

log = logging.getLogger("modelado.ajuste")

REJILLA_ARBOLES = {"max_depth": [3, 5, 8], "min_samples_leaf": [7, 14]}
REGLAS = ("minimo", "desempate", "mae_interno")
DELTA_CRITERIO = 2.0
DIAS_VALIDACION_INTERNA = 90


# ------------------------------------------------------------------ validación solo en pliegues
def validar_en_pliegues(cfg, y: pd.Series, predictor: Callable, X: pd.DataFrame | None = None
                        ) -> dict:
    """Evalúa un predictor **solo** en los pliegues. Nunca predice la evaluación final.

    Recibe la serie ya recortada al fin del entrenamiento; además comprueba que ningún pliegue
    pase de ese día, por si alguien le pasa la serie completa.
    """
    limite = pd.Timestamp(cfg.fin_entrenamiento)
    if y.index.max() > limite:
        raise ValueError("la selección debe recibir la serie recortada al fin del entrenamiento")
    idx, filas, errores = y.index, [], []
    for p in pliegues(cfg, idx):
        tr, ev = p.mascaras(idx)
        if not ev.any():
            continue
        den = mae_ingenuo_estacional(y[tr], cfg.periodo_estacional_mase)
        pred = predictor(y, X, tr, idx[ev])
        filas.append({"pliegue": p.numero, **metricas(y[ev], pred, den)})
        errores.append((y[ev] - pred.reindex(idx[ev])).abs())
    e = pd.concat(errores)
    return {"MAE_combinado": round(float(e.mean()), 2), "n_validacion": int(e.notna().sum()),
            "por_pliegue": filas}


# ------------------------------------------------------------------ árboles
def candidatas_arboles(nombre: str) -> list[dict]:
    """La configuración fija de #44 y la rejilla de #45 sobre ella."""
    base = dict(arboles.HIPERPARAMETROS[nombre])
    salida = [{"etiqueta": "fija_44", "hiperparametros": base}]
    for d, h in itertools.product(REJILLA_ARBOLES["max_depth"], REJILLA_ARBOLES["min_samples_leaf"]):
        salida.append({"etiqueta": f"profundidad_{d}_hoja_{h}",
                       "hiperparametros": {**base, "max_depth": d, "min_samples_leaf": h}})
    return salida


def clave_arbol(c: dict) -> tuple:
    """Orden de selección: menor MAE; a igualdad, menor profundidad y mayor hoja mínima."""
    hp = c["hiperparametros"]
    prof = hp.get("max_depth")
    return (c["MAE_combinado"], math.inf if prof is None else prof, -hp["min_samples_leaf"])


# ------------------------------------------------------------------ SARIMA y ETS
def candidatas_estadisticas(familia: str, tr: pd.Series) -> list[dict]:
    """Ajusta cada especificación de la malla de #43 con `tr` y devuelve criterio y parámetros."""
    est._silenciar()
    salida = []
    if familia == "sarima":
        d, D, _ = est.elegir_diferenciacion(tr)
        for (p, q), (P, Q) in itertools.product(est.MALLA_PQ, est.MALLA_PQ_ESTACIONAL):
            orden, estacional = (p, d, q), (P, D, Q, est.PERIODO)
            try:
                m = est._ajustar_sarima(tr, orden, estacional)
            except Exception:  # noqa: BLE001 - un orden que no converge no se elige
                continue
            if np.isfinite(m.aic):
                salida.append({"espec": (orden, estacional), "criterio": float(m.aic),
                               "k": p + q + P + Q})
    else:
        for c in est.CONFIG_ETS:
            try:
                r = est._modelo_ets(tr, c).fit(disp=False)
            except Exception:  # noqa: BLE001
                continue
            if np.isfinite(r.aicc):
                k = sum(1 for n in r.param_names if not n.startswith("initial"))
                salida.append({"espec": c, "criterio": float(r.aicc), "k": k})
    if not salida:
        raise RuntimeError(f"ninguna especificación de {familia} convergió")
    return salida


def predecir_estadistico(familia: str, espec, tr: pd.Series, y: pd.Series,
                         indice: pd.DatetimeIndex) -> pd.Series:
    """Ajusta con `tr` y predice `indice` un paso adelante con parámetros fijos (como en #43).

    El filtrado arranca en el primer día de `tr`, no en el de `y`. Los parámetros del ETS incluyen
    los estados iniciales, estimados para el inicio de `tr`: si se aplicaran desde 2020 a un modelo
    entrenado desde 2021, el nivel y la estacionalidad de partida serían los de otra fecha, y con
    estacionalidad multiplicativa el error no se disipa (pliegues 2 y 3: MAE 84,0 y 79,5 en lugar
    de 35,7 y 33,8). Sin `desde`, `tr` empieza donde `y` y nada cambia.
    """
    est._silenciar()
    hasta = y[tr.index.min():indice.max()]
    if familia == "sarima":
        m = est._ajustar_sarima(tr, *espec)
        return m.apply(est._con_frecuencia(hasta)).fittedvalues.reindex(indice)
    aj = est._modelo_ets(tr, espec).fit(disp=False)
    return est._modelo_ets(hasta, espec).smooth(aj.params).fittedvalues.reindex(indice)


def elegir_especificacion(familia: str, tr: pd.Series, regla: str) -> dict:
    """Aplica una regla de selección usando **solo** `tr`."""
    cands = candidatas_estadisticas(familia, tr)
    if regla == "minimo":
        return min(cands, key=lambda c: c["criterio"])
    if regla == "desempate":
        mejor = min(c["criterio"] for c in cands)
        cerca = [c for c in cands if c["criterio"] - mejor < DELTA_CRITERIO]
        return min(cerca, key=lambda c: (c["k"], c["criterio"]))
    if regla == "mae_interno":
        h = DIAS_VALIDACION_INTERNA
        interno, valida = tr.iloc[:-h], tr.index[-h:]
        for c in cands:
            try:
                pred = predecir_estadistico(familia, c["espec"], interno, tr, valida)
                c["mae_interno"] = float((tr.loc[valida] - pred).abs().mean())
            except Exception:  # noqa: BLE001
                c["mae_interno"] = math.inf
        return min(cands, key=lambda c: (c["mae_interno"], c["k"], c["criterio"]))
    raise KeyError(f"regla desconocida: {regla}")


def predictor_estadistico(familia: str, regla: str, desde: pd.Timestamp | None = None,
                          registro: list | None = None) -> Callable:
    """Predictor con la firma del arnés: elige con la regla y el entrenamiento del tramo."""

    def _predecir(y: pd.Series, X, entrena: np.ndarray, indice: pd.DatetimeIndex) -> pd.Series:
        tr = y[entrena]
        if desde is not None:
            tr = tr[tr.index >= desde]
        sel = elegir_especificacion(familia, tr, regla)
        pred = predecir_estadistico(familia, sel["espec"], tr, y, indice)
        if registro is not None:
            registro.append({"espec": sel["espec"], "criterio": sel["criterio"], "k": sel["k"],
                             "pred": pred})
        return pred

    return _predecir


# ------------------------------------------------------------------ búsqueda
def buscar_arboles(cfg, y_sel: pd.Series, semilla: int) -> tuple[list[dict], dict]:
    X_sel = arboles.construir_X(y_sel)
    filas, elegidos = [], {}
    for nombre in arboles.HIPERPARAMETROS:
        resultados = []
        for c in candidatas_arboles(nombre):
            t0 = time.perf_counter()
            pred = arboles.predictor_arbol(nombre, semilla, hiperparametros=c["hiperparametros"])
            r = validar_en_pliegues(cfg, y_sel, pred, X_sel)
            c = {**c, **r, "segundos": round(time.perf_counter() - t0, 1)}
            resultados.append(c)
            log.info("  %-24s %-22s MAE validación %.2f", nombre, c["etiqueta"], c["MAE_combinado"])
        elegidos[nombre] = min(resultados, key=clave_arbol)
        filas += [{"familia": "arboles", "modelo": nombre, **_fila(c)} for c in resultados]
    return filas, elegidos


def buscar_estadisticos(cfg, y_sel: pd.Series) -> tuple[list[dict], dict]:
    filas, elegidos = [], {}
    for familia in ("sarima", "ets"):
        resultados = []
        for regla in REGLAS:
            t0 = time.perf_counter()
            espec: list[dict] = []
            r = validar_en_pliegues(cfg, y_sel, predictor_estadistico(familia, regla,
                                                                      registro=espec))
            c = {"etiqueta": regla, "hiperparametros": {"regla": regla}, **r,
                 "segundos": round(time.perf_counter() - t0, 1),
                 "especificaciones": [_json_espec(e["espec"]) for e in espec]}
            resultados.append(c)
            log.info("  %-24s %-22s MAE validación %.2f", familia, regla, c["MAE_combinado"])
        elegidos[familia] = min(resultados, key=lambda c: (c["MAE_combinado"],
                                                           REGLAS.index(c["etiqueta"])))
        filas += [{"familia": "estadisticos", "modelo": familia, **_fila(c)} for c in resultados]
    return filas, elegidos


def _json_espec(espec) -> str:
    return json.dumps(espec, default=list)


def _fila(c: dict) -> dict:
    f = {"candidata": c["etiqueta"], "hiperparametros": json.dumps(c["hiperparametros"]),
         "MAE_validacion": c["MAE_combinado"], "n_validacion": c["n_validacion"],
         "segundos": c["segundos"]}
    for p in c["por_pliegue"]:
        f[f"MAE_pliegue_{p['pliegue']}"] = p["MAE"]
    if "especificaciones" in c:
        f["especificaciones_por_pliegue"] = " | ".join(c["especificaciones"])
    return f


# ------------------------------------------------------------------ evaluación final
def evaluar_elegido(cfg, y: pd.Series, familia: str, modelo: str, elegido: dict, semilla: int,
                    sensibilidad: bool) -> dict:
    """Protocolo completo (pliegues + evaluación final) para la candidata elegida."""
    if familia == "arboles":
        r = arboles.evaluar_modelo(cfg, y, modelo, semilla, sin_2020=sensibilidad,
                                   hiperparametros=elegido["hiperparametros"])
        r["nombre"] = f"{modelo}{'_sin_2020' if sensibilidad else ''}"
        return r
    desde = pd.Timestamp(year=cfg.anio_atipico + 1, month=1, day=1) if sensibilidad else None
    espec: list[dict] = []
    nombre = f"{modelo}{'_desde_2021' if sensibilidad else ''}"
    r = evaluar(cfg, y, predictor_estadistico(modelo, elegido["etiqueta"], desde, espec),
                nombre=nombre)
    r["especificaciones"] = [_json_espec(e["espec"]) for e in espec]
    numeros = [q["pliegue"] for q in r["por_pliegue"]] + ["final"]
    if len(espec) != len(numeros):
        raise RuntimeError(f"se esperaban {len(numeros)} llamadas al predictor y hubo {len(espec)}")
    r["predicciones"] = pd.DataFrame(
        [{"modelo": nombre, "pliegue": n, "fecha": f.date().isoformat(), "real": float(y.loc[f]),
          "prediccion": round(float(v), 4)}
         for n, e in zip(numeros, espec) for f, v in e["pred"].items()])
    return r


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=None,
                   help="Carpeta de las tablas; con ella, el registro va a <salida>/registro. "
                        "Por defecto, outputs/modelado/ajuste.")
    p.add_argument("--solo", choices=("arboles", "estadisticos"), default=None)
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
    y_sel = y[y.index <= pd.Timestamp(cfg.fin_entrenamiento)]

    salida = a.salida or (cfg.carpeta_registro / "ajuste")
    salida.mkdir(parents=True, exist_ok=True)
    if a.salida is not None:
        cfg = dataclasses.replace(cfg, carpeta_registro=a.salida / "registro")

    inicio = time.perf_counter()
    busqueda, elegidos = [], {}
    if a.solo in (None, "arboles"):
        log.info("búsqueda de árboles en %d pliegues", len(pliegues(cfg, y_sel.index)))
        f, e = buscar_arboles(cfg, y_sel, semilla)
        busqueda += f
        elegidos.update({("arboles", k): v for k, v in e.items()})
    if a.solo in (None, "estadisticos"):
        log.info("búsqueda de reglas de selección de SARIMA y ETS")
        f, e = buscar_estadisticos(cfg, y_sel)
        busqueda += f
        elegidos.update({("estadisticos", k): v for k, v in e.items()})
    segundos_busqueda = round(time.perf_counter() - inicio, 1)

    barra = evaluar_todos(cfg, y)["barra"]
    entorno = os.environ.get("AD_ENTORNO", "local")
    datos = {"serie": cfg.serie.name, "serie_sha256": sha256_archivo(cfg.serie),
             "huella_pliegues": huella_pliegues(cfg, y.index), "version_arnes": VERSION_ARNES,
             "entorno": entorno}
    finales, por_pliegue, predicciones = [], [], []
    for (familia, modelo), el in elegidos.items():
        for sens in (False, True):
            r = evaluar_elegido(cfg, y, familia, modelo, el, semilla, sens)
            finales.append({"modelo": r["nombre"], "familia": familia,
                            "candidata": el["etiqueta"], **r["final"],
                            "MAE_vs_barra": round(r["final"]["MAE"] - barra["MAE"], 2),
                            **{k: v for k, v in r["resumen_pliegues"].items()}})
            por_pliegue += [{"modelo": r["nombre"], **q} for q in r["por_pliegue"]]
            if "predicciones" in r:
                predicciones.append(r["predicciones"])
            registrar(cfg, f"ajuste.{r['nombre']}",
                      {**el["hiperparametros"], "sensibilidad_2020": sens}, r["final"], datos,
                      extra={"resumen_pliegues": r["resumen_pliegues"],
                             "MAE_validacion_seleccion": el["MAE_combinado"],
                             "especificaciones": r.get("especificaciones")})
            log.info("  %-34s final MAE %6.2f (barra %.2f) · pliegues MAE medio %6.2f",
                     r["nombre"], r["final"]["MAE"], barra["MAE"],
                     r["resumen_pliegues"]["MAE_medio"])

    pd.DataFrame(busqueda).to_csv(salida / "busqueda.csv", index=False)
    pd.DataFrame(finales).to_csv(salida / "metricas_finales.csv", index=False)
    pd.DataFrame(por_pliegue).to_csv(salida / "metricas_por_pliegue.csv", index=False)
    if predicciones:
        pd.concat(predicciones).to_csv(salida / "predicciones_por_pliegue.csv", index=False)
    (salida / "seleccion.json").write_text(json.dumps({
        "criterio": "menor MAE sobre las fechas de validación combinadas de los pliegues de "
                    "origen rodante; la evaluación final no interviene",
        "pliegues": [{"pliegue": q.numero, "fin_entrenamiento": str(q.fin_entrenamiento.date()),
                      "fin_evaluacion": str(q.fin_evaluacion.date())}
                     for q in pliegues(cfg, y_sel.index)],
        "espacio": {"arboles": {"rejilla": REJILLA_ARBOLES,
                                "fija_44": arboles.HIPERPARAMETROS,
                                "desempate": "menor max_depth y después mayor min_samples_leaf"},
                    "estadisticos": {"reglas": list(REGLAS), "delta_criterio": DELTA_CRITERIO,
                                     "dias_validacion_interna": DIAS_VALIDACION_INTERNA,
                                     "desempate": "la regla más simple, en el orden de 'reglas'"}},
        "semilla": semilla,
        "elegidos": {f"{f}.{m}": {"candidata": e["etiqueta"],
                                  "hiperparametros": e["hiperparametros"],
                                  "MAE_validacion": e["MAE_combinado"]}
                     for (f, m), e in elegidos.items()},
        "barra": barra,
        "segundos_busqueda": segundos_busqueda,
        "entorno": entorno,
        "commit": os.environ.get("AD_COMMIT", "no indicado"),
        "versiones": versiones(),
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log.info("búsqueda en %.0f s; salidas en %s", segundos_busqueda, salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
