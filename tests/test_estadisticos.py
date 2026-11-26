"""Pruebas de SARIMA y ETS (#43), con series SINTÉTICAS.

Lo que se comprueba es lo que, si fallara, daría números plausibles y falsos: una predicción que
mira el día que predice, una selección de órdenes que ve la evaluación, o una variante «sin 2020»
que en realidad usa ese año.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import estadisticos as es  # noqa: E402
from modelado.evaluacion import particion, pliegues, sin_fuga  # noqa: E402

warnings.filterwarnings("ignore")

ORDEN, ESTACIONAL = (1, 0, 1), (1, 0, 0, 7)
ETS = ("add", None, False, "add")


class Cfg:
    fin_entrenamiento = "2022-03-31"
    pliegues = 2
    dias_pliegue = 30
    minimo_entrenamiento = 200
    periodo_estacional_mase = 7
    metricas = ("MAE", "RMSE", "MAPE", "MASE")
    metrica_principal = "MAE"
    criterio_barra = "mejor_comparador_en_evaluacion"
    anio_atipico = 2020


def serie(n: int = 800, inicio: str = "2020-06-01", semilla: int = 3) -> pd.Series:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, periods=n, freq="D", name="fecha")
    v = 300 + 40 * np.sin(2 * np.pi * idx.dayofweek / 7) + rng.normal(0, 8, n)
    return pd.Series(v.round(), index=idx, name="victimas")


def _casos(cfg, y, n=2):
    tr_f, ev_f = particion(cfg, y.index)
    tr_p, ev_p = pliegues(cfg, y.index)[0].mascaras(y.index)
    return [(tr_p, list(y.index[ev_p][:n])), (tr_f, list(y.index[ev_f][:n]))]


@pytest.mark.parametrize("nombre,pred", [
    ("sarima", es.predictor_sarima(ORDEN, ESTACIONAL)),
    ("ets", es.predictor_ets(ETS)),
])
def test_prueba_anti_fuga_pasa_para_cada_modelo(nombre, pred):
    """Altera y[t:] y exige que la predicción de t no cambie."""
    cfg, y = Cfg(), serie()
    for tr, dias in _casos(cfg, y):
        assert sin_fuga(pred, y, tr, dias)


def test_la_prueba_detecta_a_un_predictor_que_usa_el_dia():
    """Control: sin él, la prueba anterior podría pasar por vacuidad."""
    cfg, y = Cfg(), serie()
    tr, dias = _casos(cfg, y)[0]
    assert not sin_fuga(lambda y_, X, e, i: y_.reindex(i), y, tr, dias)


@pytest.mark.parametrize("fabrica", [lambda **k: es.predictor_sarima(ORDEN, ESTACIONAL, **k),
                                     lambda **k: es.predictor_ets(ETS, **k)])
def test_el_ajuste_solo_ve_el_entrenamiento(fabrica):
    """Alterar la serie después del entrenamiento no cambia los parámetros: si no, ajustaría con ella."""
    cfg, y = Cfg(), serie()
    tr, ev = particion(cfg, y.index)
    dias = y.index[ev][:5]
    alterada = y.copy()
    alterada[ev] = alterada[ev] * 5 + 500
    a, b = [], []
    fabrica(registro=a)(y, None, tr, dias)
    fabrica(registro=b)(alterada, None, tr, dias)
    assert a[0]["criterio"] == b[0]["criterio"]


def test_la_seleccion_de_ordenes_solo_usa_el_entrenamiento_del_tramo():
    cfg, y = Cfg(), serie(600)
    tr, ev = particion(cfg, y.index)
    dias = y.index[ev][:3]
    alterada = y.copy()
    alterada[ev] = alterada[ev] * 7 + 900
    a, b = [], []
    es.predictor_ets(registro=a)(y, None, tr, dias)
    es.predictor_ets(registro=b)(alterada, None, tr, dias)
    assert a[0]["espec"] == b[0]["espec"] and a[0]["criterio"] == b[0]["criterio"]


def test_desde_2021_no_entrena_con_2020():
    """La variante de sensibilidad parte la serie en 2021-01-01 y no usa nada anterior."""
    cfg, y = Cfg(), serie()
    tr, ev = particion(cfg, y.index)
    dias = y.index[ev][:3]
    desde = pd.Timestamp("2021-01-01")
    alterada = y.copy()
    alterada[alterada.index < desde] = 99999.0
    a, b = [], []
    es.predictor_ets(ETS, desde=desde, registro=a)(y, None, tr, dias)
    es.predictor_ets(ETS, desde=desde, registro=b)(alterada, None, tr, dias)
    assert a[0]["criterio"] == b[0]["criterio"]
    c = []
    es.predictor_ets(ETS, registro=c)(alterada, None, tr, dias)
    assert c[0]["criterio"] != a[0]["criterio"]      # sin `desde`, 2020 sí influye


def test_las_predicciones_se_reproducen():
    cfg, y = Cfg(), serie()
    for fabrica in (lambda: es.predictor_sarima(ORDEN, ESTACIONAL), lambda: es.predictor_ets(ETS)):
        tr, ev = particion(cfg, y.index)
        dias = y.index[ev][:10]
        pd.testing.assert_series_equal(fabrica()(y, None, tr, dias), fabrica()(y, None, tr, dias))


def test_evaluar_modelo_guarda_predicciones_de_cada_pliegue_y_de_la_final():
    cfg, y = Cfg(), serie(700)
    original = es.MALLA_PQ, es.MALLA_PQ_ESTACIONAL
    es.MALLA_PQ, es.MALLA_PQ_ESTACIONAL = [(1, 1)], [(1, 0)]     # malla mínima, por velocidad
    try:
        r = es.evaluar_modelo(cfg, y, "sarima")
    finally:
        es.MALLA_PQ, es.MALLA_PQ_ESTACIONAL = original
    p = r["predicciones"]
    assert set(p["pliegue"]) == {1, 2, "final"}
    _, ev = particion(cfg, y.index)
    assert (p["pliegue"] == "final").sum() == ev.sum()
    assert p["prediccion"].notna().all()
    final = p.query("pliegue == 'final'")
    assert round((final["real"] - final["prediccion"]).abs().mean(), 2) == r["final"]["MAE"]
    assert len(r["elegidos"]) == 3


def test_estacionariedad_distingue_una_caminata_aleatoria_de_una_serie_estacionaria():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2020-01-01", periods=600, freq="D")
    camina = pd.Series(np.cumsum(rng.normal(0, 1, 600)), index=idx)
    t = es.pruebas_estacionariedad(camina).set_index("serie")
    assert not t.loc["nivel", "estacionaria"]
    assert t.loc["diferencia_1", "estacionaria"]


def test_la_diferenciacion_sale_de_las_pruebas():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2020-01-01", periods=700, freq="D")
    camina = pd.Series(np.cumsum(rng.normal(0, 1, 700)) + 100, index=idx)
    d, D, _ = es.elegir_diferenciacion(camina)
    assert (d, D) == (1, 0)
    estacional = pd.Series(100 + 50 * np.sin(2 * np.pi * idx.dayofweek / 7)
                           + rng.normal(0, 2, 700), index=idx)
    d2, D2, fuerza = es.elegir_diferenciacion(estacional)
    assert D2 == 1 and fuerza > es.UMBRAL_ESTACIONALIDAD


def test_ljung_box_detecta_autocorrelacion_residual():
    """Un AR(1) fuerte ajustado con un modelo sin AR deja residuos autocorrelacionados."""
    rng = np.random.default_rng(2)
    n = 700
    e = rng.normal(0, 5, n)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.9 * x[i - 1] + e[i]
    idx = pd.date_range("2020-06-01", periods=n, freq="D")
    y = pd.Series(300 + x, index=idx)
    d = es.diagnostico_residuos(Cfg(), y, "sarima", ((0, 0, 0), (0, 0, 0, 7)))
    assert d["autocorrelacion_residual"]
    bien = es.diagnostico_residuos(Cfg(), y, "sarima", ((1, 0, 0), (0, 0, 0, 7)))
    assert not bien["autocorrelacion_residual"]


@pytest.mark.parametrize("fabrica", [lambda **k: es.predictor_sarima(ORDEN, ESTACIONAL, **k),
                                     lambda **k: es.predictor_ets(("add", None, False, "mul"), **k)])
def test_con_desde_la_prediccion_no_depende_de_los_dias_anteriores(fabrica):
    """El filtrado arranca donde arranca el entrenamiento, no donde arranca la serie.

    Regresión: con `desde`, ETS filtraba desde el inicio de la serie con los estados iniciales
    estimados para `desde`, y con estacionalidad multiplicativa el error no se disipaba
    (MAE de 84,00 y 79,51 en los pliegues 2 y 3 de «ETS, desde 2021»).
    """
    cfg, y = Cfg(), serie()
    tr, ev = particion(cfg, y.index)
    dias = y.index[ev][:20]
    desde = pd.Timestamp("2021-01-01")
    alterada = y.copy()
    alterada[alterada.index < desde] = alterada[alterada.index < desde] * 3 + 500
    a = fabrica(desde=desde)(y, None, tr, dias)
    b = fabrica(desde=desde)(alterada, None, tr, dias)
    pd.testing.assert_series_equal(a, b)
