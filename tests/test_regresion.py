"""Pruebas de la regresión lineal con rezagos y calendario (#144), con datos SINTÉTICOS.

Lo que, si fallara, daría números plausibles y falsos: una predicción que mira el día que predice, una
elección de la regularización que ve la evaluación, o un coeficiente mal convertido a su unidad.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import ajuste, regresion  # noqa: E402
from modelado.arboles import construir_X  # noqa: E402
from modelado.evaluacion import particion, pliegues, sin_fuga  # noqa: E402


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


def _casos(cfg, y, n=3):
    tr_f, ev_f = particion(cfg, y.index)
    tr_p, ev_p = pliegues(cfg, y.index)[0].mascaras(y.index)
    return [(tr_p, list(y.index[ev_p][:n])), (tr_f, list(y.index[ev_f][:n]))]


@pytest.mark.parametrize("alpha", [0.0, 1.0, 100.0])
def test_prueba_anti_fuga_pasa(alpha):
    """Altera y[t:], reconstruye las 21 variables desde la serie alterada y exige la misma predicción."""
    cfg, y = Cfg(), serie()
    pred = regresion.predictor_regresion(alpha)
    for tr, dias in _casos(cfg, y):
        assert sin_fuga(pred, y, tr, dias, construir_X=construir_X)


def test_la_prueba_anti_fuga_detecta_un_modelo_con_el_valor_del_dia():
    """Control: si el modelo mirara y[t], la prueba tiene que fallar."""
    cfg, y = Cfg(), serie()
    tr, dias = _casos(cfg, y)[0]
    assert not sin_fuga(lambda y_, X, e, i: X["del_dia"].reindex(i), y, tr, dias,
                        construir_X=lambda s: pd.DataFrame({"del_dia": s}))


def test_las_predicciones_se_reproducen():
    cfg, y = Cfg(), serie()
    a = regresion.evaluar_modelo(cfg, y, 1.0)
    b = regresion.evaluar_modelo(cfg, y, 1.0)
    pd.testing.assert_frame_equal(a["predicciones"], b["predicciones"])
    assert a["final"] == b["final"]


def test_se_guardan_predicciones_de_cada_pliegue_y_de_la_final_y_reproducen_el_mae():
    cfg, y = Cfg(), serie()
    r = regresion.evaluar_modelo(cfg, y, 1.0)
    p = r["predicciones"]
    assert set(p["pliegue"]) == {1, 2, 3, "final"}
    _, ev = particion(cfg, y.index)
    assert (p["pliegue"] == "final").sum() == ev.sum()
    final = p.query("pliegue == 'final'")
    assert round((final["real"] - final["prediccion"]).abs().mean(), 2) == r["final"]["MAE"]


def test_sin_2020_no_entrena_con_filas_de_2020():
    cfg, y = Cfg(), serie()
    X = construir_X(y)
    tr, _ = particion(cfg, y.index)
    con = regresion._entrenamiento(X, y, tr, False, cfg.indicador_atipico)
    sin = regresion._entrenamiento(X, y, tr, True, cfg.indicador_atipico)
    assert (con.index.year == 2020).any() and not (sin.index.year == 2020).any()


def test_el_ajuste_descarta_las_filas_sin_historia_para_los_rezagos():
    cfg, y = Cfg(), serie()
    X = construir_X(y)
    tr, _ = particion(cfg, y.index)
    t = regresion._entrenamiento(X, y, tr, False, cfg.indicador_atipico)
    assert t.notna().all().all() and t.index.min() == pd.Timestamp("2020-01-29")


def test_un_modelo_sin_X_falla_con_un_mensaje_claro():
    cfg, y = Cfg(), serie()
    tr, dias = _casos(cfg, y)[0]
    with pytest.raises(ValueError, match="variables derivadas"):
        regresion.predictor_regresion(1.0)(y, None, tr, pd.DatetimeIndex(dias))


def test_una_prediccion_no_finita_falla_en_lugar_de_pasar(monkeypatch):
    """Los avisos falsos de numpy se silencian, así que un fallo real no puede pasar inadvertido."""
    class Roto:
        def fit(self, X, y):
            return self

        def predict(self, X):
            return np.full(len(X), np.nan)

    cfg, y = Cfg(), serie()
    tr, dias = _casos(cfg, y)[0]
    monkeypatch.setattr(regresion, "crear_modelo", lambda *a, **k: Roto())
    with pytest.raises(RuntimeError, match="no finitas"):
        regresion.predictor_regresion(1.0)(y, construir_X(y), tr, pd.DatetimeIndex(dias))


def test_la_eleccion_de_alpha_no_ve_la_evaluacion():
    """Alterar los días posteriores al fin del entrenamiento no cambia la búsqueda."""
    cfg, y = Cfg(), serie()
    fin = pd.Timestamp(cfg.fin_entrenamiento)
    otra = y.copy()
    otra[otra.index > fin] = otra[otra.index > fin] * 3 + 500

    def busqueda(s):
        res, elegido = regresion.buscar_alpha(cfg, s[s.index <= fin], ajuste.predictoras_seleccion(s, fin))
        return [(c["alpha"], c["MAE_combinado"]) for c in res], elegido["alpha"]

    assert busqueda(y) == busqueda(otra)


def test_a_igualdad_gana_la_regularizacion_mas_alta(monkeypatch):
    monkeypatch.setattr(ajuste, "validar_en_pliegues",
                        lambda cfg, y, pred, X=None: {"MAE_combinado": 30.0, "n_validacion": 1,
                                                      "por_pliegue": []})
    cfg, y = Cfg(), serie()
    _, elegido = regresion.buscar_alpha(cfg, y, construir_X(y))
    assert elegido["alpha"] == max(regresion.ALPHAS)


def test_los_coeficientes_se_convierten_a_su_unidad():
    """Con una relación conocida, el coeficiente por unidad recupera el efecto en la escala original."""
    rng = np.random.default_rng(0)
    n = 600
    df = pd.DataFrame({"dia_semana": rng.integers(0, 7, n), "mes": rng.integers(1, 13, n),
                       "temp": rng.normal(20, 5, n), "festivo": rng.integers(0, 2, n)})
    y = 100 + 3.0 * df["temp"] - 80.0 * df["festivo"] + 25.0 * (df["dia_semana"] == 4)
    modelo = regresion.crear_modelo(0.0, list(df.columns)).fit(df, y)
    t = regresion.tabla_coeficientes(modelo).set_index("variable")
    assert t.loc["temp", "coef_por_unidad"] == pytest.approx(3.0, abs=1e-3)
    assert t.loc["festivo", "coef_por_unidad"] == pytest.approx(-80.0, abs=1e-3)
    # con una referencia común, el viernes se separa 25 de cada uno de los demás días
    otros = [t.loc[f"dia_semana_{d}", "coef_por_unidad"] for d in (0, 1, 2, 3, 5, 6)]
    assert t.loc["dia_semana_4", "coef_por_unidad"] - np.mean(otros) == pytest.approx(25.0, abs=1e-2)
    assert t.loc["temp", "coef_estandarizado"] == pytest.approx(3.0 * df["temp"].std(ddof=0), abs=1e-2)


def test_la_tabla_de_coeficientes_trae_las_variables_codificadas():
    cfg, y = Cfg(), serie()
    t = regresion.coeficientes(cfg, y, 1.0)
    assert t.loc[0, "variable"] == "(intercepto)"
    assert {"dia_semana_3", "mes_7", "festivo", "rezago_1", "anio_atipico_2020"} <= set(t["variable"])
