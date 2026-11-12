# -*- coding: utf-8 -*-
"""Pruebas del script de auditoría con datos SINTÉTICOS (solo validan el código, no son resultados)."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import auditoria_datasets as aud  # noqa: E402

FILAS = [
    # fecha,        localidad,   tipo,                 cant, id
    ("2017-12-31", "Kennedy",   "Hurto a personas",    "3", "A"),   # fuera de periodo
    ("2018-01-15", "Kennedy",   "Hurto a personas",    "2", "B"),
    ("2018-01-15", "Kennedy",   "Hurto a personas",    "2", "B"),   # duplicado exacto
    ("2018-02-01", "Suba",      "Riña",                "1", "C"),
    ("2019-05-10", "Suba",      "HURTO A COMERCIO",    "-1", "D"),  # cantidad negativa
    ("fecha mala", "Bosa",      "Hurto a personas",    "4", "E"),   # fecha inválida
    ("2025-12-31", "",          "Hurto a personas",    "5", "F"),   # localidad nula
    ("2026-01-01", "Usme",      "Hurto a personas",    "1", "G"),   # fuera de periodo
    ("2020-03-03", "Chapinero", "Accidente",           "x", "H"),   # cantidad no numérica
]
COLS = ["FECHA", "LOCALIDAD", "TIPO INCIDENTE", "CANT_INCIDENTES", "ID"]


def escribir_csv(path, sep=",", encoding="utf-8"):
    pd.DataFrame(FILAS, columns=COLS).to_csv(path, index=False, sep=sep, encoding=encoding)


def fuente(path, **extra):
    f = {"id": "sintetica", "nombre": "Datos sintéticos", "fecha_extraccion": "2026-11-11",
         "unidad_observacion": "fila sintética", "archivos": [str(path)],
         "columnas": {"fecha": "FECHA", "localidad": "LOCALIDAD", "delito": "TIPO INCIDENTE",
                      "cantidad": "CANT_INCIDENTES", "id": "ID"},
         "filtros": {"hurto": {"columna": "TIPO INCIDENTE", "patron": "HURTO"}}}
    f.update(extra)
    return f


def correr(f, tmp_path, chunksize=1000):
    a = aud.auditar_fuente(f, (2018, 2025), chunksize, tmp_path)
    return a, a.resultados()


def test_normalizar_nombre():
    assert aud.normalizar_nombre(" FECHA HECHO ") == "fecha_hecho"
    assert aud.normalizar_nombre("Año") == "ano"
    assert aud.normalizar_nombre("Cant. Incidentes") == "cant_incidentes"


def test_conteos_basicos_y_embudo(tmp_path):
    p = tmp_path / "d.csv"
    escribir_csv(p)
    a, r = correr(fuente(p), tmp_path)
    assert r["embudo"]["1_original"] == 9
    assert r["embudo"]["2_bogota"] == 9           # filtro no configurado: no excluye
    # periodo 2018–2025: excluye 2017, 2026 y la fecha inválida
    assert r["embudo"]["3_periodo"] == 6
    # hurto dentro del periodo: B, B, D (comercio), F
    assert r["embudo"]["4_hurto"] == 4
    assert r["suma_cantidad_embudo"]["4_hurto"] == pytest.approx(2 + 2 - 1 + 5)
    assert a.archivos[0]["filas"] == 9 and a.archivos[0]["columnas"] == 5


def test_hash_y_tamano(tmp_path):
    p = tmp_path / "d.csv"
    escribir_csv(p)
    a, _ = correr(fuente(p), tmp_path)
    assert a.archivos[0]["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert a.archivos[0]["tamano_bytes"] == p.stat().st_size


def test_duplicados_exactos_y_por_id(tmp_path):
    p = tmp_path / "d.csv"
    escribir_csv(p)
    _, r = correr(fuente(p), tmp_path)
    assert r["duplicados"]["exactos_original"]["repetidas"] == 1
    assert r["duplicados"]["id_original"]["unicos"] == 8
    assert r["duplicados"]["id_final"] == {"filas": 4, "unicos": 3, "repetidas": 1, "valores_repetidos": 1,
                                           "max_repeticiones": 2}


def test_nulos_fechas_y_anomalias(tmp_path):
    p = tmp_path / "d.csv"
    escribir_csv(p)
    a, r = correr(fuente(p), tmp_path)
    assert a.columnas["localidad"].nulos == 1
    assert r["fechas"]["invalidas"] == 1
    assert r["fechas"]["fuera_periodo"] == 2
    assert r["fechas"]["min"].startswith("2017-12-31") and r["fechas"]["max"].startswith("2026-01-01")
    tipos = {x["tipo"]: x["filas"] for x in a.anomalias}
    assert tipos["cantidad_negativa"] == 1
    assert tipos["cantidad_no_numerica"] == 1
    assert tipos["fecha_invalida"] == 1
    cant = r["numericas"]["cant_incidentes"]
    assert cant["negativos"] == 1 and cant["min"] == -1 and cant["max"] == 5


@pytest.mark.parametrize("chunksize", [1, 2, 4])
def test_resultado_independiente_del_bloque(tmp_path, chunksize):
    p = tmp_path / "d.csv"
    escribir_csv(p)
    _, ref = correr(fuente(p), tmp_path, 1000)
    a, r = correr(fuente(p), tmp_path, chunksize)
    assert r["embudo"] == ref["embudo"]
    assert r["suma_cantidad_embudo"] == ref["suma_cantidad_embudo"]
    assert r["duplicados"] == ref["duplicados"]
    assert r["fechas"] == ref["fechas"]


def test_csv_latin1_punto_y_coma(tmp_path):
    p = tmp_path / "d.csv"
    escribir_csv(p, sep=";", encoding="cp1252")
    a, r = correr(fuente(p), tmp_path)
    assert a.archivos[0]["separador"] == ";"
    assert a.archivos[0]["codificacion"] == "cp1252"
    assert r["embudo"]["1_original"] == 9


def test_xlsx_con_encabezado_desplazado_y_renombrado(tmp_path):
    p = tmp_path / "policia.xlsx"
    df = pd.DataFrame(FILAS, columns=["FECHA HECHO", "LOCALIDAD", "TIPO INCIDENTE", "CANTIDAD", "ID"])
    with pd.ExcelWriter(p) as w:
        pd.DataFrame([["Título del reporte"], ["Fuente: sintética"]]).to_excel(w, index=False, header=False)
        df.to_excel(w, index=False, startrow=2)
    f = fuente(p, lectura={"fila_encabezado": 2}, renombrar={"FECHA HECHO": "FECHA", "CANTIDAD": "CANT_INCIDENTES"})
    _, r = correr(f, tmp_path)
    assert r["embudo"]["1_original"] == 9
    assert r["embudo"]["4_hurto"] == 4


def test_xlsx_pie_de_archivo_se_descarta_y_registra(tmp_path):
    p = tmp_path / "policia_pie.xlsx"
    df = pd.DataFrame(FILAS, columns=COLS)
    pie = pd.DataFrame([[None] * 5, [None] * 5, ["Fecha de entrega: 20 de agosto de 2026"] + [None] * 4,
                        ["Nota: género y edad sin calidad validada."] + [None] * 4])
    with pd.ExcelWriter(p) as w:
        df.to_excel(w, index=False)
        pie.to_excel(w, index=False, header=False, startrow=len(df) + 1)
    a, r = correr(fuente(p), tmp_path)
    assert r["embudo"]["1_original"] == 9            # las filas de pie no cuentan
    assert a.archivos[0]["filas_pie_descartadas"] >= 2
    an = [x for x in a.anomalias if x["tipo"] == "pie_de_archivo_descartado"]
    assert an and an[0]["filas"] == a.archivos[0]["filas_pie_descartadas"]
    assert "Fecha de entrega" in an[0]["ejemplo"]
    # desactivable desde el manifiesto: las notas vuelven a contarse como filas
    a2, r2 = correr(fuente(p, lectura={"descartar_pie": False}), tmp_path)
    assert r2["embudo"]["1_original"] > 9
    assert not [x for x in a2.anomalias if x["tipo"] == "pie_de_archivo_descartado"]


def test_filtro_bogota_y_anio_mes(tmp_path):
    p = tmp_path / "f.csv"
    pd.DataFrame({"cod_dane_hecho": ["11001", "05001", "11001", "11001"],
                  "a_o_hecho": ["2018", "2018", "2030", "abc"], "mes_hecho": ["1", "2", "13", "1"],
                  "capitulo_delito": ["Del Hurto", "Del Hurto", "Del Hurto", "De Las Lesiones"],
                  "proceso_anonimizado": ["p1", "p2", "p3", "p4"]}).to_csv(p, index=False)
    f = {"id": "fisc", "fecha_extraccion": "2026-11-11", "archivos": [str(p)],
         "columnas": {"anio": "a_o_hecho", "mes": "mes_hecho", "id": "proceso_anonimizado", "delito": "capitulo_delito"},
         "filtros": {"bogota": {"columna": "cod_dane_hecho", "patron": "^11001$"},
                     "hurto": {"columna": "capitulo_delito", "patron": "^DEL HURTO$"}}}
    a, r = correr(f, tmp_path)
    assert r["embudo"] == {"1_original": 4, "2_bogota": 3, "3_periodo": 1, "4_hurto": 1}
    tipos = {x["tipo"] for x in a.anomalias}
    assert {"anio_invalido", "mes_invalido"} <= tipos


def test_errores_claros(tmp_path):
    with pytest.raises(aud.ErrorAuditoria, match="No se encontró"):
        aud.auditar_fuente(fuente(tmp_path / "no_existe.csv"), (2018, 2025), 10, tmp_path)
    p = tmp_path / "d.csv"
    escribir_csv(p)
    with pytest.raises(aud.ErrorAuditoria, match="fecha_extraccion"):
        aud.auditar_fuente(fuente(p, fecha_extraccion="AAAA-MM-DD"), (2018, 2025), 10, tmp_path)
    mal = fuente(p)
    mal["columnas"]["fecha"] = "COLUMNA_INEXISTENTE"
    with pytest.raises(aud.ErrorAuditoria, match="no existen"):
        aud.auditar_fuente(mal, (2018, 2025), 10, tmp_path)
    q = tmp_path / "d.parquet"
    q.write_bytes(b"x")
    with pytest.raises(aud.ErrorAuditoria, match="no soportado"):
        aud.auditar_fuente(fuente(q), (2018, 2025), 10, tmp_path)


def test_main_genera_todas_las_salidas(tmp_path):
    p = tmp_path / "d.csv"
    escribir_csv(p)
    cfg = tmp_path / "manifiesto.json"
    cfg.write_text(json.dumps({"periodo": {"anio_min": 2018, "anio_max": 2025}, "fuentes": [fuente(p)]}), encoding="utf-8")
    salida = tmp_path / "out"
    assert aud.main(["--config", str(cfg), "--salida", str(salida), "--chunksize", "3"]) == 0
    esperados = ["resumen_fuentes.csv", "resumen_archivos.csv", "diccionario_variables.csv", "valores_nulos.csv",
                 "duplicados.csv", "cobertura_temporal.csv", "distribuciones_categoricas.csv",
                 "estadisticas_numericas.csv", "embudo_filtros.csv", "anomalias.csv", "auditoria.json",
                 "reporte_auditoria.md"]
    for e in esperados:
        assert (salida / e).exists(), e
    res = pd.read_csv(salida / "resumen_fuentes.csv")
    assert res.loc[0, "filas_hurto"] == 4 and not res.loc[0, "filas_hurto_>=_500000"]
    assert (salida / "figuras" / "sintetica_embudo.pdf").exists()
    meta = json.loads((salida / "auditoria.json").read_text(encoding="utf-8"))["metadatos"]
    assert meta["semilla"] == 42 and "pandas" in meta["versiones"]


def test_main_codigo_error(tmp_path):
    assert aud.main(["--config", str(tmp_path / "no.json")]) == 2
