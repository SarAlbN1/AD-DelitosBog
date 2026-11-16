#!/usr/bin/env python3
"""Pipeline de preprocesamiento de la segunda entrega (#30).

Va de los archivos crudos a los conjuntos listos para el análisis exploratorio y el modelado, y
deja el rastro de cuántas filas entran y salen de cada paso.

Qué produce, en ``data/processed/`` (ignorado por Git):

* ``serie_objetivo_diaria.csv`` — la variable objetivo: víctimas de hurto a personas registradas
  por día en Bogotá. Se construye con ``scripts/serie_objetivo_policia.py``, que se reutiliza en
  lugar de reimplementarlo.
* ``linea123_hurto_mensual_localidad.csv`` — Línea 123 por año, mes y localidad.
* ``linea123_hurto_mensual.csv`` — el mismo agregado sin desglose territorial.

Y en ``outputs/preprocesamiento/`` (versionado, porque es evidencia):

* ``conteos_por_paso.csv`` — filas antes y después de cada paso, con el motivo de cada exclusión.
* ``resumen.json`` — SHA-256 de cada archivo leído y las comprobaciones que se superaron.

Reglas que este pipeline respeta, y que vienen de la auditoría (``docs/CALIDAD_DATOS.md``):

* **El registro de la Policía no se deduplica por fila exacta.** 713.344 de sus 741.986 filas son
  duplicados exactos: dos víctimas del mismo perfil el mismo día son indistinguibles y el archivo
  no trae identificador. Un ``drop_duplicates()`` dejaría 28.642 filas.
* **El ``ID`` de Línea 123 no se usa como clave**: se repite 2.633 veces en el archivo completo.
* **Línea 123 se agrega sumando ``CANT_INCIDENTES``, no contando filas.** Sus filas son grupos
  agregados, así que contarlas pondera igual a un grupo de un incidente y a uno de quinientos.
* **«SIN LOCALIZACION» no es una localidad** y se separa del desglose territorial.
* **Las fuentes no se suman entre sí**: cada una queda en su propio archivo.

Uso::

    python scripts/preprocesamiento.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sys
from pathlib import Path

import pandas as pd

log = logging.getLogger("preprocesamiento")

#: Valores de LOCALIDAD que no son una localidad.
NO_LOCALIDAD = {"SIN LOCALIZACION", "-", ""}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class Conteos:
    """Acumula el rastro de filas por paso, que es la evidencia de que nada se perdió en silencio."""

    def __init__(self) -> None:
        self.filas: list[dict] = []

    def paso(self, fuente: str, paso: str, antes: int, despues: int, motivo: str = "") -> None:
        self.filas.append({"fuente": fuente, "paso": paso, "filas_antes": antes,
                           "filas_despues": despues, "excluidas": antes - despues, "motivo": motivo})
        log.info("[%s] %s: %s -> %s (%+d)", fuente, paso, f"{antes:,}", f"{despues:,}", despues - antes)

    def escribir(self, ruta: Path) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["fuente", "paso", "filas_antes", "filas_despues",
                                              "excluidas", "motivo"])
            w.writeheader()
            w.writerows(self.filas)


def serie_objetivo(entrada: Path, patron: str, chunksize: int, inicio: str, fin: str,
                   c: Conteos) -> tuple[pd.DataFrame, dict]:
    """Construye la serie objetivo reutilizando scripts/serie_objetivo_policia.py."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import serie_objetivo_policia as sop  # noqa: E402

    archivos = sorted(entrada.glob(patron))
    if not archivos:
        raise SystemExit(f"no hay archivos que coincidan con {patron!r} en {entrada}. "
                         f"Convierta los xlsx con scripts/policia_registro_a_csv.py.")

    registros, meta = sop.leer(archivos, chunksize)
    c.paso("policia_registro", "original", meta["filas_entrada"], meta["filas_entrada"],
           "todos los delitos del país")
    c.paso("policia_registro", "filtro Bogotá", meta["filas_entrada"], meta["filas_bogota"],
           "CODIGO DANE = 11001")
    c.paso("policia_registro", "filtro hurto a personas", meta["filas_bogota"], meta["filas_hurto"],
           "DELITOS contiene (05022)")

    serie, resumen = sop.construir(registros, meta, inicio, fin)
    c.paso("policia_registro", f"periodo {inicio} a {fin}", meta["filas_hurto"],
           resumen["filas_en_la_serie"],
           f"{resumen['filas_fuera_del_periodo']} fuera del periodo; el fin es {fin} porque "
           f"noviembre y diciembre de 2025 están incompletos (#86)")

    # Comprobación: no se deduplica. Si alguien añade un drop_duplicates, esto lo delata.
    if resumen["filas_en_la_serie"] != int(serie["victimas"].sum()):
        raise SystemExit("la suma de la serie no coincide con las filas filtradas")
    return serie, resumen


def linea123(ruta: Path, anio_min: int, anio_max: int, c: Conteos) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Agrega Línea 123 por año, mes y localidad, sumando CANT_INCIDENTES."""
    df = pd.read_csv(ruta, sep=";", encoding="utf-8-sig", dtype=str,
                     encoding_errors="replace", low_memory=False)
    n0 = len(df)
    c.paso("linea123", "original", n0, n0, "archivo histórico 2015-2026")

    df["anio"] = pd.to_numeric(df["ANIO"], errors="coerce")
    df["mes"] = pd.to_numeric(df["MES"], errors="coerce")
    df["incidentes"] = pd.to_numeric(df["CANT_INCIDENTES"], errors="coerce").fillna(0).astype(int)

    en_periodo = df[df["anio"].between(anio_min, anio_max)]
    c.paso("linea123", f"periodo {anio_min}-{anio_max}", n0, len(en_periodo),
           "el recurso cubre 2015-2026")

    hurto = en_periodo[en_periodo["TIPO_DETALLE"].fillna("").str.upper().str.contains("HURTO")]
    c.paso("linea123", "filtro hurto", len(en_periodo), len(hurto),
           "TIPO_DETALLE contiene HURTO; es la tipificación de la llamada, no una calificación jurídica")

    hurto = hurto.assign(localidad=hurto["LOCALIDAD"].fillna("").str.strip().str.upper())
    con_loc = hurto[~hurto["localidad"].isin(NO_LOCALIDAD)]
    c.paso("linea123", "localidad asignada", len(hurto), len(con_loc),
           f"se separan {len(hurto) - len(con_loc)} filas sin localidad: «SIN LOCALIZACION» no es una localidad")

    por_localidad = (con_loc.groupby(["anio", "mes", "localidad"], as_index=False)["incidentes"]
                     .sum().sort_values(["anio", "mes", "localidad"]))
    mensual = (hurto.groupby(["anio", "mes"], as_index=False)["incidentes"]
               .sum().sort_values(["anio", "mes"]))

    meta = {
        "archivo": ruta.as_posix(),
        "sha256": sha256(ruta),
        "filas_originales": n0,
        "filas_hurto_en_periodo": int(len(hurto)),
        "incidentes_hurto_en_periodo": int(hurto["incidentes"].sum()),
        "incidentes_con_localidad": int(con_loc["incidentes"].sum()),
        "filas_sin_localidad": int(len(hurto) - len(con_loc)),
        "localidades": sorted(por_localidad["localidad"].unique().tolist()),
        "nota_medida": ("el agregado suma CANT_INCIDENTES y no cuenta filas: las filas son grupos "
                        "agregados y contarlas cambia el ranking territorial"),
    }
    return por_localidad, mensual, meta


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--registro", type=Path, default=Path("data/raw/policia_registro/csv"))
    p.add_argument("--patron", default="delitos_registro_*.csv")
    p.add_argument("--linea123", type=Path, default=Path("data/raw/linea123.csv"))
    p.add_argument("--procesados", type=Path, default=Path("data/processed"))
    p.add_argument("--salida", type=Path, default=Path("outputs/preprocesamiento"))
    p.add_argument("--inicio", default="2020-01-01")
    p.add_argument("--fin", default="2025-10-31", help="Ver issue #86.")
    p.add_argument("--anio-min", type=int, default=2018)
    p.add_argument("--anio-max", type=int, default=2025)
    p.add_argument("--chunksize", type=int, default=200_000)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    c = Conteos()
    a.procesados.mkdir(parents=True, exist_ok=True)

    serie, resumen_serie = serie_objetivo(a.registro, a.patron, a.chunksize, a.inicio, a.fin, c)
    serie.to_csv(a.procesados / "serie_objetivo_diaria.csv", index=False, date_format="%Y-%m-%d")

    meta_123 = None
    if a.linea123.is_file():
        por_loc, mensual, meta_123 = linea123(a.linea123, a.anio_min, a.anio_max, c)
        por_loc.to_csv(a.procesados / "linea123_hurto_mensual_localidad.csv", index=False)
        mensual.to_csv(a.procesados / "linea123_hurto_mensual.csv", index=False)
    else:
        log.warning("no existe %s: se omite Línea 123", a.linea123)

    c.escribir(a.salida / "conteos_por_paso.csv")
    (a.salida / "resumen.json").write_text(json.dumps({
        "serie_objetivo": resumen_serie,
        "linea123": meta_123,
        "reglas_respetadas": [
            "el registro de la Policía no se deduplica por fila exacta",
            "el ID de Línea 123 no se usa como clave",
            "Línea 123 se agrega sumando CANT_INCIDENTES, no contando filas",
            "«SIN LOCALIZACION» se separa del desglose territorial",
            "las fuentes no se suman entre sí: cada una en su propio archivo",
        ],
    }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    log.info("serie objetivo: %s días, %s víctimas", resumen_serie["dias"],
             f"{resumen_serie['filas_en_la_serie']:,}")
    log.info("conjuntos en %s · evidencia en %s", a.procesados, a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
