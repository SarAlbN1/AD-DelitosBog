"""Pruebas del entorno de modelado (#41).

Se centran en lo que, si fallara, produciría números plausibles pero falsos: una configuración
inválida que pasa, una semilla que no fija nada, o un registro que acepta dos resultados distintos
para la misma corrida.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

from modelado import cargar, fijar_semillas  # noqa: E402
from modelado.config import ErrorConfig, validar_contra_serie  # noqa: E402
from modelado.registro import (Registro, comprobar_determinismo, huella,  # noqa: E402
                               registrar, versiones)


def base() -> dict:
    return json.loads((RAIZ / "config" / "modelado.json").read_text(encoding="utf-8"))


def escribir(tmp_path: Path, d: dict) -> Path:
    cfg = tmp_path / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    p = cfg / "modelado.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- la configuración real
def test_la_configuracion_del_proyecto_es_valida():
    c = cargar()
    assert c.semilla == 42
    assert c.horizonte_dias == 1
    assert c.esquema == "origen_rodante"
    assert c.metrica_principal == "MAE"
    assert set(c.metricas) == {"MAE", "RMSE", "MAPE", "MASE"}
    assert c.periodo_estacional_mase == 7
    assert c.fin_entrenamiento == "2025-04-30"


def test_la_configuracion_codifica_lo_que_fija_d04():
    """Si alguien cambia el protocolo en el JSON, esta prueba lo delata."""
    c = cargar()
    assert c.pliegues == 6 and c.dias_pliegue == 90
    assert c.criterio_barra == "mejor_comparador_en_evaluacion"
    assert c.anio_atipico == 2020 and c.prueba_sensibilidad is True
    assert "fiscalia.estado" in c.excluidas_por_fuga


def test_la_huella_de_la_configuracion_cambia_si_cambia_el_contenido(tmp_path):
    d = base()
    a = cargar(escribir(tmp_path, d))
    d["semilla"] = 7
    b = cargar(escribir(tmp_path / "otra", d))
    assert a.sha256 != b.sha256


# --------------------------------------------------------------------------- validación
def test_rechaza_una_validacion_aleatoria(tmp_path):
    d = base()
    d["validacion"]["esquema"] = "k_fold_aleatorio"
    with pytest.raises(ErrorConfig, match="no admitido"):
        cargar(escribir(tmp_path, d))


def test_rechaza_una_metrica_principal_que_no_se_reporta(tmp_path):
    d = base()
    d["metricas"]["principal"] = "RMSE"
    d["metricas"]["reportadas"] = ["MAE", "MAPE"]
    with pytest.raises(ErrorConfig, match="no está entre las reportadas"):
        cargar(escribir(tmp_path, d))


def test_rechaza_una_metrica_desconocida(tmp_path):
    d = base()
    d["metricas"]["reportadas"] = ["MAE", "R2"]
    with pytest.raises(ErrorConfig, match="desconocidas"):
        cargar(escribir(tmp_path, d))


def test_rechaza_una_fecha_de_particion_invalida(tmp_path):
    d = base()
    d["particion"]["fin_entrenamiento"] = "30/04/2025"
    with pytest.raises(ErrorConfig, match="AAAA-MM-DD"):
        cargar(escribir(tmp_path, d))


@pytest.mark.parametrize("campo,valor", [("pliegues", 0), ("dias_pliegue", -5),
                                         ("minimo_entrenamiento", 1.5)])
def test_rechaza_enteros_no_positivos(tmp_path, campo, valor):
    d = base()
    d["validacion"][campo] = valor
    with pytest.raises(ErrorConfig, match="entero positivo"):
        cargar(escribir(tmp_path, d))


def test_rechaza_un_json_invalido(tmp_path):
    p = tmp_path / "roto.json"
    p.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ErrorConfig, match="JSON válido"):
        cargar(p)


# --------------------------------------------------------------------------- contra la serie
def test_rechaza_una_particion_fuera_del_rango_de_la_serie():
    c = cargar()
    idx = pd.date_range("2024-01-01", "2024-12-31", freq="D")
    with pytest.raises(ErrorConfig, match="deja un lado vacío"):
        validar_contra_serie(c, idx)


def test_rechaza_pliegues_que_no_caben(tmp_path):
    d = base()
    d["validacion"].update(pliegues=20, dias_pliegue=200, minimo_entrenamiento=365)
    c = cargar(escribir(tmp_path, d))
    idx = pd.date_range("2020-01-01", "2025-10-31", freq="D")
    with pytest.raises(ErrorConfig, match="no caben"):
        validar_contra_serie(c, idx)


def test_acepta_la_serie_real():
    c = cargar()
    idx = pd.date_range("2020-01-01", "2025-10-31", freq="D")
    validar_contra_serie(c, idx)  # no debe lanzar


# --------------------------------------------------------------------------- semillas
def test_fijar_semillas_hace_reproducible_a_random():
    fijar_semillas(42)
    a = [random.random() for _ in range(5)]
    fijar_semillas(42)
    assert a == [random.random() for _ in range(5)]


def test_fijar_semillas_hace_reproducible_a_numpy():
    import numpy as np
    fijar_semillas(42)
    a = np.random.rand(5).tolist()
    fijar_semillas(42)
    assert a == np.random.rand(5).tolist()


def test_semillas_distintas_dan_resultados_distintos():
    fijar_semillas(1)
    a = [random.random() for _ in range(5)]
    fijar_semillas(2)
    assert a != [random.random() for _ in range(5)]


def test_fijar_semillas_devuelve_la_semilla_para_pasarla():
    assert fijar_semillas(42) == 42


@pytest.mark.parametrize("malo", ["42", 4.2, None, True])
def test_rechaza_una_semilla_que_no_es_entero(malo):
    with pytest.raises(TypeError):
        fijar_semillas(malo)


# --------------------------------------------------------------------------- registro
class CfgFalso:
    def __init__(self, carpeta: Path):
        self.carpeta_registro = carpeta
        self.indice_registro = "experimentos.csv"
        self.sha256 = "abc123"
        self.semilla = 42

    def resumen(self):
        return {"config_sha256": self.sha256, "semilla": self.semilla}


def test_la_huella_no_depende_del_momento():
    a = huella("sha", "RF", {"n": 10}, 42)
    b = huella("sha", "RF", {"n": 10}, 42)
    assert a == b


@pytest.mark.parametrize("cambio", [
    {"cfg_sha": "otro"}, {"modelo": "GBM"}, {"hiperparametros": {"n": 11}}, {"semilla": 7},
])
def test_la_huella_cambia_con_cualquier_cosa_que_afecte_al_resultado(cambio):
    args = {"cfg_sha": "sha", "modelo": "RF", "hiperparametros": {"n": 10}, "semilla": 42}
    assert huella(**args) != huella(**{**args, **cambio})


def test_el_registro_falla_si_la_misma_corrida_da_otras_metricas(tmp_path):
    cfg = CfgFalso(tmp_path)
    registrar(cfg, "RF", {"n": 10}, {"MAE": 40.0})
    with pytest.raises(RuntimeError, match="ya existe con otras métricas"):
        registrar(cfg, "RF", {"n": 10}, {"MAE": 41.0})


def test_el_registro_acepta_repetir_la_misma_corrida(tmp_path):
    cfg = CfgFalso(tmp_path)
    a = registrar(cfg, "RF", {"n": 10}, {"MAE": 40.0})
    b = registrar(cfg, "RF", {"n": 10}, {"MAE": 40.0})
    assert a["huella"] == b["huella"]
    assert len(Registro(tmp_path).leer_indice()) == 1, "la corrida repetida se duplicó en el índice"


def test_comprobar_determinismo_detecta_la_diferencia(tmp_path):
    cfg = CfgFalso(tmp_path)
    registrar(cfg, "RF", {"n": 10}, {"MAE": 40.0})
    assert comprobar_determinismo(cfg, "RF", {"n": 10}, {"MAE": 40.0})
    assert not comprobar_determinismo(cfg, "RF", {"n": 10}, {"MAE": 41.0})


def test_comprobar_determinismo_sin_registro_previo_no_falla(tmp_path):
    assert comprobar_determinismo(CfgFalso(tmp_path), "RF", {"n": 10}, {"MAE": 40.0})


def test_el_registro_guarda_las_versiones(tmp_path):
    e = registrar(CfgFalso(tmp_path), "RF", {"n": 10}, {"MAE": 40.0})
    assert e["versiones"]["python"]
    assert "pandas" in e["versiones"]


def test_versiones_no_falla_si_una_biblioteca_no_esta():
    v = versiones()
    assert "xgboost" in v  # presente aunque no se pueda importar
