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
