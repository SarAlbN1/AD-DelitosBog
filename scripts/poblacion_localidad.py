#!/usr/bin/env python3
"""Población por localidad y año a partir de las proyecciones oficiales de la SDP.

Fuente: «Proyecciones y retroproyecciones de Población (2005 - 2035)», Secretaría Distrital de
Planeación (SDP), Datos Abiertos Bogotá. Recurso por localidad, versión de marzo de 2025
(``202503_localidad_proyeccion_retroproyeccion_poblacion_2005_2035.ods``). La URL, la fecha de
descarga y la huella están en ``data/README.md``.

El archivo trae una fila por localidad, año y área (cabecera municipal o centro poblado y rural
disperso), con la población por sexo y edad simple y una columna ``Total``. Este script suma las dos
áreas y deja una fila por localidad y año, que es la resolución de la Línea 123.

Se usa para calcular tasas de llamadas por 100.000 habitantes. La población es residente: no
incluye la población flotante, así que la tasa de las localidades que reciben a mucha gente que
no vive en ellas sale inflada.

Lee el ``.ods`` con la biblioteca estándar (es un ZIP con XML), sin dependencias adicionales.

Uso::

    python scripts/poblacion_localidad.py
    python scripts/poblacion_localidad.py --desde 2018 --hasta 2025
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

log = logging.getLogger("poblacion_localidad")

ENTRADA = Path("data/raw/poblacion/202503_localidad_proyeccion_retroproyeccion_poblacion_2005_2035.ods")
SALIDA = Path("outputs/poblacion")

_T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
_O = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
_TEXTO = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"
#: Las filas y celdas vacías del final de una hoja se declaran repetidas miles de veces.
_MAX_REPETICION = 400

#: La Línea 123 escribe «CANDELARIA» sin artículo. El resto coincide al quitar tildes.
CLAVE_LINEA123 = {"LA CANDELARIA": "CANDELARIA"}


def clave(nombre: str) -> str:
    """Nombre en mayúsculas y sin tildes, con el que se cruza con la Línea 123."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn")
    k = " ".join(sin_tildes.upper().split())
    return CLAVE_LINEA123.get(k, k)


def _valor(celda: ET.Element) -> str:
    v = celda.get(_O + "value")
    if v is not None:
        return v
    return "\n".join("".join(p.itertext()) for p in celda.findall(_TEXTO))


def leer_ods(ruta: Path) -> list[list[str]]:
    """Filas de la primera hoja del .ods, como texto."""
    with zipfile.ZipFile(ruta) as z:
        raiz = ET.fromstring(z.read("content.xml"))
    tabla = next(raiz.iter(_T + "table"))
    filas = []
    for fila in tabla.iter(_T + "table-row"):
        celdas: list[str] = []
        for c in fila:
            if c.tag in (_T + "table-cell", _T + "covered-table-cell"):
                rep = int(c.get(_T + "number-columns-repeated", "1"))
                celdas.extend([_valor(c)] * min(rep, _MAX_REPETICION))
        while celdas and celdas[-1] == "":
            celdas.pop()
        if celdas:
            filas.extend([celdas] * min(int(fila.get(_T + "number-rows-repeated", "1")), _MAX_REPETICION))
    return filas


def agregar(filas: list[list[str]], desde: int, hasta: int) -> tuple[list[dict], dict]:
    """Suma las áreas de cada localidad y año, y comprueba la consistencia interna del archivo."""
    i_enc = next(i for i, f in enumerate(filas) if f and f[0] == "Departamento")
    enc = filas[i_enc]
    col = {nombre: i for i, nombre in enumerate(enc)}
    c_cod, c_nom, c_area, c_anio = (col["Código Localidad"], col["Nombre Localidad"], col["Área"], col["AÑO"])
    c_total, c_h, c_m = col["Total"], col["Total Hombres"], col["Total Mujeres"]
    c_edades = [i for n, i in col.items() if n.startswith("Total_")]
    if len(c_edades) != 101:
        raise ValueError(f"se esperaban 101 columnas de edad (0 a 100 y más) y hay {len(c_edades)}")

    datos = [f for f in filas[i_enc + 1:] if f and f[0] == "11"]
    areas, anios = set(), set()
    pob: dict[tuple, dict] = defaultdict(lambda: {"cabecera": 0, "rural": 0})
    nombres: dict[int, str] = {}
    for f in datos:
        total, h, m = int(float(f[c_total])), int(float(f[c_h])), int(float(f[c_m]))
        suma_edades = sum(int(float(f[i])) for i in c_edades)
        if total != h + m or total != suma_edades:
            raise ValueError(f"fila inconsistente: {f[:8]} total={total} h+m={h + m} edades={suma_edades}")
        anio, cod = int(float(f[c_anio])), int(float(f[c_cod]))
        anios.add(anio)
        areas.add(f[c_area])
        nombres[cod] = f[c_nom]
        parte = "cabecera" if f[c_area] == "Cabecera Municipal" else "rural"
        pob[(cod, anio)][parte] += total

    if areas != {"Cabecera Municipal", "Centro Poblado y Rural Disperso"}:
        raise ValueError(f"áreas inesperadas: {sorted(areas)}")
    if sorted(nombres) != list(range(1, 21)):
        raise ValueError(f"se esperaban las 20 localidades y hay {sorted(nombres)}")
    if not (min(anios) <= desde and hasta <= max(anios)):
        raise ValueError(f"el archivo cubre {min(anios)}–{max(anios)}; se pidió {desde}–{hasta}")

    salida = []
    for (cod, anio), p in sorted(pob.items()):
        if desde <= anio <= hasta:
            salida.append({
                "codigo_localidad": cod,
                "localidad": nombres[cod],
                "clave": clave(nombres[cod]),
                "anio": anio,
                "habitantes": p["cabecera"] + p["rural"],
                "habitantes_cabecera": p["cabecera"],
                "habitantes_rural": p["rural"],
            })
    total_anio = defaultdict(int)
    for r in salida:
        total_anio[r["anio"]] += r["habitantes"]
    resumen = {
        "filas_archivo": len(datos),
        "anios_archivo": [min(anios), max(anios)],
        "localidades": len(nombres),
        "periodo_salida": [desde, hasta],
        "filas_salida": len(salida),
        "bogota_por_anio": dict(sorted(total_anio.items())),
        "comprobaciones": [
            "Total = Total Hombres + Total Mujeres en cada fila",
            "Total = suma de las 101 edades simples en cada fila",
            "20 localidades y dos áreas: cabecera municipal y centro poblado y rural disperso",
        ],
    }
    return salida, resumen


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--entrada", type=Path, default=ENTRADA)
    p.add_argument("--salida", type=Path, default=SALIDA)
    p.add_argument("--desde", type=int, default=2020)
    p.add_argument("--hasta", type=int, default=2025)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    filas, resumen = agregar(leer_ods(a.entrada), a.desde, a.hasta)
    a.salida.mkdir(parents=True, exist_ok=True)
    destino = a.salida / f"poblacion_localidad_{a.desde}_{a.hasta}.csv"
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    resumen = {"entrada": a.entrada.as_posix(), "sha256_entrada": sha256(a.entrada), **resumen,
               "salida": destino.as_posix()}
    (a.salida / "resumen_poblacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log.info("%s filas -> %s", len(filas), destino)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
