"""Pruebas de la importancia por permutación y del contraste con el EDA (#47), con datos SINTÉTICOS."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import interpretacion as it  # noqa: E402


class Lineal:
    """Modelo fijo y conocido: y = 3·a + b. La columna `c` no interviene."""

    def predict(self, X):
        return 3 * X["a"].to_numpy() + X["b"].to_numpy()


def datos(n=400, semilla=0):
    rng = np.random.default_rng(semilla)
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n), "c": rng.normal(size=n)},
                     index=pd.date_range("2024-01-01", periods=n, freq="D"))
    return X, pd.Series(Lineal().predict(X), index=X.index)


def test_permutar_una_variable_que_no_usa_el_modelo_no_cambia_nada():
    X, y = datos()
    imp = it.importancia_permutacion(Lineal(), X, y, {"c": ["c"]}, 5, 42)
    assert (imp["aumento_MAE"] == 0).all()
    assert (imp["MAE_base"] == 0).all()


def test_la_importancia_ordena_por_peso_y_es_reproducible():
    X, y = datos()
    grupos = {"a": ["a"], "b": ["b"], "c": ["c"]}
    r1 = it.resumir(it.importancia_permutacion(Lineal(), X, y, grupos, 10, 42), ["grupo"])
    r2 = it.resumir(it.importancia_permutacion(Lineal(), X, y, grupos, 10, 42), ["grupo"])
    pd.testing.assert_frame_equal(r1, r2)
    m = r1.set_index("grupo")["aumento_MAE"]
    assert m["a"] > m["b"] > m["c"] == 0


def test_un_grupo_se_permuta_junto():
    """Dos columnas idénticas: permutadas juntas siguen iguales entre sí en cada fila."""
    X, y = datos()
    X["a2"] = X["a"]

    class Usa:
        def predict(self, Z):
            assert (Z["a"].to_numpy() == Z["a2"].to_numpy()).all()
            return Z["a"].to_numpy()

    it.importancia_permutacion(Usa(), X, y, {"a": ["a", "a2"]}, 3, 1)


def test_anadir_un_grupo_no_cambia_los_anteriores():
    X, y = datos()
    uno = it.importancia_permutacion(Lineal(), X, y, {"a": ["a"]}, 5, 7)
    dos = it.importancia_permutacion(Lineal(), X, y, {"a": ["a"], "b": ["b"]}, 5, 7)
    pd.testing.assert_frame_equal(uno, dos[dos["grupo"] == "a"].reset_index(drop=True))


def test_los_grupos_cubren_las_predictoras_sin_solaparse():
    import features as feat
    idx = pd.date_range("2020-01-01", periods=120, freq="D")
    y = pd.Series(np.arange(120, dtype=float) + 300, index=idx, name="victimas")
    X = feat.construir(y.to_frame(), objetivo="victimas")
    cols = [c for g in it.GRUPOS.values() for c in g]
    assert len(cols) == len(set(cols))
    assert sorted(cols) == sorted(feat.predictoras(X, objetivo="victimas"))


def test_respuesta_al_festivo():
    """Un modelo que resta un 40 % en festivo da −40 % al marcar y +66,7 % al desmarcar."""
    idx = pd.date_range("2024-01-01", periods=70, freq="D")
    X = pd.DataFrame({"festivo": 0, "puente": 0}, index=idx)
    lunes = idx[idx.day_of_week == 0]
    X.loc[lunes[:3], ["festivo", "puente"]] = 1

    class Festivo:
        def predict(self, Z):
            return np.where(Z["festivo"].to_numpy() == 1, 60.0, 100.0)

    r = it.respuesta_festivo(Festivo(), X)
    assert r["n_lunes_festivos"] == 3 and r["n_lunes_laborables"] == len(lunes) - 3
    assert r["laborable_a_festivo_pct"] == pytest.approx(-40)
    assert r["festivo_a_laborable_pct"] == pytest.approx(100 * (100 / 60 - 1))


def test_perfil_semanal():
    idx = pd.date_range("2024-01-01", periods=14, freq="D")   # empieza en lunes
    y = pd.Series(np.tile(np.arange(7, dtype=float), 2), index=idx)
    p = it.perfil_semanal(y, {"m": y * 2})
    assert list(p.index) == it.DIAS
    assert p.loc["domingo", "observado"] == 6 and p.loc["lunes", "m"] == 0
