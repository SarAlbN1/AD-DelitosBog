"""Pruebas del arnés de evaluación compartido (#42).

El criterio de aceptación de la issue es que **los comparadores usen exactamente los mismos
pliegues que los modelos**. Que ambos «sigan el mismo protocolo» no es comprobable; que produzcan
los mismos límites de pliegue, sí. Eso es lo que se prueba aquí, con un modelo de verdad al lado de
los comparadores.

Lo segundo que se prueba es el contrato: el predictor recibe la serie observada completa, así que
lo que impide la fuga no es ocultarle datos sino la **prueba de perturbación**.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado.evaluacion import (VERSION_ARNES, Pliegue, evaluar,  # noqa: E402
                                 huella_pliegues, mae_ingenuo_estacional, metricas, particion,
                                 pliegues)
from modelado.referencia import COMPARADORES, predictor  # noqa: E402


class Cfg:
    """Config mínima, para no depender del archivo real."""

    fin_entrenamiento = "2022-06-30"
    pliegues = 4
    dias_pliegue = 60
    minimo_entrenamiento = 200
    periodo_estacional_mase = 7
    metricas = ("MAE", "RMSE", "MAPE", "MASE")
    metrica_principal = "MAE"
    criterio_barra = "mejor_comparador_en_evaluacion"


def serie(n: int = 900, inicio: str = "2020-07-01", semilla: int = 11) -> pd.Series:
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, periods=n, freq="D", name="fecha")
    v = 300 + np.arange(n) * 0.05 + 25 * np.sin(2 * np.pi * idx.dayofweek / 7)
    return pd.Series((v + rng.normal(0, 12, n)).round(), index=idx, name="victimas")


def predictor_modelo():
    """Un modelo de verdad, con la misma firma: ajusta sobre el entrenamiento y predice."""
    from sklearn.linear_model import LinearRegression

    def _predecir(y, X, entrena, indice):
        # Rezagos construidos de la serie observada: para t se usan t-1 y t-7, que son pasado.
        feats = pd.DataFrame({"r1": y.shift(1), "r7": y.shift(7),
                              "dia": y.index.dayofweek}, index=y.index)
        tr = feats[entrena].dropna()
        modelo = LinearRegression().fit(tr, y.loc[tr.index])
        pred = feats.reindex(indice)
        return pd.Series(modelo.predict(pred.fillna(pred.mean())), index=indice)

    return _predecir


# ------------------------------------------------- el criterio de aceptación de #42
def test_comparadores_y_modelo_usan_exactamente_los_mismos_pliegues():
    """Si un día divergen, esta prueba falla antes de que los números se publiquen."""
    cfg, y = Cfg(), serie()

    del_modelo = evaluar(cfg, y, predictor_modelo(), nombre="lineal")["por_pliegue"]
    limites_modelo = [(p["fin_entrenamiento"], p["fin_evaluacion"]) for p in del_modelo]

    for nombre, spec in COMPARADORES.items():
        del_comp = evaluar(cfg, y, predictor(*spec), nombre=nombre)["por_pliegue"]
        limites = [(p["fin_entrenamiento"], p["fin_evaluacion"]) for p in del_comp]
        assert limites == limites_modelo, f"{nombre} usa pliegues distintos del modelo"


def test_todos_evaluan_el_mismo_numero_de_dias_por_pliegue():
    cfg, y = Cfg(), serie()
    ns = {}
    for nombre, spec in COMPARADORES.items():
        ns[nombre] = [p["n"] for p in evaluar(cfg, y, predictor(*spec), nombre=nombre)["por_pliegue"]]
    ns["modelo"] = [p["n"] for p in evaluar(cfg, y, predictor_modelo())["por_pliegue"]]
    valores = list(ns.values())
    assert all(v == valores[0] for v in valores), f"evalúan distinto número de días: {ns}"


def test_la_huella_de_pliegues_identifica_el_conjunto():
    cfg, y = Cfg(), serie()
    assert huella_pliegues(cfg, y.index) == huella_pliegues(cfg, y.index)

    class Otra(Cfg):
        dias_pliegue = 90
    assert huella_pliegues(cfg, y.index) != huella_pliegues(Otra(), y.index)


# ------------------------------------------------- los pliegues
def test_los_pliegues_no_tocan_el_conjunto_de_evaluacion():
    cfg, y = Cfg(), serie()
    limite = pd.Timestamp(cfg.fin_entrenamiento)
    for p in pliegues(cfg, y.index):
        assert p.fin_evaluacion <= limite


def test_los_pliegues_no_se_solapan_y_el_entrenamiento_crece():
    cfg, y = Cfg(), serie()
    ps = pliegues(cfg, y.index)
    assert len(ps) >= 2
    for a, b in zip(ps, ps[1:]):
        assert a.fin_evaluacion <= b.fin_entrenamiento
    tam = [int((y.index <= p.fin_entrenamiento).sum()) for p in ps]
    assert tam == sorted(tam) and len(set(tam)) == len(tam)


def test_los_pliegues_van_numerados_desde_uno():
    cfg, y = Cfg(), serie()
    assert [p.numero for p in pliegues(cfg, y.index)] == list(range(1, len(pliegues(cfg, y.index)) + 1))


def test_respeta_el_minimo_de_entrenamiento():
    class Exigente(Cfg):
        minimo_entrenamiento = 600
    cfg, y = Exigente(), serie()
    for p in pliegues(cfg, y.index):
        assert int((y.index <= p.fin_entrenamiento).sum()) > 600


def test_mascaras_de_un_pliegue_son_disjuntas():
    cfg, y = Cfg(), serie()
    for p in pliegues(cfg, y.index):
        tr, ev = p.mascaras(y.index)
        assert not (tr & ev).any()


def test_la_particion_final_es_disjunta_y_cubre_todo():
    cfg, y = Cfg(), serie()
    tr, ev = particion(cfg, y.index)
    assert not (tr & ev).any()
    assert (tr | ev).all()


# ------------------------------------------------- fuga de información
@pytest.mark.parametrize("nombre,spec", list(COMPARADORES.items()))
def test_perturbar_el_futuro_no_cambia_la_evaluacion_de_los_comparadores(nombre, spec):
    """El predictor recibe la serie completa, así que esto es lo que impide la fuga."""
    cfg, y = Cfg(), serie()
    limite = pd.Timestamp(cfg.fin_entrenamiento)
    ps = pliegues(cfg, y.index)
    primero = ps[0]

    base = evaluar(cfg, y, predictor(*spec), nombre=nombre)["por_pliegue"][0]
    alterada = y.copy()
    alterada[alterada.index > primero.fin_evaluacion] = alterada[
        alterada.index > primero.fin_evaluacion] * 9 + 777
    nuevo = evaluar(cfg, alterada, predictor(*spec), nombre=nombre)["por_pliegue"][0]
    assert base == nuevo, "alterar días posteriores cambió la métrica del primer pliegue"
    assert limite == pd.Timestamp(cfg.fin_entrenamiento)


def test_perturbar_el_pasado_si_cambia_la_evaluacion():
    """Comprobación inversa: sin ella la anterior podría pasar por vacuidad."""
    cfg, y = Cfg(), serie()
    base = evaluar(cfg, y, predictor(1, None))["final"]
    alterada = y.copy()
    alterada.iloc[:100] = 1.0
    assert evaluar(cfg, alterada, predictor(1, None))["final"] != base


# ------------------------------------------------- métricas
def test_el_denominador_del_mase_usa_el_entrenamiento_de_cada_tramo():
    cfg, y = Cfg(), serie()
    tr, _ = particion(cfg, y.index)
    r = evaluar(cfg, y, predictor(1, None))
    assert r["denominador_mase"] == round(mae_ingenuo_estacional(y[tr], 7), 2)


def test_mase_uno_para_el_ingenuo_estacional_sobre_su_propio_tramo():
    y = serie()
    den = mae_ingenuo_estacional(y, 7)
    pred = y.shift(7)
    assert metricas(y, pred, den)["MASE"] == pytest.approx(1.0, abs=1e-3)


def test_metricas_ignoran_los_dias_sin_prediccion():
    y = serie(n=30)
    pred = y.shift(7)
    assert metricas(y, pred, 10.0)["n"] == 23


def test_el_resumen_de_pliegues_trae_medio_peor_y_desviacion():
    cfg, y = Cfg(), serie()
    r = evaluar(cfg, y, predictor(1, None))["resumen_pliegues"]
    assert r["pliegues"] >= 2
    assert r["MAE_peor"] >= r["MAE_medio"]
    assert r["MAE_desv"] is not None


# ------------------------------------------------- integridad
def test_falla_si_la_particion_deja_un_lado_vacio():
    class Mala(Cfg):
        fin_entrenamiento = "2019-01-01"
    with pytest.raises(ValueError, match="vacío"):
        evaluar(Mala(), serie(), predictor(1, None))


def test_la_version_del_arnes_esta_declarada():
    """Si cambia la semántica del cálculo hay que subirla, o el registro guardaría dos verdades."""
    assert isinstance(VERSION_ARNES, int) and VERSION_ARNES >= 1


def test_pliegue_es_inmutable():
    p = Pliegue(1, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-03-31"))
    with pytest.raises(Exception):
        p.numero = 2
