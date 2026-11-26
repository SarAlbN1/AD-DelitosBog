"""Pruebas del ajuste de hiperparámetros (#45), con una serie SINTÉTICA.

El criterio de aceptación de la issue es que el periodo de prueba final no participe en el ajuste.
Se prueba de tres maneras: la validación rechaza una serie que pase del fin del entrenamiento, la
selección no cambia si se altera la evaluación, y los predictores ajustados pasan `sin_fuga`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import ajuste, arboles  # noqa: E402
from modelado.evaluacion import particion, pliegues, sin_fuga  # noqa: E402

PEQUENO_BOSQUE = {"n_estimators": 15, "min_samples_leaf": 7, "max_features": 0.5, "max_depth": 3}


class Cfg:
    fin_entrenamiento = "2022-06-30"
    pliegues = 3
    dias_pliegue = 45
    minimo_entrenamiento = 200
    periodo_estacional_mase = 7
    metricas = ("MAE", "RMSE", "MAPE", "MASE")
    metrica_principal = "MAE"
    criterio_barra = "mejor_comparador_en_evaluacion"
    indicador_atipico = "anio_atipico_2020"
    anio_atipico = 2020


def serie(n: int = 1000, inicio: str = "2020-01-01", semilla: int = 5) -> pd.Series:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, periods=n, freq="D", name="fecha")
    v = 300 + np.arange(n) * 0.05 + 25 * np.sin(2 * np.pi * idx.dayofweek / 7)
    return pd.Series((v + rng.normal(0, 12, n)).round(), index=idx, name="victimas")


def recortada(cfg, y):
    return y[y.index <= pd.Timestamp(cfg.fin_entrenamiento)]


def test_la_validacion_rechaza_la_serie_con_dias_de_evaluacion():
    cfg, y = Cfg(), serie()
    pred = arboles.predictor_arbol("bosque_aleatorio", 42, hiperparametros=PEQUENO_BOSQUE)
    with pytest.raises(ValueError, match="recortada"):
        ajuste.validar_en_pliegues(cfg, y, pred, arboles.construir_X(y))


def test_la_validacion_solo_predice_dias_de_los_pliegues():
    cfg, y = Cfg(), serie()
    ys = recortada(cfg, y)
    pedidos = []

    def espia(y_, X, entrena, indice):
        pedidos.append(indice)
        return pd.Series(float(y_[entrena].mean()), index=indice)

    r = ajuste.validar_en_pliegues(cfg, ys, espia)
    dias = pd.DatetimeIndex(np.concatenate([p.values for p in pedidos]))
    assert dias.max() <= pd.Timestamp(cfg.fin_entrenamiento)
    assert len(pedidos) == len(pliegues(cfg, ys.index))
    assert r["n_validacion"] == Cfg.pliegues * Cfg.dias_pliegue


def test_la_seleccion_de_arboles_no_cambia_si_se_altera_la_evaluacion():
    """Criterio de la issue: el periodo de prueba final no participa en el ajuste."""
    cfg, y = Cfg(), serie()
    _, ev = particion(cfg, y.index)
    otra = y.copy()
    otra[ev] = otra[ev] * 3 + 500
    pred = arboles.predictor_arbol("bosque_aleatorio", 42, hiperparametros=PEQUENO_BOSQUE)
    a = ajuste.validar_en_pliegues(cfg, recortada(cfg, y), pred, arboles.construir_X(recortada(cfg, y)))
    b = ajuste.validar_en_pliegues(cfg, recortada(cfg, otra), pred,
                                   arboles.construir_X(recortada(cfg, otra)))
    assert a == b


def test_rejilla_de_arboles_incluye_la_configuracion_de_44():
    for nombre in arboles.HIPERPARAMETROS:
        c = ajuste.candidatas_arboles(nombre)
        assert len(c) == 1 + 3 * 2
        assert c[0]["hiperparametros"] == arboles.HIPERPARAMETROS[nombre]
        assert {(x["hiperparametros"].get("max_depth"), x["hiperparametros"]["min_samples_leaf"])
                for x in c[1:]} == {(d, h) for d in (3, 5, 8) for h in (7, 14)}


def test_desempate_de_arboles_menor_profundidad_y_mayor_hoja():
    cands = [{"MAE_combinado": 30.0, "hiperparametros": {"max_depth": 8, "min_samples_leaf": 14}},
             {"MAE_combinado": 30.0, "hiperparametros": {"max_depth": 3, "min_samples_leaf": 7}},
             {"MAE_combinado": 30.0, "hiperparametros": {"max_depth": 3, "min_samples_leaf": 14}},
             {"MAE_combinado": 30.0, "hiperparametros": {"max_depth": None, "min_samples_leaf": 3}}]
    elegido = min(cands, key=ajuste.clave_arbol)
    assert elegido["hiperparametros"] == {"max_depth": 3, "min_samples_leaf": 14}


def test_regla_de_desempate_estadistica(monkeypatch):
    """Entre candidatas a menos de 2 puntos de la mejor gana la de menos parámetros."""
    cands = [{"espec": "a", "criterio": 100.0, "k": 4},
             {"espec": "b", "criterio": 101.5, "k": 2},
             {"espec": "c", "criterio": 103.0, "k": 1}]
    monkeypatch.setattr(ajuste, "candidatas_estadisticas", lambda f, tr: [dict(c) for c in cands])
    tr = serie(300)
    assert ajuste.elegir_especificacion("ets", tr, "minimo")["espec"] == "a"
    assert ajuste.elegir_especificacion("ets", tr, "desempate")["espec"] == "b"


def test_regla_mae_interno_solo_usa_el_tramo(monkeypatch):
    """La validación interna son los últimos días de `tr`: nada posterior entra."""
    vistos = []

    def falso_predecir(familia, espec, tr_int, y_, indice):
        vistos.append((tr_int.index.max(), y_.index.max(), indice.max()))
        return pd.Series(0.0 if espec == "buena" else 50.0, index=indice) + y_.loc[indice]

    monkeypatch.setattr(ajuste, "candidatas_estadisticas", lambda f, tr: [
        {"espec": "mala", "criterio": 1.0, "k": 1}, {"espec": "buena", "criterio": 9.0, "k": 3}])
    monkeypatch.setattr(ajuste, "predecir_estadistico", falso_predecir)
    tr = serie(400)
    assert ajuste.elegir_especificacion("ets", tr, "mae_interno")["espec"] == "buena"
    for fin_interno, fin_y, fin_pred in vistos:
        assert fin_interno < tr.index[-ajuste.DIAS_VALIDACION_INTERNA]
        assert fin_y == tr.index.max() and fin_pred == tr.index.max()


@pytest.mark.parametrize("regla", ["minimo", "desempate"])
def test_predictor_ets_ajustado_pasa_sin_fuga(regla):
    cfg, y = Cfg(), serie(700)
    tr_p, ev_p = pliegues(cfg, y.index)[0].mascaras(y.index)
    pred = ajuste.predictor_estadistico("ets", regla)
    assert sin_fuga(pred, y, tr_p, list(y.index[ev_p][:2]))
