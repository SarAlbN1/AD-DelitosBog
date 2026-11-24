"""Modelos de referencia, evaluados con el arnés compartido (#42).

Los cuatro comparadores triviales que fija D-04, expresados como **predictores** con la misma firma
que tendrá cualquier modelo. Así pasan por `evaluacion.evaluar` igual que un bosque aleatorio y
usan, por construcción, los mismos pliegues: no hay dos implementaciones del protocolo que puedan
divergir.

Ninguno usa información de `t` ni posterior. El arnés además no se lo permite: solo recibe el tramo
de entrenamiento del pliegue y el índice que debe predecir.

Un detalle que importa para que la comparación sea justa: un comparador necesita la historia
inmediatamente anterior al día que predice, y esa historia **es pasado**, no fuga. El desplazamiento
mínimo es de un día, así que el valor del día evaluado nunca entra en su propia predicción. La
prueba de perturbación lo comprueba en lugar de confiarlo.

Uso::

    python scripts/modelado/referencia.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import cargar, fijar_semillas, registrar  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import VERSION_ARNES, evaluar, huella_pliegues  # noqa: E402
from modelado.registro import sha256_archivo  # noqa: E402

log = logging.getLogger("modelado.referencia")

#: Los cuatro comparadores: nombre -> (desplazamiento, ventana de la media o None).
COMPARADORES: dict[str, tuple[int, int | None]] = {
    "ingenuo": (1, None),
    "ingenuo_estacional": (7, None),
    "media_movil_7": (1, 7),
    "media_movil_28": (1, 28),
}


def predictor(desplazamiento: int, ventana: int | None):
    """Construye un predictor trivial con la firma del arnés."""

    def _predecir(y: pd.Series, X, entrena, indice: pd.DatetimeIndex) -> pd.Series:
        # El desplazamiento usa la serie observada: para predecir t se toma t-k, que ya es pasado.
        # Nunca entra el valor de t, porque el desplazamiento mínimo es 1.
        base = y.shift(desplazamiento)
        serie = base if ventana is None else base.rolling(ventana).mean()
        return serie.reindex(indice)

    return _predecir


def evaluar_todos(cfg, y: pd.Series) -> dict:
    resultados = {n: evaluar(cfg, y, predictor(*spec), nombre=n)
                  for n, spec in COMPARADORES.items()}

    final = {n: r["final"] for n, r in resultados.items()}
    mejor_mae = min(final, key=lambda k: final[k]["MAE"])
    mejor_rmse = min(final, key=lambda k: final[k]["RMSE"])

    # ¿Quién gana en cada pliegue? Es lo que mostró que el orden no es estable.
    ganadores: dict[str, int] = {}
    n_pliegues = len(resultados[mejor_mae]["por_pliegue"])
    for i in range(n_pliegues):
        por = {n: r["por_pliegue"][i][cfg.metrica_principal] for n, r in resultados.items()}
        g = min(por, key=por.get)
        ganadores[g] = ganadores.get(g, 0) + 1

    return {
        "comparadores": resultados,
        "huella_pliegues": huella_pliegues(cfg, y.index),
        "barra": {
            "criterio": cfg.criterio_barra,
            "mejor_por_MAE": mejor_mae, "MAE": final[mejor_mae]["MAE"],
            "mejor_por_RMSE": mejor_rmse, "RMSE": final[mejor_rmse]["RMSE"],
            "MASE_a_superar": final[mejor_mae]["MASE"],
        },
        "ganadores_por_pliegue": ganadores,
        "nota_estabilidad": ("el orden entre comparadores cambia con la ventana: el que gana en la "
                             "evaluación final no gana en todos los pliegues"),
    }


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=None,
                   help="Por defecto, la carpeta de registro de config/modelado.json.")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = cargar()
    fijar_semillas(cfg.semilla)
    if not cfg.serie.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", cfg.serie)
        return 2

    y = (pd.read_csv(cfg.serie, parse_dates=["fecha"]).set_index("fecha")[cfg.objetivo]
         .astype(float).sort_index())
    validar_contra_serie(cfg, y.index)

    r = evaluar_todos(cfg, y)
    salida = a.salida or (cfg.carpeta_registro / "referencia")
    salida.mkdir(parents=True, exist_ok=True)

    filas = []
    for nombre, res in r["comparadores"].items():
        for p_ in res["por_pliegue"]:
            filas.append({"comparador": nombre, **p_})
    pd.DataFrame(filas).to_csv(salida / "metricas_por_pliegue.csv", index=False)
    pd.DataFrame({n: res["final"] for n, res in r["comparadores"].items()}).T.to_csv(
        salida / "metricas_finales.csv")
    (salida / "resumen_referencia.json").write_text(
        json.dumps({k: v for k, v in r.items() if k != "comparadores"} |
                   {"comparadores": {n: {"final": res["final"],
                                         "resumen_pliegues": res["resumen_pliegues"],
                                         "por_pliegue": res["por_pliegue"]}
                                     for n, res in r["comparadores"].items()}},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    # La versión del arnés entra en la huella: si cambia cómo se calcula, es otra corrida.
    datos = {"serie": cfg.serie.name, "serie_sha256": sha256_archivo(cfg.serie),
             "huella_pliegues": r["huella_pliegues"], "version_arnes": VERSION_ARNES}
    for nombre, res in r["comparadores"].items():
        registrar(cfg, f"referencia.{nombre}", {"desplazamiento": COMPARADORES[nombre][0],
                                                "ventana": COMPARADORES[nombre][1]},
                  res["final"], datos,
                  extra={"resumen_pliegues": res["resumen_pliegues"]})

    log.info("pliegues: %s (huella %s)", len(r["comparadores"]["ingenuo"]["por_pliegue"]),
             r["huella_pliegues"])
    for nombre, res in r["comparadores"].items():
        f, s = res["final"], res["resumen_pliegues"]
        log.info("  %-20s final MAE %6.2f MASE %.3f · pliegues MAE medio %6.2f peor %6.2f",
                 nombre, f["MAE"], f["MASE"], s["MAE_medio"], s["MAE_peor"])
    b = r["barra"]
    log.info("barra: %s con MAE %.2f y MASE %.3f", b["mejor_por_MAE"], b["MAE"],
             b["MASE_a_superar"])
    log.info("ganadores por pliegue: %s", r["ganadores_por_pliegue"])
    log.info("salidas en %s", salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
