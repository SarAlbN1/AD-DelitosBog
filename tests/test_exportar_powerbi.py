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
