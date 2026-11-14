#!/usr/bin/env python3
"""Comprueba si la caída del hurto registrado en noviembre y diciembre de 2025 es real (#86).

El registro de la Policía muestra en esos dos meses algo más de la mitad de las víctimas de los
meses anteriores. Antes de usarlos para entrenar o evaluar un modelo hay que saber si el fenómeno
bajó de verdad o si el archivo todavía no tiene cargados esos meses.

La prueba decisiva es contrastar con una fuente **independiente**. El agregado diario de MinDefensa
no sirve para eso: ya se demostró que es la agregación del mismo registro, así que repetiría el
mismo sesgo. Línea 123 sí es independiente: son llamadas al 123 tramitadas por el C4, con otro
circuito de captura y otra entidad.

Uso:

    python scripts/verificar_caida_2025.py

Lee `data/raw/policia_registro/csv/delitos_registro_2025.csv`, `data/raw/hurto_bogota.csv` y
`data/raw/linea123.csv`, y escribe `outputs/verificacion_caida_2025/`.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import logging
import sys
from pathlib import Path

log = logging.getLogger("caida2025")

HURTO_ICCS = "(05022)"
DANE_BOGOTA = "11001"
#: Meses bajo sospecha.
MESES_SOSPECHOSOS = ("2025/11", "2025/12")
#: Caída relativa desde la que se considera que el mes está incompleto.
UMBRAL_CAIDA = 0.30


def _mes(fecha: str) -> str:
    return fecha[:7]


def contar_registro(path: Path) -> tuple[dict, dict, dict]:
    """Devuelve (hurto Bogotá por mes, hurto Bogotá por día, todos los delitos del país por mes)."""
    mes, dia, nacional = collections.Counter(), collections.Counter(), collections.Counter()
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            nacional[_mes(r["FECHA HECHO"])] += 1
            if r["CODIGO DANE"].lstrip("0") == DANE_BOGOTA and HURTO_ICCS in r["DELITOS"]:
                mes[_mes(r["FECHA HECHO"])] += 1
                dia[r["FECHA HECHO"]] += 1
    return dict(mes), dict(dia), dict(nacional)


def contar_agregado(path: Path, anio: str = "2025") -> dict:
    c = collections.Counter()
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["fecha_hecho"].startswith(anio):
                c[r["fecha_hecho"][:7].replace("-", "/")] += int(r["cantidad"])
    return dict(c)


def contar_linea123(path: Path, anio: str = "2025") -> dict:
    """Suma CANT_INCIDENTES, no cuenta filas: las filas son grupos agregados."""
    c = collections.Counter()
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["ANIO"] != anio or "HURTO" not in (r["TIPO_DETALLE"] or "").upper():
                continue
            try:
                cant = int(float(r["CANT_INCIDENTES"]))
            except (TypeError, ValueError):
                cant = 0
            c[f"{anio}/{int(r['MES']):02d}"] += cant
    return dict(c)


def media_de_referencia(serie: dict, excluir: tuple[str, ...]) -> float:
    base = [v for k, v in serie.items() if k not in excluir]
    return sum(base) / len(base) if base else 0.0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Verifica la caída de noviembre y diciembre de 2025 (#86).")
    p.add_argument("--registro", type=Path,
                   default=Path("data/raw/policia_registro/csv/delitos_registro_2025.csv"))
    p.add_argument("--agregado", type=Path, default=Path("data/raw/hurto_bogota.csv"))
    p.add_argument("--linea123", type=Path, default=Path("data/raw/linea123.csv"))
    p.add_argument("--salida", type=Path, default=Path("outputs/verificacion_caida_2025"))
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    faltan = [x for x in (a.registro, a.agregado, a.linea123) if not x.is_file()]
    if faltan:
        for x in faltan:
            log.error("no existe: %s", x)
        log.error("reproduzca las descargas con las instrucciones de data/README.md")
        return 2

    reg_mes, reg_dia, nacional = contar_registro(a.registro)
    agg = contar_agregado(a.agregado)
    l123 = contar_linea123(a.linea123)

    ref_reg = media_de_referencia(reg_mes, MESES_SOSPECHOSOS)
    ref_123 = media_de_referencia(l123, MESES_SOSPECHOSOS)

    filas = []
    for m in sorted(set(reg_mes) | set(agg) | set(l123)):
        filas.append({
            "mes": m,
            "registro_policia": reg_mes.get(m, 0),
            "agregado_mindefensa": agg.get(m, 0),
            "linea123_incidentes": l123.get(m, 0),
            "nacional_todos_los_delitos": nacional.get(m, 0),
            "var_registro_vs_media": round(reg_mes.get(m, 0) / ref_reg - 1, 4) if ref_reg else None,
            "var_linea123_vs_media": round(l123.get(m, 0) / ref_123 - 1, 4) if ref_123 else None,
        })

    a.salida.mkdir(parents=True, exist_ok=True)
    with open(a.salida / "comparacion_mensual_2025.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    with open(a.salida / "hurto_bogota_diario_2025.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "victimas"])
        for d in sorted(reg_dia):
            w.writerow([d, reg_dia[d]])

    # ---- veredicto
    caida_reg = {m: 1 - reg_mes.get(m, 0) / ref_reg for m in MESES_SOSPECHOSOS if ref_reg}
    caida_123 = {m: 1 - l123.get(m, 0) / ref_123 for m in MESES_SOSPECHOSOS if ref_123}
    registro_cae = all(v >= UMBRAL_CAIDA for v in caida_reg.values())
    independiente_cae = any(v >= UMBRAL_CAIDA for v in caida_123.values())

    if registro_cae and not independiente_cae:
        veredicto = "artefacto"
        explicacion = ("El registro cae pero la fuente independiente no. La caída no es del fenómeno: "
                       "esos meses están incompletos en el archivo de la Policía.")
    elif registro_cae and independiente_cae:
        veredicto = "real"
        explicacion = "Las dos fuentes caen a la vez, así que la caída es del fenómeno."
    else:
        veredicto = "sin_caida"
        explicacion = "El registro no cae por encima del umbral."

    dias_con_datos = {m: sum(1 for d in reg_dia if d.startswith(m)) for m in MESES_SOSPECHOSOS}

    doc = {
        "veredicto": veredicto,
        "explicacion": explicacion,
        "umbral_caida": UMBRAL_CAIDA,
        "media_mensual_de_referencia": {"registro": round(ref_reg, 1), "linea123": round(ref_123, 1)},
        "caida_registro": {k: round(v, 4) for k, v in caida_reg.items()},
        "caida_linea123": {k: round(v, 4) for k, v in caida_123.items()},
        "dias_con_datos_en_meses_sospechosos": dias_con_datos,
        "nacional_todos_los_delitos": {m: nacional.get(m, 0) for m in ("2025/10",) + MESES_SOSPECHOSOS},
        "corte_recomendado": "2025-10-31" if veredicto == "artefacto" else None,
        "meses": filas,
    }
    (a.salida / "veredicto.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("veredicto: %s", veredicto.upper())
    log.info("%s", explicacion)
    for m in MESES_SOSPECHOSOS:
        log.info("%s: registro %+.1f%% · Línea 123 %+.1f%% · %s días con datos",
                 m, -100 * caida_reg.get(m, 0), -100 * caida_123.get(m, 0), dias_con_datos[m])
    if doc["corte_recomendado"]:
        log.info("corte recomendado de la serie: %s", doc["corte_recomendado"])
    log.info("salidas en %s", a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
