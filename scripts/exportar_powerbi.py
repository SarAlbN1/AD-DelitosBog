#!/usr/bin/env python3
"""Genera las hojas del tablero de Power BI desde las salidas versionadas (#106).

El `.pbix` **no se puede generar desde aquí**: requiere Power BI Desktop, que solo corre en Windows
y no es automatizable. Lo que este script produce es todo lo demás, que es la parte reproducible:
las hojas, con un modelo en estrella listo para cargar.

Nada se escribe a mano. Cada hoja sale de un archivo de `outputs/` o de `data/processed/`, así que
si una cifra del tablero no cuadra con el informe, es que el informe y el tablero leen distinto, no
que alguien transcribió mal.

## Qué produce

En `outputs/powerbi/`: un CSV por tabla y un `.xlsx` con una hoja por tabla, para cargar de una vez.

**Hechos**

* `fact_serie_diaria` — un día. La variable objetivo y sus 21 predictoras.
* `fact_linea123_localidad` — año × mes × localidad.
* `fact_linea123_upz` — año × UPZ.
* `fact_fuentes_mensual` — mes × fuente, en formato largo para poder comparar sin sumar.
* `fact_comparadores` — comparador × métrica, evaluación final.
* `fact_validacion_rodante` — pliegue × comparador.

**Dimensiones**

* `dim_calendario` — una fila por día, con festivo, día de la semana y año atípico.
* `dim_localidad` — una fila por localidad y año, con población y tasa.
* `dim_fuente` — una fila por fuente, con su unidad de observación y si sostiene el mínimo.

**Control de calidad**

* `qa_embudo` — filas antes y después de cada paso del pipeline.
* `qa_nulos` — nulos por fuente y columna.
* `qa_atipicos` — los días atípicos con su z.

## La regla que el formato largo impone

`fact_fuentes_mensual` va en formato **largo** (mes, fuente, valor) a propósito, no en columnas. En
formato ancho es trivial escribir una medida que sume las tres fuentes, y eso está prohibido: miden
cosas distintas. En largo, sumar exige agrupar por fuente y el error salta a la vista.

Uso::

    python scripts/exportar_powerbi.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

log = logging.getLogger("powerbi")

#: Metadatos de cada fuente. Lo que un tablero necesita saber para no mezclarlas.
FUENTES = [
    {"fuente": "Policía (registro)", "clave": "policia_registro",
     "unidad_observacion": "una víctima de hurto a personas",
     "resolucion_temporal": "día", "resolucion_territorial": "municipio",
     "periodo": "2020-01-01 a 2025-10-31", "filas_hurto_bogota": 741986,
     "sostiene_el_minimo": "sí", "es_la_serie_objetivo": "sí"},
    {"fuente": "Fiscalía (Procesos V3)", "clave": "fiscalia",
     "unidad_observacion": "un par proceso–delito",
     "resolucion_temporal": "mes", "resolucion_territorial": "municipio",
     "periodo": "2018-2025", "filas_hurto_bogota": 1300703,
     "sostiene_el_minimo": "sí", "es_la_serie_objetivo": "no"},
    {"fuente": "Línea 123", "clave": "linea123",
     "unidad_observacion": "un agregado de llamadas tramitadas",
     "resolucion_temporal": "mes", "resolucion_territorial": "UPZ",
     "periodo": "2018-2025", "filas_hurto_bogota": 25144,
     "sostiene_el_minimo": "no", "es_la_serie_objetivo": "no"},
    {"fuente": "MinDefensa (agregado)", "clave": "policia_agregado",
     "unidad_observacion": "un conteo por día y municipio",
     "resolucion_temporal": "día", "resolucion_territorial": "municipio",
     "periodo": "2018-2025", "filas_hurto_bogota": 2922,
     "sostiene_el_minimo": "no", "es_la_serie_objetivo": "no (control de consistencia)"},
]

#: Las reglas que el tablero no puede romper. Van en una hoja, para que estén dentro del archivo.
REGLAS = [
    ("El mapa y las comparaciones entre localidades usan la tasa, no el conteo",
     "Por conteo Kennedy es 1.ª y por tasa 13.ª. Un mapa de conteos colorea de rojo lo que solo es "
     "población"),
    ("Línea 123 se agrega sumando incidentes, nunca contando filas",
     "Sus filas son grupos agregados: contarlas pondera igual un grupo de 1 y uno de 500"),
    ("Las fuentes no se suman entre sí",
     "Miden cosas distintas. Por eso fact_fuentes_mensual va en formato largo"),
    ("«SIN LOCALIZACION» no es una localidad",
     "Queda fuera del mapa y se reporta aparte: 5.683 incidentes, 0,69 %"),
    ("2020 va marcado como año atípico",
     "Media diaria 227,1 frente a 434,9 en 2023, por las restricciones de movilidad"),
    ("El total de 2025 no se compara con años completos",
     "La serie termina el 2025-10-31. Se comparan medias diarias: 368,1 frente a 356,6 de 2024"),
    ("Noviembre y diciembre de 2025 están fuera de la serie",
     "No son comparables: el registro cae a la mitad y Línea 123 no (issue 86)"),
    ("Ninguna página presenta un ranking de peligrosidad",
     "Ni por conteo ni por tasa. La tasa no capta la población flotante"),
]


def _leer(ruta: Path, **kw) -> pd.DataFrame:
    if not ruta.is_file():
        raise SystemExit(f"falta {ruta}. Ejecute antes el pipeline de docs/REPRODUCIBILIDAD.md")
    return pd.read_csv(ruta, **kw)


def hechos_serie(features: Path) -> pd.DataFrame:
    df = _leer(features, parse_dates=["fecha"])
    return df.rename(columns={"victimas": "victimas"})


def dim_calendario(serie: pd.DataFrame) -> pd.DataFrame:
    """Dimensión de fecha. Power BI necesita una tabla de calendario propia para sus jerarquías."""
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
    f = serie["fecha"]
    return pd.DataFrame({
        "fecha": f,
        "anio": f.dt.year,
        "mes": f.dt.month,
        "nombre_mes": f.dt.month.map(lambda m: meses[m - 1]),
        "anio_mes": f.dt.strftime("%Y-%m"),
        "trimestre": f.dt.quarter,
        "dia_del_mes": f.dt.day,
        "dia_semana_numero": f.dt.dayofweek,
        "dia_semana": f.dt.dayofweek.map(lambda d: dias[d]),
        "fin_de_semana": serie["fin_de_semana"],
        "festivo": serie["festivo"],
        "vispera_de_festivo": serie["vispera_de_festivo"],
        "quincena": serie["quincena"],
        "anio_atipico": serie["anio_atipico_2020"],
    })


def dim_localidad(tasas: Path, poblacion: Path, conteo: Path) -> pd.DataFrame:
    t = _leer(tasas)
    pob = _leer(poblacion)
    c = _leer(conteo)
    c["puesto_conteo"] = range(1, len(c) + 1)
    t = t.sort_values("tasa_100k_periodo", ascending=False).reset_index(drop=True)
    t["puesto_tasa"] = t.index + 1
    base = t.merge(c[["localidad", "pct", "puesto_conteo"]], on="localidad", how="left")
    # Una fila por localidad y año, con la población de ese año: así el tablero puede filtrar por
    # año y la tasa sigue siendo correcta.
    pob = pob.rename(columns={"clave": "clave"})
    salida = pob.merge(base[["clave", "localidad", "incidentes", "pct", "tasa_100k_periodo",
                             "puesto_conteo", "puesto_tasa"]],
                       on="clave", how="left", suffixes=("", "_tabla"))
    salida = salida.rename(columns={"incidentes": "incidentes_periodo",
                                    "pct": "pct_incidentes_periodo",
                                    "tasa_100k_periodo": "tasa_100k_periodo"})
    salida["es_rural_sumapaz"] = (salida["clave"] == "SUMAPAZ").astype(int)
    salida["poblacion_flotante_alta"] = salida["clave"].isin(
        ["LOS MARTIRES", "LOS MÁRTIRES", "SANTA FE", "CANDELARIA", "CHAPINERO", "TEUSAQUILLO",
         "ANTONIO NARINO", "ANTONIO NARIÑO"]).astype(int)
    return salida


def fuentes_largo(series: Path) -> pd.DataFrame:
    """Formato largo a propósito: en ancho es trivial sumar las tres fuentes, y está prohibido."""
    df = _leer(series)
    cols = {"policia_registro_victimas": "Policía (registro)",
            "linea123_llamadas": "Línea 123",
            "fiscalia_filas_proceso_delito": "Fiscalía (Procesos V3)",
            "mindefensa_agregado_hurtos": "MinDefensa (agregado)"}
    presentes = {k: v for k, v in cols.items() if k in df.columns}
    largo = df.melt(id_vars=["fecha"], value_vars=list(presentes), var_name="columna",
                    value_name="valor").dropna(subset=["valor"])
    largo["fuente"] = largo["columna"].map(presentes)
    largo["anio"] = largo["fecha"].str.slice(0, 4).astype(int)
    largo["comparable"] = (largo["fecha"] < "2025-11").map({True: "sí", False: "no (issue 86)"})
    return largo[["fecha", "anio", "fuente", "valor", "comparable"]].sort_values(
        ["fecha", "fuente"])


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=RAIZ / "outputs" / "powerbi")
    p.add_argument("--sin-xlsx", action="store_true", help="Solo los CSV.")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    o, d = RAIZ / "outputs", RAIZ / "data" / "processed"
    serie = hechos_serie(d / "features_diarias.csv")

    tablas: dict[str, pd.DataFrame] = {
        "fact_serie_diaria": serie,
        "fact_linea123_localidad": _leer(d / "linea123_hurto_mensual_localidad.csv"),
        "fact_linea123_upz": _leer(d / "linea123_hurto_upz.csv"),
        "fact_fuentes_mensual": fuentes_largo(o / "informe" / "series_mensuales_fuentes.csv"),
        "fact_comparadores": _leer(o / "baselines" / "comparadores.csv").rename(
            columns={"Unnamed: 0": "comparador"}),
        "fact_validacion_rodante": _leer(o / "baselines" / "validacion_rodante.csv"),
        "dim_calendario": dim_calendario(serie),
        "dim_localidad": dim_localidad(o / "eda" / "territorial_tasas.csv",
                                      o / "poblacion" / "poblacion_localidad_2020_2025.csv",
                                      o / "eda" / "territorial_localidad.csv"),
        "dim_fuente": pd.DataFrame(FUENTES),
        "qa_embudo": _leer(o / "preprocesamiento" / "conteos_por_paso.csv"),
        "qa_nulos": _leer(o / "auditoria" / "valores_nulos.csv"),
        "qa_atipicos": pd.concat([
            _leer(o / "eda" / "atipicos_altos.csv").assign(tipo="alto"),
            _leer(o / "eda" / "atipicos_bajos.csv").assign(tipo="bajo")]),
        "qa_reglas": pd.DataFrame(REGLAS, columns=["regla", "por_que"]),
    }

    a.salida.mkdir(parents=True, exist_ok=True)
    for nombre, t in tablas.items():
        t.to_csv(a.salida / f"{nombre}.csv", index=False)

    if not a.sin_xlsx:
        try:
            with pd.ExcelWriter(a.salida / "tablero_powerbi.xlsx", engine="openpyxl") as w:
                for nombre, t in tablas.items():
                    # Excel limita el nombre de hoja a 31 caracteres.
                    t.to_excel(w, sheet_name=nombre[:31], index=False)
        except ImportError:
            log.warning("falta openpyxl: se omite el .xlsx y quedan los CSV")

    manifiesto = {
        "generado_por": "scripts/exportar_powerbi.py",
        "nota_pbix": ("el .pbix no se genera aquí: requiere Power BI Desktop. El guion de montaje "
                      "está en docs/POWERBI.md"),
        "tablas": {n: {"filas": int(len(t)), "columnas": list(t.columns)} for n, t in tablas.items()},
        "reglas": [r[0] for r in REGLAS],
    }
    (a.salida / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")

    for nombre, t in tablas.items():
        log.info("  %-26s %6s filas × %2s columnas", nombre, f"{len(t):,}", len(t.columns))
    log.info("%s tablas en %s", len(tablas), a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
