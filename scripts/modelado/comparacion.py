#!/usr/bin/env python3
"""Evaluación y comparación de todos los modelos contra la barra (#46, sección 9).

No entrena nada. Lee las predicciones que ya dejaron #43 (`estadisticos/`), #44 (`arboles/`), #45
(`ajuste/`) y #144 (`regresion/`, si existe), y recalcula las de los comparadores triviales de #42,
que no tienen estado.
Con eso arma:

* ``tabla_comparativa.csv``: métricas de la evaluación final, distancia a la barra, estabilidad
  entre pliegues (MAE medio, desviación, peor pliegue, pliegues ganados a la barra) y la prueba de
  Diebold-Mariano contra la barra.
* ``mae_por_pliegue.csv``: el MAE de cada modelo en cada pliegue, junto al de la barra.
* ``errores_por_periodo.csv``: error absoluto medio de la evaluación final por mes, por día de la
  semana y por tipo de día (festivo o no).
* ``figuras/``: pronóstico frente a observado en la evaluación final y MAE por pliegue.

## Trazabilidad

Cada métrica se recalcula desde las predicciones guardadas y se **compara con el CSV de métricas de
su issue**. Si no coinciden (más allá del redondeo a dos decimales), el script se detiene: la tabla
de la sección 9 no puede contener una cifra que no salga de un archivo.

## La barra y la prueba

La barra es la de D-04: el mejor comparador en la evaluación final, hoy el ingenuo estacional. En
cada pliegue se compara contra el **mismo** comparador, no contra el que gane en ese pliegue, para
que "pliegues ganados" no cambie de rival.

Diebold-Mariano se calcula con pérdida absoluta (coherente con el MAE, la métrica principal) y
cuadrática. La versión principal es la de Harvey, Leybourne y Newbold (1997) para horizonte 1, con
distribución t de n-1 grados de libertad. Como los residuos de los modelos muestran autocorrelación
(Ljung-Box en #43), se añade como robustez la varianza de Newey-West con 7 rezagos.

## Qué no hace

No compara por localidad: la serie objetivo es distrital (D-01) y ningún modelo predice localidades.

Uso::

    python scripts/modelado/comparacion.py
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "scripts", RAIZ / "scripts" / "modelado"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import features as feat  # noqa: E402
from modelado import cargar  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import mae_ingenuo_estacional, metricas, particion, pliegues  # noqa: E402
from modelado.referencia import COMPARADORES, predictor  # noqa: E402

log = logging.getLogger("modelado.comparacion")

#: Carpeta de cada issue dentro de outputs/modelado y la etiqueta con que aparece en las tablas.
ORIGENES: dict[str, str] = {"estadisticos": "#43", "arboles": "#44", "ajuste": "#45",
                            "regresion": "#144"}
#: Los modelos finales de cada familia. SARIMA, ETS y los árboles son los ajustados de #45; la regresión
#: no tiene una versión aparte porque su regularización ya se elige en los pliegues dentro de #144.
FINALES = ("#45", "#144")
FAMILIA = {"sarima": "estadístico", "ets": "estadístico", "bosque_aleatorio": "árboles",
           "gradiente_histogramas": "árboles", "regresion_lineal": "regresión"}
SUFIJOS_SENSIBILIDAD = ("_sin_2020", "_desde_2021")
REZAGOS_HAC = 7
TOLERANCIA = 0.011  # las métricas guardadas están redondeadas a 2 decimales (MASE a 3)
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = {5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre"}


# ------------------------------------------------------------------ prueba de Diebold-Mariano
def diebold_mariano(e_barra: np.ndarray, e_modelo: np.ndarray, potencia: int = 1,
                    rezagos: int = 0) -> dict:
    """Diebold-Mariano para horizonte 1, con la corrección de Harvey, Leybourne y Newbold.

    `d_t = |e_barra|^p - |e_modelo|^p`: un estadístico positivo significa que el modelo pierde
    menos que la barra. Con `rezagos=0` es la versión HLN (t de n-1 g.l.); con `rezagos>0` la
    varianza es la de Newey-West (pesos de Bartlett) y el valor p, normal.
    """
    d = np.abs(np.asarray(e_barra, float)) ** potencia - np.abs(np.asarray(e_modelo, float)) ** potencia
    n = d.size
    dc = d - d.mean()
    var = float(dc @ dc) / n
    for k in range(1, rezagos + 1):
        var += 2 * (1 - k / (rezagos + 1)) * float(dc[k:] @ dc[:-k]) / n
    if var <= 0:
        return {"estadistico": float("nan"), "p_valor": float("nan"), "media_diferencia": 0.0}
    dm = d.mean() / np.sqrt(var / n)
    if rezagos == 0:
        dm *= np.sqrt((n - 1) / n)  # HLN para h = 1: (n + 1 - 2h + h(h-1)/n) / n
        p = 2 * stats.t.sf(abs(dm), df=n - 1)
    else:
        p = 2 * stats.norm.sf(abs(dm))
    return {"estadistico": float(dm), "p_valor": float(p), "media_diferencia": float(d.mean())}


# ------------------------------------------------------------------ carga de predicciones
def predicciones_referencia(cfg, y: pd.Series) -> pd.DataFrame:
    """Predicciones de los comparadores de #42 en los mismos tramos que usa el arnés."""
    idx = y.index
    tramos = [(p.numero, p.mascaras(idx)[1]) for p in pliegues(cfg, idx)]
    tramos.append(("final", particion(cfg, idx)[1]))
    filas = []
    for nombre, spec in COMPARADORES.items():
        pred = predictor(*spec)
        for numero, ev in tramos:
            if not ev.any():
                continue
            p = pred(y, None, None, idx[ev])
            filas.append(pd.DataFrame({"modelo": nombre, "pliegue": str(numero), "fecha": idx[ev],
                                       "real": y[ev].values, "prediccion": p.values}))
    return pd.concat(filas, ignore_index=True).assign(origen="#42", familia="comparador")


def cargar_predicciones(carpeta: Path) -> pd.DataFrame:
    partes = []
    for sub, origen in ORIGENES.items():
        f = carpeta / sub / "predicciones_por_pliegue.csv"
        if not f.is_file():
            log.warning("no hay %s: se omite %s", f, origen)
            continue
        d = pd.read_csv(f, parse_dates=["fecha"], dtype={"pliegue": str})
        base = d["modelo"].str.replace("|".join(SUFIJOS_SENSIBILIDAD), "", regex=True)
        partes.append(d.assign(origen=origen, familia=base.map(FAMILIA)))
    if not partes:
        raise FileNotFoundError(f"no hay predicciones de modelos en {carpeta}")
    return pd.concat(partes, ignore_index=True)


def clave(origen: str, modelo: str) -> str:
    return f"{modelo} ({origen})"


# ------------------------------------------------------------------ métricas y trazabilidad
def metricas_por_tramo(cfg, y: pd.Series, pred: pd.DataFrame) -> pd.DataFrame:
    """MAE, RMSE, MAPE y MASE por modelo y tramo, con el denominador de MASE de cada tramo."""
    idx = y.index
    den = {str(p.numero): mae_ingenuo_estacional(y[p.mascaras(idx)[0]], cfg.periodo_estacional_mase)
           for p in pliegues(cfg, idx)}
    den["final"] = mae_ingenuo_estacional(y[particion(cfg, idx)[0]], cfg.periodo_estacional_mase)
    filas = []
    for (origen, modelo, pliegue), g in pred.groupby(["origen", "modelo", "pliegue"], sort=False):
        s = pd.Series(g["prediccion"].values, index=pd.DatetimeIndex(g["fecha"]))
        m = metricas(y.loc[s.index], s, den[pliegue])
        filas.append({"origen": origen, "modelo": modelo, "pliegue": pliegue, **m})
    return pd.DataFrame(filas)


def comprobar_trazabilidad(m: pd.DataFrame, carpeta: Path) -> int:
    """Compara lo recalculado con los CSV de cada issue. Devuelve cuántas cifras se cotejaron."""
    cotejadas = 0
    for sub, origen in {"referencia": "#42", **ORIGENES}.items():
        fin, plg = carpeta / sub / "metricas_finales.csv", carpeta / sub / "metricas_por_pliegue.csv"
        if not fin.is_file():
            continue
        g = pd.read_csv(fin)
        g = g.rename(columns={g.columns[0]: "modelo"}) if g.columns[0] != "modelo" else g
        g["pliegue"] = "final"
        p = pd.read_csv(plg)
        p = p.rename(columns={"comparador": "modelo"})
        p["pliegue"] = p["pliegue"].astype(str)
        guardado = pd.concat([g, p], ignore_index=True)
        calc = m[m["origen"] == origen].merge(guardado, on=["modelo", "pliegue"],
                                              suffixes=("", "_guardado"))
        esperado = len(guardado)
        if len(calc) != esperado:
            raise RuntimeError(f"{sub}: se esperaban {esperado} filas cotejables y hay {len(calc)}")
        for met in ("MAE", "RMSE", "MAPE", "MASE"):
            dif = (calc[met] - calc[f"{met}_guardado"]).abs()
            if (dif > TOLERANCIA).any():
                malas = calc.loc[dif > TOLERANCIA, ["modelo", "pliegue", met, f"{met}_guardado"]]
                raise RuntimeError(f"{sub}: {met} recalculado no coincide con el guardado:\n{malas}")
            cotejadas += len(calc)
    return cotejadas


# ------------------------------------------------------------------ tablas
def tabla_comparativa(m: pd.DataFrame, pred: pd.DataFrame, barra: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    fin = m[m["pliegue"] == "final"].set_index(["origen", "modelo"])
    plg = m[m["pliegue"] != "final"]
    mae_barra = plg[(plg["origen"] == "#42") & (plg["modelo"] == barra)].set_index("pliegue")["MAE"]
    final_barra = fin.loc[("#42", barra)]

    ev = pred[pred["pliegue"] == "final"]
    err = {k: g.set_index("fecha").eval("real - prediccion")
           for k, g in ev.groupby(["origen", "modelo"], sort=False)}
    e_b = err[("#42", barra)]

    filas, por_pliegue = [], []
    for (origen, modelo), f in fin.iterrows():
        mp = plg[(plg["origen"] == origen) & (plg["modelo"] == modelo)].set_index("pliegue")["MAE"]
        e_m = err[(origen, modelo)].reindex(e_b.index)
        fila = {"origen": origen, "modelo": modelo,
                "familia": "comparador" if origen == "#42" else FAMILIA.get(
                    modelo.replace("_sin_2020", "").replace("_desde_2021", "")),
                "sensibilidad": modelo.endswith(SUFIJOS_SENSIBILIDAD),
                **{k: f[k] for k in ("MAE", "RMSE", "MAPE", "MASE")},
                "MAE_vs_barra": round(f["MAE"] - final_barra["MAE"], 2),
                "MAE_vs_barra_pct": round(100 * (f["MAE"] / final_barra["MAE"] - 1), 1),
                "MAE_medio_pliegues": round(mp.mean(), 2),
                "MAE_desv_pliegues": round(mp.std(ddof=1), 2),
                "MAE_peor_pliegue": round(mp.max(), 2),
                "pliegues_ganados_a_barra": int((mp < mae_barra.reindex(mp.index)).sum()),
                "pliegues": int(mp.size)}
        if (origen, modelo) != ("#42", barra):
            for nom, pot in (("abs", 1), ("cuad", 2)):
                dm = diebold_mariano(e_b.values, e_m.values, pot)
                hac = diebold_mariano(e_b.values, e_m.values, pot, REZAGOS_HAC)
                fila |= {f"DM_{nom}": round(dm["estadistico"], 3), f"p_DM_{nom}": dm["p_valor"],
                         f"p_DM_{nom}_HAC{REZAGOS_HAC}": hac["p_valor"]}
        filas.append(fila)
        por_pliegue += [{"origen": origen, "modelo": modelo, "pliegue": int(k), "MAE": v,
                         "MAE_barra": mae_barra[k]} for k, v in mp.items()]
    t = pd.DataFrame(filas).sort_values(["sensibilidad", "MAE"]).reset_index(drop=True)
    for c in [c for c in t if c.startswith("p_DM")]:
        t[c] = t[c].map(lambda v: float(f"{v:.3g}") if pd.notna(v) else v)
    return t, pd.DataFrame(por_pliegue)


def dm_entre_modelos(pred: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    """Diebold-Mariano (pérdida absoluta, HLN) entre cada par de modelos sin sensibilidad.

    Responde otra pregunta que la tabla: no si un modelo bate la barra, sino si dos modelos que la
    baten se distinguen entre sí en la evaluación final.
    """
    c = t[(~t["sensibilidad"]) & (t["origen"] != "#42")]
    if (c["origen"] == "#45").any():  # los modelos finales son los ajustados
        c = c[c["origen"].isin(FINALES)]
    c = list(c[["origen", "modelo"]].itertuples(index=False))
    ev = pred[pred["pliegue"] == "final"]
    err = {(o, m): g.set_index("fecha").eval("real - prediccion")
           for (o, m), g in ev.groupby(["origen", "modelo"], sort=False)}
    filas = []
    for i, a in enumerate(c):
        for b in c[i + 1:]:
            ea, eb = err[tuple(a)], err[tuple(b)].reindex(err[tuple(a)].index)
            dm = diebold_mariano(eb.values, ea.values, 1)
            hac = diebold_mariano(eb.values, ea.values, 1, REZAGOS_HAC)
            filas.append({"modelo_a": clave(*a), "modelo_b": clave(*b),
                          "MAE_a": round(float(ea.abs().mean()), 2),
                          "MAE_b": round(float(eb.abs().mean()), 2),
                          "DM_abs": round(dm["estadistico"], 3),
                          "p_DM_abs": float(f"{dm['p_valor']:.3g}"),
                          f"p_DM_abs_HAC{REZAGOS_HAC}": float(f"{hac['p_valor']:.3g}")})
    return pd.DataFrame(filas)


def errores_por_periodo(pred: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Error absoluto medio de la evaluación final por mes, día de la semana y tipo de día."""
    cal = feat.construir(y.to_frame("victimas"), objetivo="victimas")[["festivo"]]
    ev = pred[pred["pliegue"] == "final"].copy()
    ev["error_abs"] = (ev["real"] - ev["prediccion"]).abs()
    ev["error"] = ev["prediccion"] - ev["real"]
    ev["mes"] = ev["fecha"].dt.month.map(MESES)
    ev["dia_semana"] = ev["fecha"].dt.day_of_week.map(dict(enumerate(DIAS)))
    ev["tipo_dia"] = np.where(cal["festivo"].reindex(ev["fecha"]).values == 1, "festivo", "no festivo")
    filas = []
    for dim in ("mes", "dia_semana", "tipo_dia"):
        g = ev.groupby(["origen", "modelo", dim], sort=False).agg(
            n=("error_abs", "size"), MAE=("error_abs", "mean"), sesgo=("error", "mean"))
        filas.append(g.reset_index().rename(columns={dim: "valor"}).assign(dimension=dim))
    out = pd.concat(filas, ignore_index=True)
    out[["MAE", "sesgo"]] = out[["MAE", "sesgo"]].round(2)
    return out[["dimension", "valor", "origen", "modelo", "n", "MAE", "sesgo"]]


def principales(t: pd.DataFrame) -> list[tuple[str, str]]:
    """Por familia, el modelo sin sensibilidad de menor MAE medio en los pliegues.

    Se elige por los pliegues (que están dentro del entrenamiento), no por la evaluación final, para
    que la figura no destaque al ganador de la prueba. Se prefiere la versión ajustada (#45), y la
    regresión entra con su propia versión (#144).
    """
    c = t[(~t["sensibilidad"]) & (t["origen"] != "#42")]
    if (c["origen"] == "#45").any():
        c = c[c["origen"].isin(FINALES)]
    return [tuple(c[c["familia"] == f].nsmallest(1, "MAE_medio_pliegues")[["origen", "modelo"]].iloc[0])
            for f in ("estadístico", "árboles", "regresión") if (c["familia"] == f).any()]


# ------------------------------------------------------------------ figuras
NOMBRES = {"sarima": "SARIMA", "ets": "ETS", "bosque_aleatorio": "Bosque aleatorio",
           "gradiente_histogramas": "Gradiente por histogramas", "regresion_lineal": "Regresión lineal"}


def etiqueta(origen: str, modelo: str) -> str:
    """Nombre legible para las figuras; los de #45 y #144 son los modelos finales (ajustados)."""
    nombre = NOMBRES.get(modelo, modelo.replace("_", " "))
    if origen in FINALES:
        return f"{nombre} (ajustada)" if modelo.startswith("regresion") else f"{nombre} (ajustado)"
    return f"{nombre} {origen}"


def coma(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def figuras(pred: pd.DataFrame, t: pd.DataFrame, pp: pd.DataFrame, barra: str, carpeta: Path,
            informe: Path | None) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    carpeta.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"savefig.dpi": 200, "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    elegidos = principales(t)
    colores = ["#1f4e79", "#c0504d", "#4f8a3b"]
    ev = pred[pred["pliegue"] == "final"]
    obs = ev[(ev["origen"] == "#42") & (ev["modelo"] == barra)].set_index("fecha")["real"]
    hechas = []

    fig, ejes = plt.subplots(len(elegidos), 1, figsize=(8, 2.6 * len(elegidos)), sharex=True,
                             squeeze=False)
    b = ev[(ev["origen"] == "#42") & (ev["modelo"] == barra)].set_index("fecha")["prediccion"]
    for ax, (origen, modelo), color in zip(ejes[:, 0], elegidos, colores):
        p = ev[(ev["origen"] == origen) & (ev["modelo"] == modelo)].set_index("fecha")["prediccion"]
        mae = t[(t["origen"] == origen) & (t["modelo"] == modelo)]["MAE"].iloc[0]
        mae_b = t[(t["origen"] == "#42") & (t["modelo"] == barra)]["MAE"].iloc[0]
        ax.plot(obs.index, obs.values, color="#333333", lw=1.0, label="Observado")
        ax.plot(b.index, b.values, color="#999999", lw=0.9, ls="--",
                label=f"Ingenuo estacional (MAE {coma(mae_b)})")
        ax.plot(p.index, p.values, color=color, lw=1.2,
                label=f"{etiqueta(origen, modelo)} (MAE {coma(mae)})")
        ax.set_ylabel("Víctimas por día")
        ax.legend(frameon=False, fontsize=7, loc="lower left", ncol=3, bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(carpeta / f"modelos_pronostico_observado.{ext}", bbox_inches="tight")
    plt.close(fig)
    hechas.append("modelos_pronostico_observado")

    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    bp = pp[pp["modelo"] == elegidos[0][1]].sort_values("pliegue") if elegidos else pp.iloc[:0]
    ax.plot(bp["pliegue"], bp["MAE_barra"], color="#999999", ls="--", marker="o", ms=3,
            label="Ingenuo estacional")
    for (origen, modelo), color in zip(elegidos, colores):
        q = pp[(pp["origen"] == origen) & (pp["modelo"] == modelo)].sort_values("pliegue")
        ax.plot(q["pliegue"], q["MAE"], color=color, marker="o", ms=3,
                label=etiqueta(origen, modelo))
    ax.set_xlabel("Pliegue (origen rodante, 90 días cada uno)")
    ax.set_ylabel("MAE (víctimas por día)")
    ax.set_xticks(sorted(pp["pliegue"].unique()))
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(carpeta / f"modelos_mae_por_pliegue.{ext}", bbox_inches="tight")
    plt.close(fig)
    hechas.append("modelos_mae_por_pliegue")

    if informe is not None:
        informe.mkdir(parents=True, exist_ok=True)
        for h in hechas:
            shutil.copy2(carpeta / f"{h}.pdf", informe / f"{h}.pdf")
    return hechas


# ------------------------------------------------------------------ principal
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=None,
                   help="Carpeta de salida. Por defecto, outputs/modelado/comparacion.")
    p.add_argument("--sin-informe", action="store_true",
                   help="No copiar las figuras a Informe/figuras.")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = cargar()
    if not cfg.serie.is_file():
        log.error("no existe %s. Ejecute antes scripts/preprocesamiento.py", cfg.serie)
        return 2
    y = (pd.read_csv(cfg.serie, parse_dates=["fecha"]).set_index("fecha")[cfg.objetivo]
         .astype(float).sort_index())
    validar_contra_serie(cfg, y.index)
    carpeta = cfg.carpeta_registro
    salida = a.salida or (carpeta / "comparacion")
    salida.mkdir(parents=True, exist_ok=True)

    barra = json.loads((carpeta / "referencia" / "resumen_referencia.json")
                       .read_text(encoding="utf-8"))["barra"]["mejor_por_MAE"]
    pred = pd.concat([predicciones_referencia(cfg, y), cargar_predicciones(carpeta)],
                     ignore_index=True)
    m = metricas_por_tramo(cfg, y, pred)
    n = comprobar_trazabilidad(m, carpeta)
    log.info("trazabilidad: %d cifras recalculadas coinciden con los CSV de cada issue", n)

    t, pp = tabla_comparativa(m, pred, barra)
    per = errores_por_periodo(pred, y)
    t.to_csv(salida / "tabla_comparativa.csv", index=False)
    pp.to_csv(salida / "mae_por_pliegue.csv", index=False)
    per.to_csv(salida / "errores_por_periodo.csv", index=False)
    dm_entre_modelos(pred, t).to_csv(salida / "diebold_mariano_entre_modelos.csv", index=False)
    hechas = figuras(pred, t, pp, barra, salida / "figuras",
                     None if a.sin_informe else RAIZ / "Informe" / "figuras")
    (salida / "resumen_comparacion.json").write_text(json.dumps({
        "barra": barra, "origenes": sorted(pred["origen"].unique().tolist()),
        "cifras_cotejadas": n, "rezagos_hac": REZAGOS_HAC, "principales": principales(t),
        "figuras": hechas,
        "nota_localidad": "la serie objetivo es distrital (D-01): no hay error por localidad",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        log.info("\n%s", t[["origen", "modelo", "MAE", "MASE", "MAE_vs_barra", "MAE_desv_pliegues",
                            "pliegues_ganados_a_barra", "p_DM_abs"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
