"""Pruebas de scripts/features.py, con énfasis en la fuga de información (#33).

La prueba central no revisa nombres de columna: perturba la serie desde un día hacia adelante,
reconstruye las variables y exige que la fila de ese día no cambie. Cualquier variable que mirara
el presente o el futuro haría fallar esa comprobación.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import features as ft  # noqa: E402


def serie_sintetica(n: int = 400, inicio: str = "2021-03-01", semilla: int = 7) -> pd.DataFrame:
    """Serie diaria con tendencia, estacionalidad semanal y ruido."""
    rng = np.random.default_rng(semilla)
    idx = pd.date_range(inicio, periods=n, freq="D", name="fecha")
    base = 300 + np.arange(n) * 0.1
    semanal = 25 * np.sin(2 * np.pi * idx.dayofweek / 7)
    valores = base + semanal + rng.normal(0, 15, n)
    return pd.DataFrame({"victimas": valores.round()}, index=idx)


# --------------------------------------------------------------------------- fuga de información
@pytest.mark.parametrize("posicion", [120, 200, 399])
def test_perturbar_el_futuro_no_cambia_la_fila_presente(posicion):
    """Si una variable usara datos de t o posteriores, esta prueba fallaría."""
    serie = serie_sintetica()
    original = ft.construir(serie)

    alterada = serie.copy()
    # Se cambia el día t y todos los posteriores, de forma grosera y detectable.
    alterada.iloc[posicion:, 0] = alterada.iloc[posicion:, 0] * 10 + 999

    nueva = ft.construir(alterada)
    cols = ft.predictoras(original)

    fila_antes = original.iloc[posicion][cols]
    fila_despues = nueva.iloc[posicion][cols]
    pd.testing.assert_series_equal(fila_antes, fila_despues, check_names=False)


def test_las_filas_anteriores_tampoco_cambian():
    """Perturbar el futuro no puede afectar a ninguna fila anterior."""
    serie = serie_sintetica()
    original = ft.construir(serie)
    alterada = serie.copy()
    alterada.iloc[250:, 0] = -1
    nueva = ft.construir(alterada)
    cols = ft.predictoras(original)
    pd.testing.assert_frame_equal(original.iloc[:250][cols], nueva.iloc[:250][cols])


def test_perturbar_el_pasado_si_cambia_el_presente():
    """Comprobación inversa: si nada cambiara, la prueba anterior no probaría nada."""
    serie = serie_sintetica()
    original = ft.construir(serie)
    alterada = serie.copy()
    alterada.iloc[100, 0] = 99999
    nueva = ft.construir(alterada)
    cols = ft.predictoras(original)
    assert not original.iloc[101][cols].equals(nueva.iloc[101][cols])


def test_el_objetivo_no_esta_entre_las_predictoras():
    X = ft.construir(serie_sintetica())
    assert "victimas" not in ft.predictoras(X)


def test_toda_variable_declara_su_disponibilidad():
    X = ft.construir(serie_sintetica())
    for col in X.columns:
        assert col in ft.DISPONIBILIDAD, f"{col} no declara disponibilidad"
        assert ft.DISPONIBILIDAD[col].strip(), f"{col} tiene disponibilidad vacía"


def test_ninguna_predictora_es_de_la_lista_prohibida():
    X = ft.construir(serie_sintetica())
    assert not set(ft.predictoras(X)) & set(ft.PROHIBIDAS)


# --------------------------------------------------------------------------- rezagos y ventanas
@pytest.mark.parametrize("k", ft.REZAGOS)
def test_el_rezago_k_es_el_valor_de_hace_k_dias(k):
    serie = serie_sintetica()
    X = ft.construir(serie)
    esperado = serie["victimas"].shift(k).astype(float)
    pd.testing.assert_series_equal(X[f"rezago_{k}"], esperado, check_names=False)


@pytest.mark.parametrize("v", ft.VENTANAS)
def test_la_media_previa_excluye_el_dia_actual(v):
    serie = serie_sintetica()
    X = ft.construir(serie)
    esperado = serie["victimas"].astype(float).shift(1).rolling(v).mean()
    pd.testing.assert_series_equal(X[f"media_previa_{v}"], esperado, check_names=False)


def test_los_nulos_estan_solo_al_principio():
    X = ft.construir(serie_sintetica())
    cols = ft.predictoras(X)
    con_nulo = X[cols].isna().any(axis=1).to_numpy()
    # Una vez que deja de haber nulos, no vuelven a aparecer.
    assert not con_nulo[np.argmin(con_nulo):].any()


# --------------------------------------------------------------------------- festivos
def test_pascua_en_anios_conocidos():
    assert ft.pascua(2020) == dt.date(2020, 4, 12)
    assert ft.pascua(2024) == dt.date(2024, 3, 31)
    assert ft.pascua(2025) == dt.date(2025, 4, 20)


def test_la_ley_emiliani_traslada_al_lunes():
    # 2024: el 6 de enero cae sábado, así que Reyes se corre al lunes 8.
    f24 = ft.festivos(2024)
    assert dt.date(2024, 1, 8) in f24
    assert dt.date(2024, 1, 6) not in f24
    # 2025: el 6 de enero ya es lunes, así que no se mueve.
    f25 = ft.festivos(2025)
    assert dt.date(2025, 1, 6) in f25


def test_festivos_fijos_y_de_pascua():
    f = ft.festivos(2024)
    for d in (dt.date(2024, 1, 1), dt.date(2024, 5, 1), dt.date(2024, 7, 20),
              dt.date(2024, 8, 7), dt.date(2024, 12, 8), dt.date(2024, 12, 25)):
        assert d in f, d
    # Jueves y Viernes Santo de 2024.
    assert dt.date(2024, 3, 28) in f
    assert dt.date(2024, 3, 29) in f


def test_el_numero_de_festivos_por_anio():
    """Colombia celebra 18 festivos, pero algunos años dos caen en la misma fecha.

    En 2025, San Pedro (29 de junio, domingo) y el Sagrado Corazón (Pascua + 71 = 29 de junio)
    se trasladan los dos al lunes 30 de junio, así que solo hay 17 fechas distintas. No es un
    error del cálculo: es el calendario.
    """
    esperado = {2020: 18, 2021: 18, 2022: 18, 2023: 18, 2024: 18, 2025: 17}
    for anio, n in esperado.items():
        assert len(ft.festivos(anio)) == n, anio


def test_la_colision_de_2025_es_la_esperada():
    p = ft.pascua(2025)
    assert ft._al_lunes(dt.date(2025, 6, 29)) == dt.date(2025, 6, 30)
    assert ft._al_lunes(p + dt.timedelta(days=71)) == dt.date(2025, 6, 30)


def test_la_marca_de_festivo_coincide_con_el_calendario():
    X = ft.construir(serie_sintetica(n=800, inicio="2023-01-01"))
    marcados = {d.date() for d in X.index[X["festivo"] == 1]}
    esperados = {d for d in ft.calendario_festivos(X.index.min(), X.index.max())
                 if X.index.min().date() <= d <= X.index.max().date()}
    assert marcados == esperados


# --------------------------------------------------------------------------- integridad de entrada
def test_rechaza_una_serie_con_huecos():
    serie = serie_sintetica(n=60)
    con_hueco = serie.drop(serie.index[30])
    with pytest.raises(ValueError, match="faltan"):
        ft.construir(con_hueco)


def test_rechaza_fechas_repetidas():
    serie = serie_sintetica(n=60)
    repetida = pd.concat([serie, serie.iloc[[10]]]).sort_index()
    with pytest.raises(ValueError, match="repetidas"):
        ft.construir(repetida)


def test_rechaza_un_indice_que_no_sea_de_fechas():
    serie = serie_sintetica(n=60).reset_index(drop=True)
    with pytest.raises(ValueError, match="índice de fechas"):
        ft.construir(serie)
