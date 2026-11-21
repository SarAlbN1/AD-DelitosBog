#!/usr/bin/env python3
"""Modelos de referencia y protocolo de evaluación (#38).

Implementa los cuatro comparadores triviales y el esquema de validación que fija D-04, y mide todo
con las mismas métricas. Sirve para dos cosas: fijar la barra que cualquier modelo debe superar, y
dejar el arnés de evaluación listo para la tercera entrega.

## Los comparadores

* `ingenuo`: la predicción de `t` es el valor de `t-1`.
* `ingenuo_estacional`: la predicción de `t` es el valor de `t-7`, el mismo día de la semana.
* `media_movil_7` y `media_movil_28`: la media de los 7 o 28 días anteriores a `t`.

Ninguno usa información de `t` ni posterior. Son los mismos que `scripts/features.py` produce como
rezagos y medias previas, así que la barra se calcula con las mismas series que alimentan al modelo.

## El protocolo

* **Horizonte** un día (`t+1`).
* **Partición** fija: entrenamiento hasta `--fin-entrenamiento`, evaluación después. Sin barajar.
* **Validación de origen rodante** dentro del entrenamiento, para elegir hiperparámetros sin ver el
  conjunto de evaluación. Cada pliegue entrena con todo lo anterior a su origen y evalúa el tramo
  siguiente, de modo que el pasado nunca contiene futuro.
* **La barra** es el mejor de los cuatro comparadores *sobre el mismo conjunto en el que se evalúa
  el modelo*, no un comparador fijado de antemano. El orden entre ellos cambia con la ventana.

## Las métricas

Con `y` el valor observado y `ŷ` la predicción, sobre `n` días del conjunto de evaluación:

* **MAE** = media de |y − ŷ|. Principal, porque se lee en víctimas al día.
* **RMSE** = raíz de la media de (y − ŷ)². Secundaria, penaliza más los errores grandes.
* **MAPE** = media de |y − ŷ| / y, en porcentaje. Informativa: es asimétrica y castiga más la
  sobreestimación.
* **MASE** = MAE / MAE del comparador ingenuo estacional *en el conjunto de entrenamiento*. Es la
  única de las cuatro que es adimensional y comparable entre series y entre ventanas. Un MASE menor
  que 1 significa que el método mejora al ingenuo estacional; mayor que 1, que lo empeora.

MASE se calcula con el denominador del entrenamiento, no del conjunto de evaluación, para que el
valor no dependa de lo que se quiere medir.

Uso::

    python scripts/baselines.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("baselines")

#: Comparadores: nombre -> (desplazamiento, ventana). Ventana None significa solo el rezago.
COMPARADORES: dict[str, tuple[int, int | None]] = {
    "ingenuo": (1, None),
    "ingenuo_estacional": (7, None),
    "media_movil_7": (1, 7),
    "media_movil_28": (1, 28),
}

#: Periodo estacional de la serie: la semana.
PERIODO_ESTACIONAL = 7

# Las tres funciones del cálculo viven en scripts/modelado/evaluacion.py y se importan, no se
# reimplementan. El criterio de #42 es que los comparadores y los modelos usen exactamente el
# mismo protocolo, y eso solo está garantizado si hay una única definición. Antes había dos.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modelado.evaluacion import mae_ingenuo_estacional, metricas  # noqa: E402


def predecir(y: pd.Series, desplazamiento: int, ventana: int | None) -> pd.Series:
    """Predicción de un comparador. Nunca usa el valor de t ni posteriores."""
    base = y.shift(desplazamiento)
    return base if ventana is None else base.rolling(ventana).mean()


def pliegues_origen_rodante(idx: pd.DatetimeIndex, n: int, dias: int,
                            minimo_entrenamiento: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Orígenes de la validación rodante: `n` pliegues de `dias` días, el último al final.

    Devuelve, por pliegue, el último día de su entrenamiento y el último de su evaluación. Cada
    pliegue entrena con todo lo anterior a su origen, así que el conjunto de entrenamiento crece y
    nunca contiene días posteriores a los que evalúa.
    """
    pliegues = []
    fin = len(idx)
    for _ in range(n):
        ini_eval = fin - dias
        if ini_eval <= minimo_entrenamiento:
            break
        pliegues.append((idx[ini_eval - 1], idx[fin - 1]))
        fin = ini_eval
    return list(reversed(pliegues))


def evaluar(y: pd.Series, fin_entrenamiento: str, pliegues: int, dias_pliegue: int,
            minimo_entrenamiento: int) -> dict:
    entrena = y[y.index <= fin_entrenamiento]
    evalua = y[y.index > fin_entrenamiento]
    if entrena.empty or evalua.empty:
        raise SystemExit(f"la partición en {fin_entrenamiento} deja un lado vacío")

    # El denominador del MASE sale del entrenamiento, nunca de la evaluación.
    den = mae_ingenuo_estacional(entrena, PERIODO_ESTACIONAL)

    resultados = {}
    for nombre, (desp, vent) in COMPARADORES.items():
        # La predicción se calcula sobre la serie completa para que el primer día de evaluación
        # tenga su historia, y después se recorta al tramo de evaluación.
        pred = predecir(y, desp, vent)
        resultados[nombre] = metricas(evalua, pred.reindex(evalua.index), den)

    mejor_mae = min(resultados, key=lambda k: resultados[k]["MAE"])
    mejor_rmse = min(resultados, key=lambda k: resultados[k]["RMSE"])

    # Validación de origen rodante dentro del entrenamiento.
    rodante = []
    for fin_tr, fin_ev in pliegues_origen_rodante(entrena.index, pliegues, dias_pliegue,
                                                  minimo_entrenamiento):
        tr = entrena[entrena.index <= fin_tr]
        ev = entrena[(entrena.index > fin_tr) & (entrena.index <= fin_ev)]
        den_pliegue = mae_ingenuo_estacional(tr, PERIODO_ESTACIONAL)
        fila = {"fin_entrenamiento": fin_tr.date().isoformat(),
                "fin_evaluacion": fin_ev.date().isoformat(),
                "dias_entrenamiento": int(len(tr)), "dias_evaluacion": int(len(ev))}
        for nombre, (desp, vent) in COMPARADORES.items():
            pred = predecir(y, desp, vent).reindex(ev.index)
            fila[nombre] = metricas(ev, pred, den_pliegue)["MAE"]
        rodante.append(fila)

    return {
        "particion": {
            "entrenamiento": [entrena.index.min().date().isoformat(),
                              entrena.index.max().date().isoformat()],
            "evaluacion": [evalua.index.min().date().isoformat(),
                           evalua.index.max().date().isoformat()],
            "dias_entrenamiento": int(len(entrena)), "dias_evaluacion": int(len(evalua)),
            "media_evaluacion": round(float(evalua.mean()), 1),
            "sin_barajar": True,
        },
        "denominador_mase": round(den, 2),
        "comparadores": resultados,
        "barra": {
            "criterio": "el mejor de los cuatro comparadores sobre el conjunto de evaluación (D-04)",
            "mejor_por_MAE": mejor_mae, "MAE": resultados[mejor_mae]["MAE"],
            "mejor_por_RMSE": mejor_rmse, "RMSE": resultados[mejor_rmse]["RMSE"],
            "MASE_a_superar": resultados[mejor_mae]["MASE"],
        },
        "validacion_rodante": rodante,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--serie", type=Path, default=Path("data/processed/serie_objetivo_diaria.csv"))
    p.add_argument("--fin-entrenamiento", default="2025-04-30", help="Partición de D-04.")
    p.add_argument("--pliegues", type=int, default=6)
    p.add_argument("--dias-pliegue", type=int, default=90)
    p.add_argument("--minimo-entrenamiento", type=int, default=365,
                   help="Días mínimos de entrenamiento en un pliegue rodante.")
    p.add_argument("--salida", type=Path, default=Path("outputs/baselines"))
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not a.serie.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", a.serie)
        return 2

    y = (pd.read_csv(a.serie, parse_dates=["fecha"]).set_index("fecha")["victimas"]
         .astype(float).sort_index())
    r = evaluar(y, a.fin_entrenamiento, a.pliegues, a.dias_pliegue, a.minimo_entrenamiento)

    a.salida.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(r["comparadores"]).T.to_csv(a.salida / "comparadores.csv")
    pd.DataFrame(r["validacion_rodante"]).to_csv(a.salida / "validacion_rodante.csv", index=False)
    (a.salida / "resumen_baselines.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("partición: entrena %s días hasta %s · evalúa %s días",
             r["particion"]["dias_entrenamiento"], a.fin_entrenamiento,
             r["particion"]["dias_evaluacion"])
    for nombre, m in r["comparadores"].items():
        log.info("  %-20s MAE %6.2f  RMSE %6.2f  MAPE %5.2f%%  MASE %.3f",
                 nombre, m["MAE"], m["RMSE"], m["MAPE"], m["MASE"])
    b = r["barra"]
    log.info("barra a superar: %s con MAE %.2f (MASE %.3f) · en RMSE gana %s con %.2f",
             b["mejor_por_MAE"], b["MAE"], b["MASE_a_superar"], b["mejor_por_RMSE"], b["RMSE"])
    log.info("validación rodante: %s pliegues de %s días", len(r["validacion_rodante"]),
             a.dias_pliegue)
    log.info("salidas en %s", a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
