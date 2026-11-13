"""Construye la serie objetivo diaria a partir del registro de la Policía Nacional.

Variable objetivo (decisiones.md, D-01): número diario de víctimas de hurto a personas
registradas en Bogotá D. C., 2020-01-01 a 2025-12-31.

Entrada: los CSV que produce ``scripts/policia_registro_a_csv.py`` (una fila por víctima,
``CANTIDAD = 1``). Se aplican los mismos filtros que el manifiesto de auditoría
(``config/fuentes_auditoria.json``, fuente ``policia_registro``):

* Bogotá: ``CODIGO DANE`` coincide con ``^0*11001$``.
* Hurto a personas: ``DELITOS`` contiene ``(05022)``.

Las filas repetidas **no se eliminan**: el registro no trae identificador, y dos víctimas del
mismo día, con el mismo arma, género y grupo de edad, producen filas idénticas legítimas.

Salidas en ``--salida`` (por defecto ``outputs/serie_objetivo``):

* ``serie_diaria_policia.csv``: una fila por día del calendario, con ``victimas``. Los días sin
  ningún registro aparecen con 0 y se cuentan en el resumen.
* ``resumen_serie.json``: filas de entrada, filas filtradas, suma de ``CANTIDAD``, días,
  estadísticas descriptivas y totales por año, con el SHA-256 de cada CSV leído.
* ``figuras/serie_diaria_policia.{png,pdf}``: la serie y su media móvil de 28 días.

Uso::

    python scripts/serie_objetivo_policia.py --entrada data/raw/policia_registro/csv
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

INICIO = "2020-01-01"
FIN = "2025-12-31"
PATRON_BOGOTA = re.compile(r"^0*11001$")
PATRON_HURTO = r"\(0*5022\)"
COLUMNAS = ["FECHA HECHO", "CODIGO DANE", "DELITOS", "CANTIDAD"]
# Variables de la víctima y del hecho cuya distribución se resume (el arma se renombra en 2021).
PERFIL = ["GENERO", "*AGRUPA EDAD PERSONA*"]


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer(archivos: list[Path], chunksize: int) -> tuple[pd.DataFrame, dict]:
    conteos: list[pd.DataFrame] = []
    perfiles: list[pd.DataFrame] = []
    meta = {"archivos": [], "filas_entrada": 0, "filas_bogota": 0, "filas_hurto": 0}
    for ruta in archivos:
        filas = bogota = hurto = 0
        cabecera = pd.read_csv(ruta, nrows=0).columns
        arma = "ARMA MEDIO" if "ARMA MEDIO" in cabecera else "ARMAS MEDIOS"
        usar = COLUMNAS + [arma] + [c for c in PERFIL if c in cabecera]
        for bloque in pd.read_csv(ruta, usecols=usar, dtype=str, chunksize=chunksize):
            bloque = bloque.rename(columns={arma: "ARMAS MEDIOS"})
            filas += len(bloque)
            dane = bloque["CODIGO DANE"].fillna("").str.strip()
            bloque = bloque[dane.str.match(PATRON_BOGOTA)]
            bogota += len(bloque)
            bloque = bloque[bloque["DELITOS"].fillna("").str.contains(PATRON_HURTO, regex=True)]
            hurto += len(bloque)
            perfiles.append(bloque[["ARMAS MEDIOS"] + PERFIL])
            fechas = pd.to_datetime(bloque["FECHA HECHO"].str.strip(), format="%Y/%m/%d", errors="coerce")
            cantidad = pd.to_numeric(bloque["CANTIDAD"], errors="coerce")
            conteos.append(pd.DataFrame({"fecha": fechas, "filas": 1, "cantidad": cantidad}))
        meta["archivos"].append({"archivo": ruta.as_posix(), "sha256": sha256(ruta), "filas": filas,
                                 "filas_bogota": bogota, "filas_hurto": hurto})
        meta["filas_entrada"] += filas
        meta["filas_bogota"] += bogota
        meta["filas_hurto"] += hurto
    perfil = pd.concat(perfiles, ignore_index=True)
    meta["perfil_poblacion"] = {
        col: {"nulos": int(perfil[col].isna().sum()),
              "pct_nulos": round(100 * float(perfil[col].isna().mean()), 2),
              "categorias": int(perfil[col].nunique()),
              "frecuencias": {str(k): int(v) for k, v in perfil[col].value_counts(dropna=False).head(8).items()}}
        for col in perfil.columns
    }
    return pd.concat(conteos, ignore_index=True), meta


def construir(registros: pd.DataFrame, meta: dict) -> tuple[pd.DataFrame, dict]:
    fechas_invalidas = int(registros["fecha"].isna().sum())
    fuera = registros["fecha"].notna() & ~registros["fecha"].between(INICIO, FIN)
    validos = registros[registros["fecha"].notna() & ~fuera]
    diaria = validos.groupby("fecha").agg(victimas=("filas", "sum"), suma_cantidad=("cantidad", "sum"))
    calendario = pd.date_range(INICIO, FIN, freq="D", name="fecha")
    diaria = diaria.reindex(calendario, fill_value=0)

    v = diaria["victimas"]
    pico = v.idxmax()
    minimo = v.idxmin()
    anual = v.groupby(v.index.year).sum()
    resumen = {
        **meta,
        "variable_objetivo": "victimas de hurto a personas registradas por dia en Bogota D. C.",
        "periodo": [INICIO, FIN],
        "fechas_invalidas": fechas_invalidas,
        "filas_fuera_del_periodo": int(fuera.sum()),
        "filas_en_la_serie": int(v.sum()),
        "suma_cantidad_en_la_serie": float(diaria["suma_cantidad"].sum()),
        "cantidad_distinta_de_1": int((validos["cantidad"] != 1).sum()),
        "dias": int(len(v)),
        "dias_sin_registros": int((v == 0).sum()),
        "media": round(float(v.mean()), 2),
        "mediana": float(v.median()),
        "desviacion_estandar": round(float(v.std()), 2),
        "minimo": {"fecha": minimo.date().isoformat(), "victimas": int(v.min())},
        "maximo": {"fecha": pico.date().isoformat(), "victimas": int(v.max())},
        "total_por_anio": {str(k): int(x) for k, x in anual.items()},
        "media_diaria_por_anio": {str(k): round(float(x), 2) for k, x in v.groupby(v.index.year).mean().items()},
        "media_por_dia_semana": {d: round(float(v[v.index.day_of_week == i].mean()), 2) for i, d in enumerate(
            ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"])},
    }
    return diaria.reset_index()[["fecha", "victimas"]], resumen


def figura(serie: pd.DataFrame, carpeta: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    carpeta.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"savefig.dpi": 200, "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    s = serie.set_index("fecha")["victimas"]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(s.index, s.values, lw=0.5, color="#9db4cf", label="Víctimas por día")
    ax.plot(s.index, s.rolling(28, center=True).mean(), lw=1.6, color="#1f4e79", label="Media móvil de 28 días")
    ax.set_ylabel("Víctimas registradas")
    ax.set_title("Hurto a personas en Bogotá, registro de la Policía Nacional, 2020–2025")
    ax.legend(frameon=False, loc="upper left")
    for ext in ("png", "pdf"):
        fig.savefig(carpeta / f"serie_diaria_policia.{ext}", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--entrada", default="data/raw/policia_registro/csv")
    p.add_argument("--patron", default="delitos_registro_*.csv")
    p.add_argument("--salida", default="outputs/serie_objetivo")
    p.add_argument("--chunksize", type=int, default=200_000)
    p.add_argument("--sin-figura", action="store_true")
    a = p.parse_args()

    archivos = sorted(Path(a.entrada).glob(a.patron))
    if not archivos:
        raise SystemExit(f"No hay archivos {a.patron} en {a.entrada}. Conviértalos con scripts/policia_registro_a_csv.py.")
    registros, meta = leer(archivos, a.chunksize)
    serie, resumen = construir(registros, meta)

    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    serie.to_csv(salida / "serie_diaria_policia.csv", index=False, date_format="%Y-%m-%d")
    (salida / "resumen_serie.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    if not a.sin_figura:
        figura(serie, salida / "figuras")
    print(f"{resumen['filas_hurto']} filas de hurto a personas en Bogotá -> {resumen['dias']} días "
          f"({resumen['dias_sin_registros']} sin registros). Salida en {salida}.")


if __name__ == "__main__":
    main()
