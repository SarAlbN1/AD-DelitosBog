#!/usr/bin/env python3
"""Convierte los archivos anuales de la Policía Nacional «a nivel de registro» a CSV.

Por qué existe: `scripts/auditoria_datasets.py` lee Excel con `pandas.read_excel`, que carga el
archivo completo en memoria antes de trocearlo, así que `--chunksize` no limita la memoria en esa
rama. Cada archivo anual trae del orden de 800.000 filas por 11 columnas, lo que puede pedir varios
gigabytes. Este conversor lee con `openpyxl` en modo `read_only`, fila por fila y con memoria
constante, y deja un CSV que la auditoría sí procesa por bloques.

Qué hace, además de convertir:

- Salta el membrete. El encabezado de estos archivos está en la fila 12 (`--fila-encabezado 12`).
- Descarta el pie del archivo con el mismo criterio que `recortar_pie()` de la auditoría: el bloque
  final de filas con, a lo sumo, una celda no vacía (notas, «Fecha de entrega», filas en blanco).
  No lo hace en silencio: cuenta las filas descartadas y guarda su texto.
- No filtra por municipio ni por delito. Ese recorte lo hace el embudo de la auditoría, que así
  queda documentado en `embudo_filtros.csv`.
- Registra el SHA-256 del xlsx de origen y del CSV producido, para poder demostrar que el CSV
  auditado proviene del archivo descargado.

Uso:

    python scripts/policia_registro_a_csv.py \
        --entrada data/raw/policia_registro \
        --salida data/raw/policia_registro/csv

El manifiesto de la conversión queda en `<salida>/conversion.json`.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import logging
import sys
from pathlib import Path

log = logging.getLogger("policia_registro")

#: Fila del encabezado. Varía entre años: 12 en 2020, 2023, 2024 y 2025; 13 en 2021 y 2022. Por eso
#: el valor por defecto es detectarla, y no un número fijo.
FILA_ENCABEZADO_POR_DEFECTO = "auto"

#: Filas que se inspeccionan al detectar el encabezado.
FILAS_A_INSPECCIONAR = 40

#: Celdas no vacías mínimas para aceptar una fila como encabezado. El membrete trae una sola celda.
MIN_CELDAS_ENCABEZADO = 5

#: Mínimo de celdas no vacías para considerar que una fila trae datos y no es una nota del pie.
MIN_CELDAS_CON_DATOS = 2


class ErrorConversion(Exception):
    """Error de entrada o de lectura, con un mensaje explicativo para quien ejecuta el script."""


def sha256_archivo(path: Path, bloque: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(bloque), b""):
            h.update(b)
    return h.hexdigest()


def _texto(valor) -> str:
    """Normaliza una celda a texto. Las fechas se escriben en ISO para que el CSV sea inequívoco."""
    if valor is None:
        return ""
    if isinstance(valor, dt.datetime):
        return valor.date().isoformat() if valor.time() == dt.time(0, 0) else valor.isoformat(sep=" ")
    if isinstance(valor, dt.date):
        return valor.isoformat()
    return str(valor).strip()


def _celdas_con_datos(fila: list[str]) -> int:
    return sum(1 for v in fila if v != "")


def _recortar_cola_vacia(fila: list[str]) -> list[str]:
    while fila and fila[-1] == "":
        fila.pop()
    return fila


def detectar_fila_encabezado(ws, limite: int = FILAS_A_INSPECCIONAR) -> tuple[int, list[str]]:
    """Devuelve (fila 1-indexada, cabecera) de la primera fila que parece un encabezado.

    La posición cambia entre años, así que buscarla es más fiable que fijarla en el manifiesto.
    Se acepta la primera fila con al menos `MIN_CELDAS_ENCABEZADO` celdas no vacías y sin valores
    numéricos, que es lo que distingue al encabezado de una fila de datos.
    """
    for i, cruda in enumerate(ws.iter_rows(min_row=1, max_row=limite, values_only=True), start=1):
        cabecera = _recortar_cola_vacia([_texto(v) for v in cruda])
        if _celdas_con_datos(cabecera) < MIN_CELDAS_ENCABEZADO:
            continue
        if any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in cruda):
            continue
        return i, cabecera
    raise ErrorConversion(
        f"no se encontró el encabezado en las primeras {limite} filas. "
        f"Indíquelo con --fila-encabezado <n>.")


def convertir(origen: Path, destino: Path, fila_encabezado=FILA_ENCABEZADO_POR_DEFECTO) -> dict:
    """Convierte un xlsx a CSV y devuelve el registro de la conversión."""
    try:
        from openpyxl import load_workbook
    except ImportError as e:  # pragma: no cover - depende del entorno
        raise ErrorConversion(f"falta openpyxl ({e}). Instálelo con 'pip install openpyxl'.") from e

    log.info("%s: leyendo", origen.name)
    wb = load_workbook(origen, read_only=True, data_only=True)
    try:
        ws = wb[wb.sheetnames[0]]

        if fila_encabezado in (None, "auto"):
            fila_encabezado, cabecera = detectar_fila_encabezado(ws)
            log.info("%s: encabezado detectado en la fila %s", origen.name, fila_encabezado)
            detectado = True
        else:
            fila_encabezado = int(fila_encabezado)
            detectado = False
            cabecera = None

        filas = ws.iter_rows(min_row=fila_encabezado, values_only=True)
        try:
            cabecera_cruda = next(filas)
        except StopIteration:
            raise ErrorConversion(
                f"{origen.name}: no hay fila {fila_encabezado}. Revise --fila-encabezado.") from None

        if cabecera is None:
            cabecera = _recortar_cola_vacia([_texto(v) for v in cabecera_cruda])
        if _celdas_con_datos(cabecera) < MIN_CELDAS_ENCABEZADO:
            raise ErrorConversion(
                f"{origen.name}: la fila {fila_encabezado} no parece un encabezado: {cabecera!r}. "
                f"Revise --fila-encabezado.")
        n_col = len(cabecera)

        destino.parent.mkdir(parents=True, exist_ok=True)
        escritas = 0
        vacias_intermedias = 0
        # Las filas poco densas se retienen: solo se escriben si después aparece otra fila con datos.
        # Lo que quede retenido al final del archivo es el pie y se descarta.
        pendientes: list[list[str]] = []

        with open(destino, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(cabecera)
            for cruda in filas:
                fila = [_texto(v) for v in cruda][:n_col]
                fila += [""] * (n_col - len(fila))
                if _celdas_con_datos(fila) >= MIN_CELDAS_CON_DATOS:
                    for retenida in pendientes:
                        w.writerow(retenida)
                        escritas += 1
                        vacias_intermedias += 1
                    pendientes.clear()
                    w.writerow(fila)
                    escritas += 1
                else:
                    pendientes.append(fila)
    finally:
        wb.close()

    texto_pie = [" | ".join(v for v in fila if v) for fila in pendientes]
    texto_pie = [t for t in texto_pie if t]
    registro = {
        "origen": origen.name,
        "origen_bytes": origen.stat().st_size,
        "origen_sha256": sha256_archivo(origen),
        "csv": destino.name,
        "csv_bytes": destino.stat().st_size,
        "csv_sha256": sha256_archivo(destino),
        "fila_encabezado": fila_encabezado,
        "fila_encabezado_detectada": detectado,
        "columnas": cabecera,
        "filas_escritas": escritas,
        "filas_pie_descartadas": len(pendientes),
        "pie_ejemplo": texto_pie[:3],
        "filas_poco_densas_conservadas": vacias_intermedias,
    }
    log.info("%s: %s filas escritas, %s de pie descartadas", origen.name, escritas, len(pendientes))
    if texto_pie:
        log.info("%s: pie -> %s", origen.name, "; ".join(texto_pie[:2])[:200])
    return registro


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convierte los Excel de Policía «a nivel de registro» a CSV, en streaming.")
    p.add_argument("--entrada", type=Path, default=Path("data/raw/policia_registro"),
                   help="Carpeta con los .xlsx descargados (por defecto data/raw/policia_registro).")
    p.add_argument("--salida", type=Path, default=None,
                   help="Carpeta de los CSV (por defecto <entrada>/csv).")
    p.add_argument("--patron", default="*.xlsx", help="Patrón de archivos a convertir.")
    p.add_argument("--fila-encabezado", default=FILA_ENCABEZADO_POR_DEFECTO,
                   help="Fila 1-indexada del encabezado, o 'auto' para detectarla (por defecto). "
                        "La posición cambia entre años: 12 en 2020, 2023, 2024 y 2025; 13 en 2021 y 2022.")
    p.add_argument("-v", "--verbose", action="store_true", help="Más detalle en el registro.")
    return p


def main(argv=None) -> int:
    args = construir_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(message)s")

    entrada: Path = args.entrada
    salida: Path = args.salida or (entrada / "csv")
    if not entrada.is_dir():
        log.error("no existe la carpeta de entrada: %s", entrada)
        return 2

    archivos = sorted(p for p in entrada.glob(args.patron) if not p.name.startswith("~$"))
    if not archivos:
        log.error("no hay archivos que coincidan con %r en %s", args.patron, entrada)
        return 2

    registros, fallos = [], 0
    for origen in archivos:
        destino = salida / (origen.stem + ".csv")
        try:
            registros.append(convertir(origen, destino, args.fila_encabezado))
        except ErrorConversion as e:
            log.error("%s", e)
            fallos += 1

    if registros:
        salida.mkdir(parents=True, exist_ok=True)
        manifiesto = {
            "generado": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "script": Path(__file__).name,
            "python": sys.version.split()[0],
            "fila_encabezado": args.fila_encabezado,
            "min_celdas_encabezado": MIN_CELDAS_ENCABEZADO,
            "min_celdas_con_datos": MIN_CELDAS_CON_DATOS,
            "archivos": registros,
            "filas_escritas_total": sum(r["filas_escritas"] for r in registros),
            "filas_pie_descartadas_total": sum(r["filas_pie_descartadas"] for r in registros),
        }
        (salida / "conversion.json").write_text(
            json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("manifiesto de conversión en %s", salida / "conversion.json")
        log.info("total: %s filas escritas, %s de pie descartadas",
                 manifiesto["filas_escritas_total"], manifiesto["filas_pie_descartadas_total"])

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
