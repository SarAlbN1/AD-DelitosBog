# -*- coding: utf-8 -*-
"""Pruebas de `dim_fuente` y del orden de las hojas del tablero (#106), con datos sintéticos."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exportar_powerbi as ep  # noqa: E402


def _auditorias(tmp_path, filas_policia=741986, serie=730870):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    pd.DataFrame({"fuente": ["linea123", "fiscalia"], "filas_hurto": [25144, 1300703]}).to_csv(
        a / "resumen_fuentes.csv", index=False)
    pd.DataFrame({"fuente": ["policia_registro", "policia_agregado"],
                  "filas_hurto": [filas_policia, 2922]}).to_csv(b / "resumen_fuentes.csv", index=False)
    r = tmp_path / "resumen_serie.json"
    r.write_text(json.dumps({"filas_en_la_serie": serie}), encoding="utf-8")
    return a, b, r


def test_dim_fuente_lee_las_cifras_y_separa_filas_de_victimas(tmp_path):
    t = ep.dim_fuente(*_auditorias(tmp_path, filas_policia=111, serie=99)).set_index("clave")
    assert t.loc["policia_registro", "filas_auditadas"] == 111      # 2020-2025 completo
    assert t.loc["policia_registro", "victimas_en_la_serie"] == 99  # hasta 2025-10-31
    assert t.loc["fiscalia", "filas_auditadas"] == 1300703
    assert t["victimas_en_la_serie"].drop("policia_registro").isna().all()


def test_dim_fuente_falla_si_la_auditoria_no_trae_una_fuente(tmp_path):
    a, b, r = _auditorias(tmp_path)
    pd.DataFrame({"fuente": ["linea123"], "filas_hurto": [1]}).to_csv(a / "resumen_fuentes.csv",
                                                                    index=False)
    with pytest.raises(SystemExit):
        ep.dim_fuente(a, b, r)


def test_serie_se_redondea_a_cuatro_decimales(tmp_path):
    f = tmp_path / "f.csv"
    pd.DataFrame({"fecha": ["2020-01-01"], "victimas": [1.0],
                  "m7": [472.1428571428572]}).to_csv(f, index=False)
    assert ep.hechos_serie(f)["m7"].iloc[0] == 472.1429


# ------------------------------------------------------------------ modelos (página 6)
def _metricas(carpeta, sub, col, filas):
    d = carpeta / sub
    d.mkdir(parents=True)
    fin = pd.DataFrame([{"n": 184.0, "MAE": mae, "RMSE": mae + 5, "MAPE": 10.0, "MASE": mae / 50}
                        for _, mae in filas], index=[n for n, _ in filas])
    fin.to_csv(d / "metricas_finales.csv")
    pd.DataFrame([{col: n, "pliegue": k, "MAE": mae, "RMSE": mae + 5, "MAPE": 10.0, "MASE": 1.0}
                  for n, mae in filas for k in (1, 2)]).to_csv(d / "metricas_por_pliegue.csv",
                                                               index=False)


def test_modelos_con_solo_comparadores_marca_la_barra_y_no_falla(tmp_path):
    _metricas(tmp_path, "referencia", "comparador", [("ingenuo", 52.9), ("estacional", 49.0)])
    fm, fp, familias = ep.modelos(tmp_path)
    assert familias == ["comparador"]
    assert fm.set_index("modelo").loc["estacional", "es_barra"]
    assert not fm["supera_barra"].any()


def test_modelos_calcula_la_barra_de_los_comparadores_y_la_diferencia(tmp_path):
    _metricas(tmp_path, "referencia", "comparador", [("ingenuo", 52.9), ("estacional", 49.0)])
    _metricas(tmp_path, "arboles", "modelo", [("bosque", 34.0), ("bosque_sin_2020", 33.0)])
    fm, fp, familias = ep.modelos(tmp_path)
    t = fm.set_index("modelo")
    assert familias == ["comparador", "arboles"]
    assert t.loc["bosque", "mae_vs_barra"] == -15.0
    assert t.loc["bosque", "supera_barra"] and not t.loc["ingenuo", "supera_barra"]
    assert int(fm["es_barra"].sum()) == 1                      # solo un comparador es la barra
    assert t.loc["bosque_sin_2020", "variante"] == "sin_2020"
    assert t.loc["bosque_sin_2020", "modelo_base"] == "bosque"
    assert len(fp) == 8 and set(fp["pliegue"]) == {1, 2}


def test_el_esquema_es_el_mismo_con_y_sin_modelos(tmp_path):
    """Añadir familias no puede cambiar las columnas: el modelo de Power BI no se rompe."""
    solo = tmp_path / "solo"
    todo = tmp_path / "todo"
    _metricas(solo, "referencia", "comparador", [("ingenuo", 52.9)])
    _metricas(todo, "referencia", "comparador", [("ingenuo", 52.9)])
    _metricas(todo, "estadisticos", "modelo", [("ets_desde_2021", 33.0)])
    a, pa, _ = ep.modelos(solo)
    b, pb, _ = ep.modelos(todo)
    assert list(a.columns) == list(b.columns) and list(pa.columns) == list(pb.columns)
    assert b.set_index("modelo").loc["ets_desde_2021", "variante"] == "desde_2021"


def test_modelos_falla_si_faltan_los_comparadores(tmp_path):
    _metricas(tmp_path, "arboles", "modelo", [("bosque", 34.0)])
    with pytest.raises(SystemExit):
        ep.modelos(tmp_path)


def _ajuste(carpeta, filas):
    """Resultados de #45: el archivo trae la familia y la candidata elegida de cada modelo."""
    d = carpeta / "ajuste"
    d.mkdir(parents=True)
    pd.DataFrame([{"modelo": n, "familia": fam, "candidata": cand, "n": 184, "MAE": mae,
                   "RMSE": mae + 5, "MAPE": 10.0, "MASE": mae / 50}
                  for n, fam, cand, mae in filas]).to_csv(d / "metricas_finales.csv", index=False)
    pd.DataFrame([{"modelo": n, "pliegue": k, "MAE": mae, "RMSE": mae + 5, "MAPE": 10.0, "MASE": 1.0}
                  for n, _, _, mae in filas for k in (1, 2)]).to_csv(d / "metricas_por_pliegue.csv",
                                                                     index=False)


def test_ajuste_aparece_con_su_origen_y_la_familia_del_modelo(tmp_path):
    _metricas(tmp_path, "referencia", "comparador", [("ingenuo_estacional", 49.0)])
    _metricas(tmp_path, "estadisticos", "modelo", [("ets", 33.0)])
    _ajuste(tmp_path, [("ets", "estadisticos", "mae_interno", 32.9),
                       ("bosque_aleatorio", "arboles", "fija_44", 34.2)])
    fm, fp, fuentes = ep.modelos(tmp_path)
    assert fuentes == ["comparador", "estadistico", "ajuste"]
    ets = fm[fm["modelo"] == "ets"].set_index("origen")
    assert set(ets.index) == {"#43", "#45"}               # el mismo modelo, una vez por origen
    assert ets.loc["#45", "candidata"] == "mae_interno" and ets.loc["#43", "candidata"] == ""
    assert fm.set_index(["origen", "modelo"]).loc[("#45", "bosque_aleatorio"), "familia"] == "arboles"
    assert ets.loc["#45", "familia"] == "estadistico"       # «estadisticos» de #45 se normaliza
    assert set(fp["origen"]) == {"#42", "#43", "#45"} and fp["familia"].notna().all()


def test_el_esquema_no_cambia_al_añadir_el_ajuste(tmp_path):
    solo, todo = tmp_path / "solo", tmp_path / "todo"
    _metricas(solo, "referencia", "comparador", [("ingenuo", 52.9)])
    _metricas(todo, "referencia", "comparador", [("ingenuo", 52.9)])
    _ajuste(todo, [("ets", "estadisticos", "mae_interno", 32.9)])
    a, pa, _ = ep.modelos(solo)
    b, pb, _ = ep.modelos(todo)
    assert list(a.columns) == list(b.columns) and list(pa.columns) == list(pb.columns)


def test_ajuste_con_una_familia_desconocida_falla(tmp_path):
    _metricas(tmp_path, "referencia", "comparador", [("ingenuo", 52.9)])
    _ajuste(tmp_path, [("modelo_raro", "otra_cosa", "x", 30.0)])
    with pytest.raises(SystemExit):
        ep.modelos(tmp_path)
