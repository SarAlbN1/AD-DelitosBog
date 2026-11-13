"""Figuras y tablas de la sección 4 del informe de la primera entrega.

Parte de salidas ya auditadas y no recalcula los filtros:

* ``outputs/auditoria/cobertura_temporal.csv``: Línea 123 y Fiscalía por año y mes.
* ``outputs/auditoria_policia/cobertura_temporal.csv``: registro de Policía (2020–2025) y
  agregado de MinDefensa (2018–2025) por año y mes.

Solo lee un archivo crudo, el de Línea 123, para sumar ``CANT_INCIDENTES`` por localidad, porque
la figura de localidades de la auditoría cuenta filas y cada fila agrupa varias llamadas. El filtro
es el del manifiesto: ``TIPO_DETALLE`` contiene «HURTO», años 2020–2025.

Salidas en ``--salida`` (por defecto ``outputs/informe``):

* ``series_mensuales_fuentes.csv`` y ``figuras/series_mensuales_fuentes.{png,pdf}``: una serie
  por fuente, cada una en su propia unidad, sin sumarlas.
* ``linea123_localidad_2020_2025.csv`` y ``figuras/linea123_localidad.{png,pdf}``: llamadas de
  hurto por localidad, 2020–2025.

Uso::

    python scripts/figuras_informe.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

LINEA123 = ("data/raw/linea123/datos-abiertllamadastramitadas-c4-bogota_"
            "numerounicodeseguridadyemergencias-nuse_linea-123os-nus.csv")


def series_mensuales(auditoria: Path, auditoria_policia: Path) -> pd.DataFrame:
    a = pd.read_csv(auditoria / "cobertura_temporal.csv")
    p = pd.read_csv(auditoria_policia / "cobertura_temporal.csv")
    d = pd.concat([a, p], ignore_index=True)
    d = d[(d["etapa"] == "final") & (d["anio"] > 0) & (d["mes"] > 0)].copy()
    d["fecha"] = pd.to_datetime(dict(year=d["anio"].astype(int), month=d["mes"].astype(int), day=1))
    # Medida de cada fuente: filas en el registro de Policía y en Fiscalía; suma de la cantidad en
    # Línea 123 (llamadas) y en el agregado de MinDefensa (hurtos registrados).
    medida = {"policia_registro": "filas", "fiscalia": "filas",
              "linea123": "suma_cantidad", "policia_agregado": "suma_cantidad"}
    d["valor"] = [r[medida[r["fuente"]]] for _, r in d.iterrows()]
    t = d.pivot_table(index="fecha", columns="fuente", values="valor", aggfunc="sum")
    return t.rename(columns={"policia_registro": "policia_registro_victimas",
                             "policia_agregado": "mindefensa_agregado_hurtos",
                             "fiscalia": "fiscalia_filas_proceso_delito",
                             "linea123": "linea123_llamadas"}).sort_index()


def localidades(ruta: Path) -> pd.DataFrame:
    d = pd.read_csv(ruta, sep=";", dtype=str, encoding="utf-8",
                    usecols=["ANIO", "TIPO_DETALLE", "LOCALIDAD", "CANT_INCIDENTES"])
    d = d[d["TIPO_DETALLE"].str.contains("HURTO", na=False)]
    d = d[pd.to_numeric(d["ANIO"], errors="coerce").between(2020, 2025)]
    d["llamadas"] = pd.to_numeric(d["CANT_INCIDENTES"], errors="coerce")
    t = d.groupby("LOCALIDAD").agg(filas=("llamadas", "size"), llamadas=("llamadas", "sum"))
    t = t.sort_values("llamadas", ascending=False)
    t["pct_llamadas"] = (100 * t["llamadas"] / t["llamadas"].sum()).round(2)
    return t.reset_index().rename(columns={"LOCALIDAD": "localidad"})


def figuras(series: pd.DataFrame, loc: pd.DataFrame | None, carpeta: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    carpeta.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"savefig.dpi": 200, "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})

    paneles = [
        ("policia_registro_victimas", "Policía: víctimas registradas", "#1f4e79"),
        ("fiscalia_filas_proceso_delito", "Fiscalía: filas proceso–delito", "#7a5195"),
        ("linea123_llamadas", "Línea 123: llamadas de hurto", "#c0504d"),
    ]
    fig, ejes = plt.subplots(3, 1, figsize=(8, 6.4), sharex=True)
    for ax, (col, titulo, color) in zip(ejes, paneles):
        s = series[col].dropna()
        if col == "policia_registro_victimas" and "mindefensa_agregado_hurtos" in series:
            ctx = series.loc[series.index < "2020-01-01", "mindefensa_agregado_hurtos"].dropna()
            ax.plot(ctx.index, ctx.values, color=color, lw=1.2, ls="--",
                    label="2018–2019: agregado de MinDefensa (contexto)")
            ax.legend(frameon=False, fontsize=7, loc="upper left")
        ax.plot(s.index, s.values, color=color, lw=1.4)
        ax.axvspan(pd.Timestamp("2018-01-01"), pd.Timestamp("2020-01-01"), color="#eeeeee", zorder=0)
        ax.set_title(titulo, loc="left", fontsize=9)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ejes[-1].set_xlabel("Mes del hecho (sombreado: 2018–2019, fuera del periodo principal)")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(carpeta / f"series_mensuales_fuentes.{ext}", bbox_inches="tight")
    plt.close(fig)

    if loc is not None:
        fig, ax = plt.subplots(figsize=(6.5, 0.26 * len(loc) + 1.0))
        ax.barh(loc["localidad"][::-1], loc["llamadas"][::-1], color="#c0504d")
        ax.set_xlabel("Llamadas de hurto (suma de CANT_INCIDENTES), 2020–2025")
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        for ext in ("png", "pdf"):
            fig.savefig(carpeta / f"linea123_localidad.{ext}", bbox_inches="tight")
        plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--auditoria", default="outputs/auditoria")
    p.add_argument("--auditoria-policia", default="outputs/auditoria_policia")
    p.add_argument("--linea123", default=LINEA123)
    p.add_argument("--salida", default="outputs/informe")
    a = p.parse_args()

    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    series = series_mensuales(Path(a.auditoria), Path(a.auditoria_policia))
    series.to_csv(salida / "series_mensuales_fuentes.csv", date_format="%Y-%m")
    loc = None
    if Path(a.linea123).exists():
        loc = localidades(Path(a.linea123))
        loc.to_csv(salida / "linea123_localidad_2020_2025.csv", index=False)
    else:
        print(f"Aviso: no existe {a.linea123}; se omite la figura por localidad.")
    figuras(series, loc, salida / "figuras")
    print(f"Salidas en {salida}")


if __name__ == "__main__":
    main()
