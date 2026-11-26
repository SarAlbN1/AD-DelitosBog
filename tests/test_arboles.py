"""Pruebas de los modelos de árboles con rezagos (#44), con una serie SINTÉTICA.

Los criterios de aceptación de la issue: la prueba anti-fuga pasa y las predicciones se reproducen
con la semilla. Las dos se prueban aquí, con hiperparámetros pequeños para que sea rápido.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import arboles  # noqa: E402
from modelado.evaluacion import particion, pliegues, sin_fuga  # noqa: E402

PEQUENOS = {
    "bosque_aleatorio": {"n_estimators": 20, "min_samples_leaf": 3, "max_features": 0.5},
    "gradiente_histogramas": {"max_iter": 30, "learning_rate": 0.1, "max_leaf_nodes": 8,
                              "min_samples_leaf": 10},
}


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


def serie(n: int = 1000, inicio: str = "2020-01-01", semilla: int = 5) -> pd.Series:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, periods=n, freq="D", name="fecha")
    v = 300 + np.arange(n) * 0.05 + 25 * np.sin(2 * np.pi * idx.dayofweek / 7)
    return pd.Series((v + rng.normal(0, 12, n)).round(), index=idx, name="victimas")


def _casos(cfg, y, n=3):
    """(entrenamiento, días) del primer pliegue y de la evaluación final, cada uno con su máscara."""
    tr_f, ev_f = particion(cfg, y.index)
    tr_p, ev_p = pliegues(cfg, y.index)[0].mascaras(y.index)
    return [(tr_p, list(y.index[ev_p][:n])), (tr_f, list(y.index[ev_f][:n]))]


@pytest.mark.parametrize("nombre", list(PEQUENOS))
def test_prueba_anti_fuga_pasa_para_cada_modelo(nombre):
    """Altera y[t:], reconstruye las variables desde la serie alterada y exige la misma predicción."""
    cfg, y = Cfg(), serie()
    pred = arboles.predictor_arbol(nombre, 42, hiperparametros=PEQUENOS[nombre])
    for tr, dias in _casos(cfg, y):
        assert sin_fuga(pred, y, tr, dias, construir_X=arboles.construir_X)


def test_la_prueba_anti_fuga_detecta_a_un_modelo_con_el_valor_del_dia():
    """Control: si el modelo mirara y[t], la prueba tiene que fallar; si no, no prueba nada."""
    cfg, y = Cfg(), serie()

    def con_fuga(y_, X, entrena, indice):
        return X["del_dia"].reindex(indice)

    def construir(s):
        return pd.DataFrame({"del_dia": s})

    tr, dias = _casos(cfg, y)[0]
    assert not sin_fuga(con_fuga, y, tr, dias, construir_X=construir)


def test_las_predictoras_no_incluyen_el_objetivo_y_son_21():
    X = arboles.construir_X(serie())
    assert "victimas" not in X.columns
    assert X.shape[1] == 21


@pytest.mark.parametrize("nombre", list(PEQUENOS))
def test_las_predicciones_se_reproducen_con_la_semilla(nombre):
    cfg, y = Cfg(), serie()
    a = arboles.evaluar_modelo(cfg, y, nombre, 42, hiperparametros=PEQUENOS[nombre])
    b = arboles.evaluar_modelo(cfg, y, nombre, 42, hiperparametros=PEQUENOS[nombre])
    pd.testing.assert_frame_equal(a["predicciones"], b["predicciones"])
    assert a["final"] == b["final"]


def test_otra_semilla_cambia_el_bosque():
    cfg, y = Cfg(), serie()
    hp = PEQUENOS["bosque_aleatorio"]
    a = arboles.evaluar_modelo(cfg, y, "bosque_aleatorio", 1, hiperparametros=hp)
    b = arboles.evaluar_modelo(cfg, y, "bosque_aleatorio", 2, hiperparametros=hp)
    assert not a["predicciones"]["prediccion"].equals(b["predicciones"]["prediccion"])


def test_se_guardan_predicciones_de_cada_pliegue_y_de_la_evaluacion_final():
    cfg, y = Cfg(), serie()
    r = arboles.evaluar_modelo(cfg, y, "bosque_aleatorio", 42,
                               hiperparametros=PEQUENOS["bosque_aleatorio"])
    p = r["predicciones"]
    assert set(p["pliegue"]) == {1, 2, 3, "final"}
    assert (p.groupby("pliegue").size().loc[[1, 2, 3]] == cfg.dias_pliegue).all()
    _, ev = particion(cfg, y.index)
    assert (p["pliegue"] == "final").sum() == ev.sum()
    assert p["prediccion"].notna().all()


def test_las_predicciones_guardadas_reproducen_las_metricas():
    """Comprueba que lo guardado es lo evaluado, no otra corrida."""
    cfg, y = Cfg(), serie()
    r = arboles.evaluar_modelo(cfg, y, "bosque_aleatorio", 42,
                               hiperparametros=PEQUENOS["bosque_aleatorio"])
    final = r["predicciones"].query("pliegue == 'final'")
    assert round((final["real"] - final["prediccion"]).abs().mean(), 2) == r["final"]["MAE"]


def test_sin_2020_no_entrena_con_filas_de_2020():
    cfg, y = Cfg(), serie()
    vistas: list[pd.Index] = []

    class Espia:
        def fit(self, X, yy):
            vistas.append(X.index)
            return self

        def predict(self, X):
            return np.zeros(len(X))

    original = arboles.crear_modelo
    arboles.crear_modelo = lambda *a, **k: Espia()
    try:
        X = arboles.construir_X(y)
        tr, dias = _casos(cfg, y)[1]
        arboles.predictor_arbol("bosque_aleatorio", 42, sin_2020=True)(y, X, tr, pd.DatetimeIndex(dias))
        arboles.predictor_arbol("bosque_aleatorio", 42, sin_2020=False)(y, X, tr, pd.DatetimeIndex(dias))
    finally:
        arboles.crear_modelo = original
    sin, con = vistas
    assert not (sin.year == 2020).any()
    assert (con.year == 2020).any()


def test_el_ajuste_descarta_las_filas_sin_historia_para_los_rezagos():
    cfg, y = Cfg(), serie()
    vistas: list[pd.Index] = []

    class Espia:
        def fit(self, X, yy):
            vistas.append(X)
            return self

        def predict(self, X):
            return np.zeros(len(X))

    original = arboles.crear_modelo
    arboles.crear_modelo = lambda *a, **k: Espia()
    try:
        tr, dias = _casos(cfg, y)[1]
        arboles.predictor_arbol("bosque_aleatorio", 42)(y, arboles.construir_X(y), tr,
                                                        pd.DatetimeIndex(dias))
    finally:
        arboles.crear_modelo = original
    assert vistas[0].notna().all().all()
    assert vistas[0].index.min() == pd.Timestamp("2020-01-29")


def test_un_modelo_sin_X_falla_con_un_mensaje_claro():
    cfg, y = Cfg(), serie()
    tr, dias = _casos(cfg, y)[0]
    with pytest.raises(ValueError, match="variables derivadas"):
        arboles.predictor_arbol("bosque_aleatorio", 42)(y, None, tr, pd.DatetimeIndex(dias))
