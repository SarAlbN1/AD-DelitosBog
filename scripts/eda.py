#!/usr/bin/env python3
"""Análisis exploratorio de la sección 6 (#34).

Tres bloques, sobre los conjuntos que produce ``scripts/preprocesamiento.py``:

1. **Temporal**: tendencia anual, perfil por día de la semana, estacionalidad mensual y efecto de
   los festivos sobre la serie objetivo.
2. **Territorial**: distribución por localidad de Línea 123, que es la única fuente con resolución
   dentro de la ciudad.
3. **Entre fuentes**: relación de las tres series en mes × Bogotá, la única resolución común.

Reglas que vienen de la auditoría y que aquí se respetan:

* Línea 123 se mide **sumando** ``CANT_INCIDENTES``, nunca contando filas.
* «SIN LOCALIZACION» no es una localidad: se separa y se reporta su peso.
* Las fuentes **no se suman** entre sí. Se comparan sus series, no sus totales.
* **2020 no es un año típico**: el nivel deprimido coincide con las restricciones de movilidad y se
  señala en cada salida donde aparece.
* La serie termina el 2025-10-31 (#86), así que 2025 está truncado y sus totales anuales no son
  comparables con los de los años completos.

Las tasas por población **no se calculan** mientras no haya una fuente de población por localidad.
Cuando exista, se pasa con ``--poblacion``, un CSV con columnas ``localidad`` y ``habitantes``, y el
script añade la tasa por cada 100.000. Comparar conteos absolutos entre localidades de tamaño muy
distinto induce una lectura estigmatizante, así que mientras tanto se dice explícitamente en la
salida.

Uso::

    python scripts/eda.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("eda")

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def cargar_serie(ruta: Path) -> pd.Series:
    s = pd.read_csv(ruta, parse_dates=["fecha"]).set_index("fecha")["victimas"].astype(float)
    return s.sort_index()


def bloque_temporal(s: pd.Series, festivos: set) -> dict:
    anual = s.groupby(s.index.year).agg(["sum", "mean", "size"])
    anual.columns = ["victimas", "media_diaria", "dias"]
    anual["anio_completo"] = anual["dias"] >= 365

    por_dia = s.groupby(s.index.dayofweek).mean()
    por_dia.index = [DIAS[i] for i in por_dia.index]
    por_mes = s.groupby(s.index.month).mean()
    por_mes.index = [MESES[i - 1] for i in por_mes.index]

    es_festivo = pd.Series([d.date() in festivos for d in s.index], index=s.index)
    # Un festivo cae casi siempre en lunes, así que compararlo con «todos los días» mezcla el
    # efecto del festivo con el del día de la semana. Se compara contra los lunes laborables.
    lunes = s.index.dayofweek == 0
    festivo_lunes = s[es_festivo & lunes]
    laborable_lunes = s[~es_festivo & lunes]

    return {
        "anual": anual,
        "por_dia_semana": por_dia,
        "por_mes": por_mes,
        "festivos": {
            "media_en_festivo": round(float(s[es_festivo].mean()), 1),
            "media_en_no_festivo": round(float(s[~es_festivo].mean()), 1),
            "n_festivos": int(es_festivo.sum()),
            "media_lunes_festivo": round(float(festivo_lunes.mean()), 1),
            "media_lunes_laborable": round(float(laborable_lunes.mean()), 1),
            "n_lunes_festivo": int(len(festivo_lunes)),
            "diferencia_lunes_pct": round(
                100 * (festivo_lunes.mean() / laborable_lunes.mean() - 1), 1),
        },
    }


def bloque_territorial(ruta: Path, ruta_mensual: Path) -> dict | None:
    if not ruta.is_file():
        log.warning("no existe %s: se omite el bloque territorial", ruta)
        return None
    por_loc = pd.read_csv(ruta)
    total_con_loc = int(por_loc["incidentes"].sum())
    resumen = (por_loc.groupby("localidad", as_index=False)["incidentes"].sum()
               .sort_values("incidentes", ascending=False))
    resumen["pct"] = (100 * resumen["incidentes"] / total_con_loc).round(2)

    sin_loc = None
    if ruta_mensual.is_file():
        total_todo = int(pd.read_csv(ruta_mensual)["incidentes"].sum())
        sin_loc = {"incidentes_sin_localidad": total_todo - total_con_loc,
                   "pct_sin_localidad": round(100 * (total_todo - total_con_loc) / total_todo, 2)}

    return {"resumen": resumen, "total_con_localidad": total_con_loc, "sin_localidad": sin_loc}


def bloque_entre_fuentes(ruta: Path) -> dict | None:
    if not ruta.is_file():
        log.warning("no existe %s: se omite la comparación entre fuentes", ruta)
        return None
    df = pd.read_csv(ruta)
    df["fecha"] = pd.PeriodIndex(df["fecha"], freq="M").to_timestamp()
    cols = {"policia_registro_victimas": "Policía (víctimas)",
            "linea123_llamadas": "Línea 123 (llamadas)",
            "fiscalia_filas_proceso_delito": "Fiscalía (proceso–delito)"}
    df = df.set_index("fecha")[list(cols)].rename(columns=cols).dropna()
    # Los dos últimos meses de 2025 no son comparables (#86): se excluyen de la correlación.
    df = df[df.index < "2025-11-01"]
    return {
        "periodo": [df.index.min().strftime("%Y-%m"), df.index.max().strftime("%Y-%m")],
        "meses": int(len(df)),
        "correlacion_pearson": df.corr().round(3),
        "correlacion_spearman": df.corr(method="spearman").round(3),
        "series": df,
    }


def figuras(temporal: dict, territorial: dict | None, fuentes: dict | None, carpeta: Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    carpeta.mkdir(parents=True, exist_ok=True)
    hechas = []

    def guardar(fig, nombre):
        for ext in ("png", "pdf"):
            fig.savefig(carpeta / f"{nombre}.{ext}", dpi=150, bbox_inches="tight")
        plt.close(fig)
        hechas.append(nombre)

    fig, ax = plt.subplots(figsize=(7, 3.2))
    d = temporal["por_dia_semana"]
    ax.bar(d.index, d.to_numpy(), color="#4C72B0")
    ax.set(ylabel="víctimas por día (media)", title="Perfil por día de la semana")
    ax.axhline(d.mean(), color="#C44E52", ls="--", lw=1, label=f"media {d.mean():.0f}")
    ax.legend()
    guardar(fig, "eda_dia_semana")

    fig, ax = plt.subplots(figsize=(7, 3.2))
    m = temporal["por_mes"]
    ax.plot(m.index, m.to_numpy(), marker="o", color="#4C72B0")
    ax.set(ylabel="víctimas por día (media)", title="Estacionalidad mensual")
    ax.grid(alpha=.3)
    guardar(fig, "eda_estacionalidad_mensual")

    if territorial is not None:
        fig, ax = plt.subplots(figsize=(7, 5))
        r = territorial["resumen"].head(15).iloc[::-1]
        ax.barh(r["localidad"].str.title(), r["incidentes"], color="#55A868")
        ax.set(xlabel="incidentes de hurto (suma de CANT_INCIDENTES)",
               title="Línea 123 · 15 localidades con más incidentes")
        guardar(fig, "eda_localidad")

    if fuentes is not None:
        fig, ax = plt.subplots(figsize=(8, 3.4))
        for col in fuentes["series"].columns:
            serie = fuentes["series"][col]
            ax.plot(serie.index, serie / serie.mean(), label=col, lw=1.2)
        ax.set(ylabel="valor / media de la serie", title="Las tres fuentes, normalizadas")
        ax.legend(fontsize=8)
        ax.grid(alpha=.3)
        guardar(fig, "eda_fuentes_normalizadas")

    return hechas


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--serie", type=Path, default=Path("data/processed/serie_objetivo_diaria.csv"))
    p.add_argument("--localidad", type=Path,
                   default=Path("data/processed/linea123_hurto_mensual_localidad.csv"))
    p.add_argument("--linea123-mensual", type=Path,
                   default=Path("data/processed/linea123_hurto_mensual.csv"))
    p.add_argument("--fuentes", type=Path, default=Path("outputs/informe/series_mensuales_fuentes.csv"))
    p.add_argument("--poblacion", type=Path, default=None,
                   help="CSV con localidad,habitantes para calcular tasas por 100.000.")
    p.add_argument("--salida", type=Path, default=Path("outputs/eda"))
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not a.serie.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", a.serie)
        return 2

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import features as ft

    s = cargar_serie(a.serie)
    fs = ft.calendario_festivos(s.index.min(), s.index.max())

    temporal = bloque_temporal(s, fs)
    territorial = bloque_territorial(a.localidad, a.linea123_mensual)
    fuentes = bloque_entre_fuentes(a.fuentes)

    a.salida.mkdir(parents=True, exist_ok=True)
    temporal["anual"].to_csv(a.salida / "temporal_anual.csv")
    temporal["por_dia_semana"].rename("media").to_csv(a.salida / "temporal_dia_semana.csv")
    temporal["por_mes"].rename("media").to_csv(a.salida / "temporal_mes.csv")
    if territorial:
        territorial["resumen"].to_csv(a.salida / "territorial_localidad.csv", index=False)
    if fuentes:
        fuentes["correlacion_pearson"].to_csv(a.salida / "fuentes_correlacion_pearson.csv")
        fuentes["correlacion_spearman"].to_csv(a.salida / "fuentes_correlacion_spearman.csv")

    tasas = None
    if a.poblacion and a.poblacion.is_file() and territorial:
        pob = pd.read_csv(a.poblacion)
        r = territorial["resumen"].merge(pob, on="localidad", how="left")
        r["tasa_100k"] = (100_000 * r["incidentes"] / r["habitantes"]).round(1)
        r.to_csv(a.salida / "territorial_tasas.csv", index=False)
        tasas = "calculadas"
    elif territorial:
        tasas = ("no calculadas: falta una fuente de población por localidad. Los conteos absolutos "
                 "no se deben leer como riesgo: las localidades más pobladas acumulan más incidentes")

    hechas = figuras(temporal, territorial, fuentes, a.salida / "figuras")

    doc = {
        "serie": {"periodo": [s.index.min().date().isoformat(), s.index.max().date().isoformat()],
                  "dias": int(len(s)), "media": round(float(s.mean()), 1)},
        "temporal": {
            "anual": json.loads(temporal["anual"].to_json(orient="index")),
            "por_dia_semana": {k: round(float(v), 1) for k, v in temporal["por_dia_semana"].items()},
            "por_mes": {k: round(float(v), 1) for k, v in temporal["por_mes"].items()},
            "festivos": temporal["festivos"],
            "nota_2020": "2020 no es comparable: el nivel está deprimido por las restricciones de movilidad",
            "nota_2025": "2025 está truncado el 2025-10-31 (#86): su total anual no es comparable",
        },
        "territorial": None if not territorial else {
            "total_con_localidad": territorial["total_con_localidad"],
            "sin_localidad": territorial["sin_localidad"],
            "top5": territorial["resumen"].head(5).to_dict("records"),
            "tasas_por_poblacion": tasas,
        },
        "entre_fuentes": None if not fuentes else {
            "periodo": fuentes["periodo"], "meses": fuentes["meses"],
            "pearson": json.loads(fuentes["correlacion_pearson"].to_json()),
            "spearman": json.loads(fuentes["correlacion_spearman"].to_json()),
            "nota": "resolución mes × Bogotá, la única común; las fuentes no se suman entre sí",
        },
        "figuras": hechas,
    }
    (a.salida / "resumen_eda.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                                               encoding="utf-8")

    f = temporal["festivos"]
    log.info("serie: %s días, media %.1f", len(s), s.mean())
    log.info("día de más tráfico: %s (%.0f) · de menos: %s (%.0f)",
             temporal["por_dia_semana"].idxmax(), temporal["por_dia_semana"].max(),
             temporal["por_dia_semana"].idxmin(), temporal["por_dia_semana"].min())
    log.info("lunes festivo %.1f vs lunes laborable %.1f (%+.1f %%)",
             f["media_lunes_festivo"], f["media_lunes_laborable"], f["diferencia_lunes_pct"])
    if fuentes:
        log.info("correlación Policía–Línea 123 (mensual): %.3f",
                 fuentes["correlacion_pearson"].iloc[0, 1])
    log.info("figuras: %s · salidas en %s", ", ".join(hechas), a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
