"""Pruebas de scripts/baselines.py (#38).

Las tres que importan son las que pidió la revisión: que ningún comparador mire el presente ni el
futuro, que los pliegues rodantes no se solapen ni toquen el conjunto de evaluación, y que el
denominador del MASE no dependa del tramo que se quiere medir.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import baselines as bl  # noqa: E402

FIN_ENTRENAMIENTO = "2022-06-30"


def serie(n: int = 900, inicio: str = "2020-07-01", semilla: int = 11) -> pd.Series:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, periods=n, freq="D", name="fecha")
    valores = 300 + np.arange(n) * 0.05 + 25 * np.sin(2 * np.pi * idx.dayofweek / 7)
    return pd.Series((valores + rng.normal(0, 12, n)).round(), index=idx, name="victimas")


# --------------------------------------------------------------- 1. nada mira el presente ni el futuro
@pytest.mark.parametrize("nombre,spec", list(bl.COMPARADORES.items()))
def test_perturbar_el_futuro_no_cambia_la_prediccion_de_hoy(nombre, spec):
    y = serie()
    pos = 500
    pred = bl.predecir(y, *spec)

    alterada = y.copy()
    alterada.iloc[pos:] = alterada.iloc[pos:] * 7 + 1234
    pred_alterada = bl.predecir(alterada, *spec)

    # La predicción de `pos` y de todos los días anteriores no puede moverse.
    pd.testing.assert_series_equal(pred.iloc[: pos + 1], pred_alterada.iloc[: pos + 1],
                                   check_names=False)


def test_perturbar_el_pasado_si_cambia_la_prediccion():
    """Comprobación inversa: sin ella la anterior podría pasar por vacuidad."""
    y = serie()
    pred = bl.predecir(y, *bl.COMPARADORES["ingenuo"])
    alterada = y.copy()
    alterada.iloc[200] = 99999
    nueva = bl.predecir(alterada, *bl.COMPARADORES["ingenuo"])
    assert pred.iloc[201] != nueva.iloc[201]


def test_ningun_comparador_usa_el_valor_del_dia():
    y = serie()
    for nombre, spec in bl.COMPARADORES.items():
        desplazamiento = spec[0]
        assert desplazamiento >= 1, f"{nombre} no desplaza la serie"
        pred = bl.predecir(y, *spec)
        # El primer día nunca puede tener predicción: no hay historia.
        assert pd.isna(pred.iloc[0]), nombre


# --------------------------------------------------------------- 2. los pliegues
def test_los_pliegues_no_se_solapan_y_van_en_orden():
    y = serie()
    idx = y.index
    pliegues = bl.pliegues_origen_rodante(idx, n=5, dias=90, minimo_entrenamiento=200)
    assert len(pliegues) >= 2
    anterior_fin = None
    for fin_tr, fin_ev in pliegues:
        assert fin_tr < fin_ev, "el entrenamiento debe acabar antes que la evaluación"
        if anterior_fin is not None:
            assert fin_tr >= anterior_fin, "un pliegue empieza antes de que acabe el anterior"
        anterior_fin = fin_ev


def test_ningun_pliegue_toca_el_conjunto_de_evaluacion():
    y = serie()
    entrena = y[y.index <= FIN_ENTRENAMIENTO]
    pliegues = bl.pliegues_origen_rodante(entrena.index, n=5, dias=90, minimo_entrenamiento=200)
    limite = pd.Timestamp(FIN_ENTRENAMIENTO)
    for _, fin_ev in pliegues:
        assert fin_ev <= limite, "un pliegue evalúa días del conjunto de evaluación final"


def test_el_entrenamiento_de_cada_pliegue_crece():
    y = serie()
    pliegues = bl.pliegues_origen_rodante(y.index, n=5, dias=90, minimo_entrenamiento=200)
    tamanos = [int((y.index <= fin_tr).sum()) for fin_tr, _ in pliegues]
    assert tamanos == sorted(tamanos), "el conjunto de entrenamiento debe crecer entre pliegues"
    assert len(set(tamanos)) == len(tamanos), "dos pliegues con el mismo entrenamiento"


def test_respeta_el_minimo_de_entrenamiento():
    y = serie()
    pliegues = bl.pliegues_origen_rodante(y.index, n=20, dias=90, minimo_entrenamiento=400)
    for fin_tr, _ in pliegues:
        assert int((y.index <= fin_tr).sum()) > 400


# --------------------------------------------------------------- 3. el denominador del MASE
def test_el_denominador_del_mase_no_depende_de_la_evaluacion():
    y = serie()
    r1 = bl.evaluar(y, FIN_ENTRENAMIENTO, pliegues=3, dias_pliegue=90, minimo_entrenamiento=200)

    # Se altera solo el tramo de evaluación, de forma brutal.
    alterada = y.copy()
    alterada[alterada.index > FIN_ENTRENAMIENTO] = 1.0
    r2 = bl.evaluar(alterada, FIN_ENTRENAMIENTO, pliegues=3, dias_pliegue=90,
                    minimo_entrenamiento=200)

    assert r1["denominador_mase"] == r2["denominador_mase"]


def test_el_denominador_sale_del_entrenamiento():
    y = serie()
    entrena = y[y.index <= FIN_ENTRENAMIENTO]
    r = bl.evaluar(y, FIN_ENTRENAMIENTO, pliegues=3, dias_pliegue=90, minimo_entrenamiento=200)
    assert r["denominador_mase"] == round(bl.mae_ingenuo_estacional(entrena, bl.PERIODO_ESTACIONAL), 2)


def test_mase_de_uno_para_el_ingenuo_estacional_sobre_su_propio_tramo():
    """Si se evalúa el ingenuo estacional en el mismo tramo del denominador, su MASE es 1."""
    y = serie()
    den = bl.mae_ingenuo_estacional(y, bl.PERIODO_ESTACIONAL)
    pred = bl.predecir(y, *bl.COMPARADORES["ingenuo_estacional"])
    m = bl.metricas(y, pred, den)
    assert m["MASE"] == pytest.approx(1.0, abs=1e-3)


# --------------------------------------------------------------- integridad general
def test_la_barra_es_el_mejor_comparador_del_conjunto_de_evaluacion():
    y = serie()
    r = bl.evaluar(y, FIN_ENTRENAMIENTO, pliegues=3, dias_pliegue=90, minimo_entrenamiento=200)
    maes = {k: v["MAE"] for k, v in r["comparadores"].items()}
    assert r["barra"]["mejor_por_MAE"] == min(maes, key=maes.get)
    assert r["barra"]["MAE"] == min(maes.values())


def test_la_particion_no_se_solapa():
    y = serie()
    r = bl.evaluar(y, FIN_ENTRENAMIENTO, pliegues=3, dias_pliegue=90, minimo_entrenamiento=200)
    p = r["particion"]
    assert p["entrenamiento"][1] < p["evaluacion"][0]
    assert p["dias_entrenamiento"] + p["dias_evaluacion"] == len(y)


def test_falla_si_la_particion_deja_un_lado_vacio():
    y = serie()
    with pytest.raises(SystemExit, match="vacío"):
        bl.evaluar(y, "2019-01-01", pliegues=3, dias_pliegue=90, minimo_entrenamiento=200)
