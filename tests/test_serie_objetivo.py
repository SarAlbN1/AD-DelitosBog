# -*- coding: utf-8 -*-
"""Pruebas de la serie objetivo y de la clasificación de Fiscalía con datos SINTÉTICOS."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fiscalia_modalidades as fm  # noqa: E402
import serie_objetivo_policia as so  # noqa: E402

CABECERA = "ARMAS MEDIOS,DEPARTAMENTO,MUNICIPIO,FECHA HECHO,GENERO,*AGRUPA EDAD PERSONA*,CODIGO DANE,DELITOS,MES,CANTIDAD\n"
HURTO = "(05022) Hurto a personas"


def fila(fecha, dane="11001", delito=HURTO, genero="FEMENINO"):
    return f"SIN EMPLEO DE ARMAS,CUNDINAMARCA,Bogotá,{fecha},{genero},DE 18 AÑOS Y MÁS,{dane},{delito},01,1\n"


def test_serie_conserva_filas_identicas_y_rellena_el_calendario(tmp_path, monkeypatch):
    monkeypatch.setattr(so, "INICIO", "2020-01-01")
    monkeypatch.setattr(so, "FIN", "2020-01-04")
    filas = [
        fila("2020/01/01"), fila("2020/01/01"),          # dos víctimas idénticas: ambas cuentan
        fila("2020/01/02", dane="05001"),                 # Medellín: fuera
        fila("2020/01/02", delito="(05024) Hurto a residencias"),  # otro delito: fuera
        fila("2020/01/04", genero=""),                    # género nulo: cuenta
    ]
    ruta = tmp_path / "delitos_registro_2020.csv"
    ruta.write_text(CABECERA + "".join(filas), encoding="utf-8")

    registros, meta = so.leer([ruta], chunksize=2)
    serie, resumen = so.construir(registros, meta)

    assert meta["filas_entrada"] == 5 and meta["filas_bogota"] == 4 and meta["filas_hurto"] == 3
    assert serie["victimas"].tolist() == [2, 0, 0, 1]
    assert resumen["dias"] == 4 and resumen["dias_sin_registros"] == 2
    assert resumen["filas_en_la_serie"] == 3
    assert meta["perfil_poblacion"]["GENERO"]["nulos"] == 1


def test_serie_unifica_el_nombre_del_arma_de_2021(tmp_path):
    ruta = tmp_path / "delitos_registro_2021.csv"
    ruta.write_text(CABECERA.replace("ARMAS MEDIOS", "ARMA MEDIO") + fila("2021/03/01"), encoding="utf-8")
    _, meta = so.leer([ruta], chunksize=10)
    assert meta["perfil_poblacion"]["ARMAS MEDIOS"]["frecuencias"] == {"SIN EMPLEO DE ARMAS": 1}


def test_fiscalia_clasifica_por_el_texto_del_tipo_penal():
    assert fm.clasificar("Hurto. Art. 239 C.P.") == "generico_sin_modalidad"
    assert fm.clasificar("Hurto Calificado Art. 240 C.P. Mayor Cuantia") == "generico_sin_modalidad"
    assert fm.clasificar("Hurto Agravado Art. 241 C.P. Num 6 Medios Motorizados") == "medios_motorizados_241_6"
    assert fm.clasificar("Hurto De Automotores") == "automotor"
    assert fm.clasificar("Hurto Agravado Art. 241 C.P. Num 11 Establecimiento Publico") == "establecimiento_publico_241_11"
    assert fm.clasificar("Hurto Calificado Art. 240 C.P. Agravado") == "otro_no_excluible"
    assert isinstance(pd.Series(["x"]).map(fm.clasificar).iloc[0], str)
