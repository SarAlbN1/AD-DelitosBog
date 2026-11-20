#!/usr/bin/env python3
"""Comprueba que el entorno de modelado es reproducible (#41).

Ajusta dos veces el mismo modelo con la misma semilla y exige que las métricas coincidan, que es el
criterio de aceptación de la issue. Usa un modelo de verdad, no una simulación: si un estimador no
recibe `random_state` o una biblioteca introduce no determinismo, esto lo detecta.

Uso::

    python scripts/modelado/comprobar_entorno.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import cargar, fijar_semillas, registrar  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.registro import comprobar_determinismo, sha256_archivo  # noqa: E402

log = logging.getLogger("comprobar_entorno")

#: Modelo de humo: un bosque pequeño, que sí depende de la semilla.
HIPERPARAMETROS = {"n_estimators": 60, "max_depth": 6, "min_samples_leaf": 7}


def ajustar(cfg, semilla: int) -> dict:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor

    sys.path.insert(0, str(RAIZ / "scripts"))
    import baselines as bl

    X = pd.read_csv(cfg.features, parse_dates=["fecha"]).set_index("fecha").sort_index()
    validar_contra_serie(cfg, X.index)

    y = X[cfg.objetivo].astype(float)
    pred_cols = [c for c in X.columns if c != cfg.objetivo]
    datos = X[pred_cols].dropna()
    y = y.reindex(datos.index)

    entrena = datos.index <= cfg.fin_entrenamiento
    den = bl.mae_ingenuo_estacional(y[entrena], cfg.periodo_estacional_mase)

    modelo = RandomForestRegressor(random_state=semilla, n_jobs=1, **HIPERPARAMETROS)
    modelo.fit(datos[entrena], y[entrena])
    pred = pd.Series(modelo.predict(datos[~entrena]), index=datos.index[~entrena])
    # Los conteos no pueden ser negativos; se recorta a cero (ver #42).
    pred = pred.clip(lower=0)
    return bl.metricas(y[~entrena], pred, den)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = cargar()
    log.info("config %s (sha %s) · semilla %s", cfg.ruta.name, cfg.sha256[:12], cfg.semilla)

    if not cfg.features.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py y scripts/features.py",
                  cfg.features)
        return 2

    primera = ajustar(cfg, fijar_semillas(cfg.semilla))
    segunda = ajustar(cfg, fijar_semillas(cfg.semilla))

    if primera != segunda:
        log.error("DOS CORRIDAS CON LA MISMA SEMILLA DIFIEREN")
        log.error("  primera: %s", primera)
        log.error("  segunda: %s", segunda)
        return 1
    log.info("dos corridas con la semilla %s dan las mismas métricas: %s", cfg.semilla, primera)

    datos = {"features": cfg.features.name, "features_sha256": sha256_archivo(cfg.features)}
    if not comprobar_determinismo(cfg, "RandomForestRegressor", HIPERPARAMETROS, primera, datos):
        log.error("las métricas no coinciden con las de la corrida ya registrada con esta huella")
        return 1

    entrada = registrar(cfg, "RandomForestRegressor", HIPERPARAMETROS, primera, datos,
                        extra={"proposito": "comprobación de reproducibilidad del entorno (#41)"})
    log.info("registrada la corrida %s en %s", entrada["huella"], cfg.carpeta_registro)
    for k, v in entrada["versiones"].items():
        log.info("  %s: %s", k, v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
