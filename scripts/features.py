#!/usr/bin/env python3
"""Variables derivadas de la serie objetivo, construidas solo con información pasada (#33).

La variable objetivo es el número de víctimas de hurto a personas registradas en Bogotá el día `t`.
Todo lo que este módulo produce para la fila `t` debe poder calcularse **antes** de conocer ese día.

## Regla de disponibilidad

Cada variable declara en `DISPONIBILIDAD` cuándo se conoce:

* `calendario` — se conoce con años de antelación: fecha, día de la semana, festivos.
* `pasado` — usa solo valores de la serie hasta `t-1`.
* `prohibida` — usaría `t` o posterior. No se construye aquí, y se listan para que nadie las añada
  por descuido.

La prueba `tests/test_features.py` no se conforma con revisar nombres: perturba la serie desde el
día `t` hacia adelante, reconstruye las variables y comprueba que la fila `t` **no cambia**. Si
alguna variable mirara el presente o el futuro, esa fila cambiaría y la prueba falla.

## Festivos

Se calculan, no se copian de una lista: días fijos, los que la Ley 51 de 1983 («Ley Emiliani»)
traslada al lunes siguiente, y los que dependen de la Pascua. La fecha de Pascua sale del algoritmo
gregoriano anónimo. Así el calendario vale para cualquier año sin mantenimiento.

Uso::

    python scripts/features.py --entrada data/processed/serie_objetivo_diaria.csv
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("features")

#: Rezagos de la serie, en días. 1 y 7 son los comparadores naturales; 14 y 28 dan dos y cuatro semanas.
REZAGOS = (1, 7, 14, 28)

#: Ventanas de las medias móviles, siempre sobre la serie desplazada un día.
VENTANAS = (7, 28)

#: Festivos de fecha fija.
FIJOS = ((1, 1), (5, 1), (7, 20), (8, 7), (12, 8), (12, 25))

#: Festivos que la Ley Emiliani traslada al lunes siguiente si no caen en lunes.
EMILIANI = ((1, 6), (3, 19), (6, 29), (8, 15), (10, 12), (11, 1), (11, 11))

#: Festivos ligados a la Pascua: (desplazamiento en días, ¿se traslada al lunes?).
#: Jueves y Viernes Santo no se trasladan; Ascensión, Corpus Christi y Sagrado Corazón sí.
PASCUA = ((-3, False), (-2, False), (43, True), (64, True), (71, True))

#: Colombia celebra 18 festivos, pero hay años con menos fechas distintas porque dos coinciden.
#: En 2025, San Pedro (29 de junio, domingo) y el Sagrado Corazón (Pascua + 71 = 29 de junio) se
#: trasladan los dos al lunes 30 de junio, así que ese año hay 17 fechas festivas y no 18.

#: De dónde sale cada variable y cuándo se conoce.
DISPONIBILIDAD: dict[str, str] = {
    "victimas": "objetivo — es el valor de t, nunca una predictora",
    "anio": "calendario",
    "mes": "calendario",
    "dia_del_mes": "calendario",
    "dia_semana": "calendario",
    "fin_de_semana": "calendario",
    "semana_del_anio": "calendario",
    "quincena": "calendario",
    "festivo": "calendario",
    "vispera_de_festivo": "calendario — depende de t+1, pero el calendario se conoce de antemano",
    "dia_despues_de_festivo": "calendario",
    "puente": "calendario",
    **{f"rezago_{k}": f"pasado — valor de t-{k}" for k in REZAGOS},
    **{f"media_previa_{v}": f"pasado — media de t-1 a t-{v}" for v in VENTANAS},
    **{f"desv_previa_{v}": f"pasado — desviación de t-1 a t-{v}" for v in VENTANAS},
    "tendencia_7_28": "pasado — cociente entre la media previa de 7 y la de 28 días",
}

#: Variables de otras fuentes que NO se usan como predictoras, con el motivo.
PROHIBIDAS: dict[str, str] = {
    "fiscalia.a_o_creacion_proceso": "el proceso puede abrirse meses después del hecho",
    "fiscalia.mes_creacion_proceso": "igual que el anterior",
    "fiscalia.etapa": "avanza con el tiempo transcurrido desde el hecho",
    "fiscalia.estado": "refleja la situación de la investigación al momento de la consulta (#19)",
    "policia.pico_revision": "se calcula con el percentil de la propia serie, incluido el futuro",
    "serie.media_movil_centrada": "una media centrada en t usa días posteriores a t",
}


def pascua(anio: int) -> dt.date:
    """Domingo de Pascua por el algoritmo gregoriano anónimo."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(anio, mes, dia)


def _al_lunes(f: dt.date) -> dt.date:
    """Traslada al lunes siguiente si no cae en lunes (Ley 51 de 1983)."""
    return f if f.weekday() == 0 else f + dt.timedelta(days=7 - f.weekday())


def festivos(anio: int) -> set[dt.date]:
    """Festivos nacionales de Colombia de un año."""
    fs = {dt.date(anio, m, d) for m, d in FIJOS}
    fs |= {_al_lunes(dt.date(anio, m, d)) for m, d in EMILIANI}
    p = pascua(anio)
    for delta, mover in PASCUA:
        f = p + dt.timedelta(days=delta)
        fs.add(_al_lunes(f) if mover else f)
    return fs


def calendario_festivos(inicio: pd.Timestamp, fin: pd.Timestamp) -> set[dt.date]:
    fs: set[dt.date] = set()
    for anio in range(inicio.year - 1, fin.year + 2):
        fs |= festivos(anio)
    return fs


def construir(serie: pd.DataFrame, objetivo: str = "victimas") -> pd.DataFrame:
    """Devuelve la matriz de variables. `serie` debe tener índice de fechas diario y sin huecos."""
    if not isinstance(serie.index, pd.DatetimeIndex):
        raise ValueError("la serie debe tener un índice de fechas")
    if serie.index.has_duplicates:
        raise ValueError("la serie tiene fechas repetidas")
    esperado = pd.date_range(serie.index.min(), serie.index.max(), freq="D")
    if len(esperado.difference(serie.index)):
        raise ValueError(f"faltan {len(esperado.difference(serie.index))} días en el calendario")

    y = serie[objetivo].astype(float)
    fs = calendario_festivos(serie.index.min(), serie.index.max())
    idx = serie.index
    es_festivo = pd.Series([d.date() in fs for d in idx], index=idx)

    X = pd.DataFrame(index=idx)
    X[objetivo] = y

    # ---- calendario: se conoce con años de antelación
    X["anio"] = idx.year
    X["mes"] = idx.month
    X["dia_del_mes"] = idx.day
    X["dia_semana"] = idx.dayofweek
    X["fin_de_semana"] = (idx.dayofweek >= 5).astype(int)
    X["semana_del_anio"] = idx.isocalendar().week.to_numpy()
    # Días de pago: el 15 y el último día del mes concentran movimiento de efectivo.
    X["quincena"] = ((idx.day == 15) | idx.is_month_end).astype(int)
    X["festivo"] = es_festivo.astype(int)
    X["vispera_de_festivo"] = es_festivo.shift(-1, fill_value=False).astype(int)
    X["dia_despues_de_festivo"] = es_festivo.shift(1, fill_value=False).astype(int)
    # Puente: festivo que cae en lunes. La Ley Emiliani traslada al lunes la mayoría de los
    # festivos movibles, así que esta condición cubre los puentes reales del calendario
    # colombiano. No se marca el caso del lunes laboral entre domingo y un festivo en martes,
    # que con el traslado al lunes casi no ocurre.
    X["puente"] = (es_festivo.to_numpy() & (idx.dayofweek == 0)).astype(int)

    # ---- pasado: solo valores anteriores a t
    for k in REZAGOS:
        X[f"rezago_{k}"] = y.shift(k)
    previa = y.shift(1)
    for v in VENTANAS:
        X[f"media_previa_{v}"] = previa.rolling(v).mean()
        X[f"desv_previa_{v}"] = previa.rolling(v).std()
    X["tendencia_7_28"] = X["media_previa_7"] / X["media_previa_28"]

    faltan = set(X.columns) - set(DISPONIBILIDAD)
    if faltan:
        raise ValueError(f"variables sin regla de disponibilidad declarada: {sorted(faltan)}")
    return X


def predictoras(X: pd.DataFrame, objetivo: str = "victimas") -> list[str]:
    return [c for c in X.columns if c != objetivo]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--entrada", type=Path, default=Path("data/processed/serie_objetivo_diaria.csv"))
    p.add_argument("--objetivo", default="victimas")
    p.add_argument("--procesados", type=Path, default=Path("data/processed"))
    p.add_argument("--salida", type=Path, default=Path("outputs/features"))
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not a.entrada.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", a.entrada)
        return 2

    serie = pd.read_csv(a.entrada, parse_dates=["fecha"]).set_index("fecha").sort_index()
    X = construir(serie, a.objetivo)

    a.procesados.mkdir(parents=True, exist_ok=True)
    a.salida.mkdir(parents=True, exist_ok=True)
    X.to_csv(a.procesados / "features_diarias.csv", date_format="%Y-%m-%d")

    cols = predictoras(X, a.objetivo)
    nulos_iniciales = int(X[cols].isna().any(axis=1).sum())
    doc = {
        "objetivo": a.objetivo,
        "periodo": [X.index.min().date().isoformat(), X.index.max().date().isoformat()],
        "dias": int(len(X)),
        "n_predictoras": len(cols),
        "filas_con_algun_nulo": nulos_iniciales,
        "nota_nulos": ("los nulos están solo al principio: los rezagos y las ventanas necesitan "
                       "historia. Se conservan; descartarlos es decisión del modelado"),
        "primera_fila_completa": X[cols].dropna().index.min().date().isoformat(),
        "disponibilidad": {c: DISPONIBILIDAD[c] for c in X.columns},
        "prohibidas": PROHIBIDAS,
        "festivos_en_el_periodo": sorted(
            d.isoformat() for d in calendario_festivos(X.index.min(), X.index.max())
            if X.index.min().date() <= d <= X.index.max().date()),
    }
    (a.salida / "diccionario_features.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("%s días · %s predictoras · primera fila completa %s",
             doc["dias"], doc["n_predictoras"], doc["primera_fila_completa"])
    log.info("festivos en el periodo: %s", len(doc["festivos_en_el_periodo"]))
    log.info("salidas: %s y %s", a.procesados / "features_diarias.csv",
             a.salida / "diccionario_features.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
