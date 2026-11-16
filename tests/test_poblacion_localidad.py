"""Pruebas de scripts/poblacion_localidad.py con filas sintéticas (no necesitan el .ods real)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import poblacion_localidad as pl  # noqa: E402

ENC = (["Departamento", "Nombre Departamento", "Municipio", "Nombre municipio", "Código Localidad",
        "Nombre Localidad", "Área", "AÑO"]
       + [f"Total_{i}" for i in range(100)] + ["Total_100 y más", "Total Hombres", "Total Mujeres", "Total"])


def fila(cod, nombre, area, anio, por_edad=1, hombres=None):
    total = 101 * por_edad
    h = total // 2 if hombres is None else hombres
    return (["11", "Bogotá, D.C.", "11001", "Bogotá, D.C.", str(cod), nombre, area, str(anio)]
            + [str(por_edad)] * 101 + [str(h), str(total - h), str(total)])


def archivo(anios=(2020, 2021), rural=(20,)):
    filas = [[], ["título"], ENC]
    for anio in anios:
        for cod in range(1, 21):
            filas.append(fila(cod, f"Loc {cod}" if cod != 17 else "La Candelaria", "Cabecera Municipal", anio))
            if cod in rural:
                filas.append(fila(cod, f"Loc {cod}", "Centro Poblado y Rural Disperso", anio, por_edad=2))
    return filas


def test_suma_cabecera_y_rural():
    salida, resumen = pl.agregar(archivo(), 2020, 2021)
    assert len(salida) == 40
    r = next(x for x in salida if x["codigo_localidad"] == 20 and x["anio"] == 2020)
    assert (r["habitantes_cabecera"], r["habitantes_rural"], r["habitantes"]) == (101, 202, 303)
    assert resumen["bogota_por_anio"][2020] == 20 * 101 + 202


def test_filtra_el_periodo():
    salida, _ = pl.agregar(archivo(anios=(2019, 2020, 2021)), 2020, 2020)
    assert {x["anio"] for x in salida} == {2020}


def test_rechaza_un_total_inconsistente():
    filas = archivo()
    filas[3][-1] = "999"
    with pytest.raises(ValueError, match="inconsistente"):
        pl.agregar(filas, 2020, 2021)


def test_rechaza_un_periodo_fuera_del_archivo():
    with pytest.raises(ValueError, match="cubre"):
        pl.agregar(archivo(), 2018, 2021)


@pytest.mark.parametrize("nombre, esperado", [
    ("Engativá", "ENGATIVA"),
    ("Ciudad Bolivar", "CIUDAD BOLIVAR"),
    ("Los Mártires", "LOS MARTIRES"),
    ("La Candelaria", "CANDELARIA"),
    ("Antonio Nariño", "ANTONIO NARINO"),
])
def test_clave_cruza_con_linea123(nombre, esperado):
    assert pl.clave(nombre) == esperado
