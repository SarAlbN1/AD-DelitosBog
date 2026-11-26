"""Pruebas de la comparación contra la barra (#46), con datos SINTÉTICOS."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import comparacion as cmp  # noqa: E402
from modelado.evaluacion import evaluar  # noqa: E402
from modelado.referencia import COMPARADORES, predictor  # noqa: E402


class Cfg:
    fin_entrenamiento = "2022-06-30"
    pliegues = 3
    dias_pliegue = 45
    minimo_entrenamiento = 200
    periodo_estacional_mase = 7
    metricas = ("MAE", "RMSE", "MAPE", "MASE")
    metrica_principal = "MAE"


def serie(n: int = 1000, semilla: int = 5) -> pd.Series:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range("2020-01-01", periods=n, freq="D", name="fecha")
    v = 300 + 25 * np.sin(2 * np.pi * idx.day_of_week / 7) + rng.normal(0, 12, n)
    return pd.Series(v.round(), index=idx, name="victimas")


def test_dm_signo_positivo_cuando_el_modelo_pierde_menos():
    rng = np.random.default_rng(1)
    e_barra = rng.normal(0, 20, 300)
    e_modelo = e_barra / 2
    r = cmp.diebold_mariano(e_barra, e_modelo)
    assert r["estadistico"] > 0 and r["p_valor"] < 1e-6
    assert cmp.diebold_mariano(e_modelo, e_barra)["estadistico"] == pytest.approx(-r["estadistico"])


def test_dm_errores_identicos_no_da_estadistico():
    e = np.arange(10.0)
    assert np.isnan(cmp.diebold_mariano(e, e)["estadistico"])


def test_dm_hln_coincide_con_la_formula():
    rng = np.random.default_rng(3)
    a, b = rng.normal(0, 10, 50), rng.normal(0, 9, 50)
    d = np.abs(a) - np.abs(b)
    n = d.size
    esperado = d.mean() / np.sqrt(d.var() / n) * np.sqrt((n - 1) / n)
    assert cmp.diebold_mariano(a, b)["estadistico"] == pytest.approx(esperado)


def test_dm_hac_cambia_la_varianza_con_errores_autocorrelacionados():
    rng = np.random.default_rng(4)
    ruido = rng.normal(0, 1, 400)
    d = np.convolve(ruido, np.ones(5) / 5, mode="same") + 0.1  # diferencial con autocorrelación
    a, b = np.abs(d) + 1, np.ones_like(d)
    sin = cmp.diebold_mariano(a, b)["estadistico"]
    con = cmp.diebold_mariano(a, b, rezagos=7)["estadistico"]
    assert abs(con) < abs(sin)


def test_predicciones_de_referencia_reproducen_el_arnes():
    """Las predicciones recalculadas dan las mismas métricas que `evaluar` en cada tramo."""
    cfg, y = Cfg(), serie()
    pred = cmp.predicciones_referencia(cfg, y)
    m = cmp.metricas_por_tramo(cfg, y, pred)
    for nombre, spec in COMPARADORES.items():
        r = evaluar(cfg, y, predictor(*spec), nombre=nombre)
        mm = m[m["modelo"] == nombre].set_index("pliegue")
        assert mm.loc["final", "MAE"] == pytest.approx(r["final"]["MAE"])
        assert mm.loc["final", "MASE"] == pytest.approx(r["final"]["MASE"])
        for p in r["por_pliegue"]:
            assert mm.loc[str(p["pliegue"]), "MAE"] == pytest.approx(p["MAE"])


def _escribir_referencia(carpeta: Path, m: pd.DataFrame, delta: float = 0.0) -> None:
    ref = carpeta / "referencia"
    ref.mkdir(parents=True)
    fin = m[m["pliegue"] == "final"].drop(columns=["origen", "pliegue"]).set_index("modelo")
    fin.loc[fin.index[0], "MAE"] += delta
    fin.to_csv(ref / "metricas_finales.csv")
    p = m[m["pliegue"] != "final"].drop(columns=["origen"]).rename(columns={"modelo": "comparador"})
    p.to_csv(ref / "metricas_por_pliegue.csv", index=False)


def test_trazabilidad_acepta_lo_guardado_y_rechaza_una_cifra_distinta(tmp_path):
    cfg, y = Cfg(), serie()
    m = cmp.metricas_por_tramo(cfg, y, cmp.predicciones_referencia(cfg, y))
    _escribir_referencia(tmp_path / "ok", m.round(2))
    assert cmp.comprobar_trazabilidad(m, tmp_path / "ok") > 0
    _escribir_referencia(tmp_path / "mal", m.round(2), delta=0.5)
    with pytest.raises(RuntimeError, match="no coincide"):
        cmp.comprobar_trazabilidad(m, tmp_path / "mal")


# ------------------------------------------------------------------ la regresión lineal (#144)
def _tabla(filas):
    """Una `tabla_comparativa` mínima: (origen, modelo, MAE medio por pliegues)."""
    return pd.DataFrame([{"origen": o, "modelo": m, "sensibilidad": m.endswith(cmp.SUFIJOS_SENSIBILIDAD),
                          "familia": "comparador" if o == "#42" else cmp.FAMILIA[
                              m.replace("_sin_2020", "").replace("_desde_2021", "")],
                          "MAE_medio_pliegues": v} for o, m, v in filas])


def test_la_regresion_es_un_origen_con_su_familia():
    assert cmp.ORIGENES["regresion"] == "#144"
    assert cmp.FAMILIA["regresion_lineal"] == "regresión"
    assert "#144" in cmp.FINALES and "#45" in cmp.FINALES


def test_los_principales_incluyen_la_regresion_y_prefieren_lo_ajustado():
    t = _tabla([("#42", "ingenuo_estacional", 58.0),
                ("#43", "ets", 30.0), ("#45", "ets", 36.7), ("#45", "sarima", 36.1),
                ("#44", "bosque_aleatorio", 20.0), ("#45", "bosque_aleatorio", 34.9),
                ("#45", "gradiente_histogramas", 30.8),
                ("#144", "regresion_lineal", 34.6), ("#144", "regresion_lineal_sin_2020", 34.5)])
    p = cmp.principales(t)
    # uno por familia, siempre de los finales (#45 o #144), nunca la primera versión de #43 o #44
    assert p == [("#45", "sarima"), ("#45", "gradiente_histogramas"), ("#144", "regresion_lineal")]


def test_los_principales_sin_ajuste_siguen_funcionando_sin_la_regresion():
    t = _tabla([("#42", "ingenuo_estacional", 58.0), ("#43", "ets", 36.7), ("#44", "bosque_aleatorio", 34.9)])
    assert cmp.principales(t) == [("#43", "ets"), ("#44", "bosque_aleatorio")]


def test_dm_entre_modelos_incluye_los_pares_con_la_regresion():
    rng = np.random.default_rng(0)
    fechas = pd.date_range("2025-05-01", periods=60)
    real = rng.normal(350, 40, 60)
    filas = []
    for origen, modelo, sd in [("#42", "ingenuo_estacional", 60), ("#45", "ets", 30),
                               ("#45", "gradiente_histogramas", 28), ("#144", "regresion_lineal", 35)]:
        filas += [{"origen": origen, "modelo": modelo, "pliegue": "final", "fecha": f, "real": r,
                   "prediccion": r + rng.normal(0, sd)} for f, r in zip(fechas, real)]
    pred = pd.DataFrame(filas)
    t = _tabla([("#42", "ingenuo_estacional", 1.0), ("#45", "ets", 1.0),
                ("#45", "gradiente_histogramas", 1.0), ("#144", "regresion_lineal", 1.0)])
    d = cmp.dm_entre_modelos(pred, t)
    assert len(d) == 3                                              # 3 modelos finales, 3 pares
    assert any("regresion_lineal (#144)" in x for x in d["modelo_b"].tolist() + d["modelo_a"].tolist())
    assert not any("#42" in x for x in d["modelo_a"].tolist() + d["modelo_b"].tolist())


@pytest.mark.parametrize("origen,modelo,esperado", [
    ("#144", "regresion_lineal", "Regresión lineal (ajustada)"),
    ("#45", "gradiente_histogramas", "Gradiente por histogramas (ajustado)"),
    ("#43", "ets", "ETS #43"),
])
def test_etiquetas_de_las_figuras(origen, modelo, esperado):
    assert cmp.etiqueta(origen, modelo) == esperado
