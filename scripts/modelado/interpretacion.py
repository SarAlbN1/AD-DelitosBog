#!/usr/bin/env python3
"""Interpretación de los modelos: importancia por permutación y contraste con el EDA (#47).

Responde a una pregunta descriptiva: **en qué se apoyan los modelos ajustados en #45**, y si
coincide con las señales que dejó el análisis exploratorio (el día de la semana, con un 65 % entre
viernes y domingo, y el festivo, con −37,8 % entre lunes festivos y laborables). No es una lectura
causal: la importancia dice cuánto empeora la predicción al romper la relación de una variable con
el resto, no qué produce el hurto.

## Qué se calcula

1. **Importancia por permutación agrupada** de los dos modelos de árboles. Se permutan juntas las
   columnas de cada grupo (los rezagos semanales, las medias previas...), con la misma permutación
   para todas, y se mide cuánto sube el MAE. Agrupar evita el sesgo de permutar una variable que
   tiene sustitutas: si se permuta solo `rezago_7`, el modelo lo suple con `rezago_14` y parece que
   no importa. También se da la importancia por variable, como complemento.
2. Se mide en dos sitios: en los **184 días de evaluación**, con el modelo que se reporta en la
   sección 9, y en los **seis pliegues** de validación, con un modelo entrenado por pliegue. Si las
   dos coinciden, el orden no depende de un periodo. Nada de esto ajusta el modelo: las
   configuraciones son las de `outputs/modelado/ajuste/seleccion.json`.
3. **Contraste con el EDA**: el perfil semanal que reproduce cada modelo y su respuesta al
   indicador de festivo (lunes laborables marcados como festivos y al revés, con lo demás fijo).

SARIMA y ETS no tienen variables explicativas: su estructura (estacionalidad de periodo 7, sin
calendario) ya dice en qué se apoyan, y la sección 10 la discute con las cifras de la sección 9.

Uso::

    python scripts/modelado/interpretacion.py [--salida DIR] [--repeticiones 50]
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

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "scripts", RAIZ / "scripts" / "modelado"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from modelado import cargar, fijar_semillas  # noqa: E402
from modelado.arboles import construir_X, crear_modelo  # noqa: E402
from modelado.config import validar_contra_serie  # noqa: E402
from modelado.evaluacion import particion, pliegues  # noqa: E402

log = logging.getLogger("modelado.interpretacion")

#: Grupos de variables. Cubren las 21 predictoras de `features.py` sin solaparse.
GRUPOS: dict[str, list[str]] = {
    "dia_semana": ["dia_semana", "fin_de_semana"],
    "festivos": ["festivo", "vispera_de_festivo", "dia_despues_de_festivo", "puente"],
    "calendario_lento": ["anio", "mes", "dia_del_mes", "semana_del_anio", "quincena"],
    "anio_2020": ["anio_atipico_2020"],
    "rezago_1": ["rezago_1"],
    "rezagos_semanales": ["rezago_7", "rezago_14", "rezago_28"],
    "medias_previas": ["media_previa_7", "desv_previa_7", "media_previa_28", "desv_previa_28",
                       "tendencia_7_28"],
}
NOMBRES_GRUPOS = {
    "dia_semana": "Día de la semana",
    "festivos": "Festivos y puentes",
    "calendario_lento": "Año, mes y día del mes",
    "anio_2020": "Indicador de 2020",
    "rezago_1": "Rezago de 1 día",
    "rezagos_semanales": "Rezagos de 7, 14 y 28 días",
    "medias_previas": "Medias y desviaciones previas",
}
MODELOS = ("gradiente_histogramas", "bosque_aleatorio")
NOMBRES_MODELOS = {"gradiente_histogramas": "Gradiente por histogramas",
                   "bosque_aleatorio": "Bosque aleatorio"}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
#: Tolerancia del cotejo con `metricas_finales.csv` de #45: las cifras se redondean a centésimas.
TOLERANCIA = 0.011


def mae(a, b) -> float:
    return float(np.mean(np.abs(np.asarray(a, float) - np.asarray(b, float))))


def entrenar(nombre: str, hp: dict, semilla: int, X: pd.DataFrame, y: pd.Series,
             hasta: pd.Timestamp):
    """Ajusta como `arboles.predictor_arbol`: hasta `hasta`, sin las filas con nulos."""
    tr = X[X.index <= hasta]
    tr = tr.loc[tr.notna().all(axis=1)]
    return crear_modelo(nombre, semilla, hp).fit(tr, y.loc[tr.index])


def importancia_permutacion(modelo, X: pd.DataFrame, y: pd.Series, grupos: dict[str, list[str]],
                            repeticiones: int, semilla: int) -> pd.DataFrame:
    """Aumento del MAE al permutar cada grupo de columnas, una fila por grupo y repetición.

    Todas las columnas de un grupo se permutan con la misma permutación, así que conservan su
    relación entre sí y solo pierden la relación con el resto y con `y`. Cada grupo tiene su propio
    generador, derivado de `semilla` y de su posición, para que añadir un grupo no cambie los demás.
    """
    base = mae(y, modelo.predict(X))
    filas = []
    for k, (grupo, cols) in enumerate(grupos.items()):
        rng = np.random.default_rng([semilla, k])
        valores = X[cols].to_numpy()
        for r in range(repeticiones):
            Xp = X.copy()
            Xp[cols] = valores[rng.permutation(len(X))]
            m = mae(y, modelo.predict(Xp))
            filas.append({"grupo": grupo, "repeticion": r, "MAE_base": base, "MAE_permutado": m,
                          "aumento_MAE": m - base})
    return pd.DataFrame(filas)


def resumir(imp: pd.DataFrame, claves: list[str]) -> pd.DataFrame:
    """Media y percentiles 5 y 95 del aumento del MAE, y su proporción sobre el MAE base."""
    g = imp.groupby(claves)
    r = g["aumento_MAE"].agg(aumento_MAE="mean", p05=lambda s: s.quantile(0.05),
                             p95=lambda s: s.quantile(0.95)).reset_index()
    r["MAE_base"] = g["MAE_base"].first().to_numpy()
    r["aumento_pct"] = 100 * r["aumento_MAE"] / r["MAE_base"]
    return r


def perfil_semanal(y: pd.Series, preds: dict[str, pd.Series]) -> pd.DataFrame:
    """Media diaria observada y predicha por día de la semana, en los días que se le pasan."""
    t = pd.DataFrame({"observado": y, **preds})
    t["dia_semana"] = [DIAS[d] for d in t.index.day_of_week]
    return t.groupby("dia_semana").mean().reindex(DIAS)


def respuesta_festivo(modelo, X: pd.DataFrame) -> dict:
    """Cambio relativo de la predicción al marcar como festivo un lunes laborable, y al revés.

    Solo se cambian `festivo` y `puente` (un festivo en lunes es puente): los rezagos y lo demás
    quedan como estaban. Es la respuesta del modelo al indicador, no un efecto causal del festivo.
    """
    lunes = X[X.index.day_of_week == 0]
    lab, fes = lunes[lunes["festivo"] == 0], lunes[lunes["festivo"] == 1]
    salida = {"n_lunes_laborables": int(len(lab)), "n_lunes_festivos": int(len(fes))}
    for clave, sub, valor in (("laborable_a_festivo", lab, 1), ("festivo_a_laborable", fes, 0)):
        if sub.empty:
            salida[clave + "_pct"] = None
            continue
        antes = modelo.predict(sub)
        alterado = sub.copy()
        alterado[["festivo", "puente"]] = valor
        despues = modelo.predict(alterado)
        salida[clave + "_pct"] = float(100 * (despues.sum() / antes.sum() - 1))
    return salida


def coma(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def figura(res_ev: pd.DataFrame, res_pl: pd.DataFrame, carpeta: Path,
           informe: Path | None) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"savefig.dpi": 200, "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    colores = {"gradiente_histogramas": "#1f4e79", "bosque_aleatorio": "#c0504d"}
    orden = (res_ev[res_ev["modelo"] == MODELOS[0]].sort_values("aumento_pct")["grupo"].tolist())
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    pos = np.arange(len(orden))
    alto = 0.38
    for i, m in enumerate(MODELOS):
        e = res_ev[res_ev["modelo"] == m].set_index("grupo").reindex(orden)
        p = res_pl[res_pl["modelo"] == m].set_index("grupo").reindex(orden)
        desp = pos + (alto / 2 if i == 0 else -alto / 2)
        base = e["MAE_base"].iloc[0]
        ax.barh(desp, e["aumento_pct"], height=alto, color=colores[m],
                label=f"{NOMBRES_MODELOS[m]}: evaluación (MAE {coma(base)})")
        ax.errorbar(e["aumento_pct"], desp,
                    xerr=[100 * (e["aumento_MAE"] - e["p05"]) / base,
                          100 * (e["p95"] - e["aumento_MAE"]) / base],
                    fmt="none", ecolor="#333333", elinewidth=0.7, capsize=1.5)
        ax.plot(p["aumento_pct"], desp, ls="none", marker="D", ms=3.5, mfc="white",
                mec=colores[m], mew=1.0, label=f"{NOMBRES_MODELOS[m]}: media en pliegues")
    ax.set_yticks(pos)
    ax.set_yticklabels([NOMBRES_GRUPOS[g] for g in orden])
    ax.axvline(0, color="#999999", lw=0.6)
    ax.set_xlabel("Aumento del MAE al permutar el grupo (% del MAE sin permutar)")
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    nombre = "importancia_permutacion_grupos"
    for ext in ("png", "pdf"):
        fig.savefig(carpeta / f"{nombre}.{ext}", bbox_inches="tight")
    plt.close(fig)
    if informe is not None:
        informe.mkdir(parents=True, exist_ok=True)
        shutil.copy2(carpeta / f"{nombre}.pdf", informe / f"{nombre}.pdf")
    return nombre


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--salida", type=Path, default=RAIZ / "outputs" / "modelado" / "interpretacion")
    p.add_argument("--repeticiones", type=int, default=50,
                   help="Permutaciones por grupo en la evaluación (en cada pliegue, la mitad).")
    p.add_argument("--sin-informe", action="store_true",
                   help="No copiar la figura a Informe/figuras.")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = cargar()
    semilla = fijar_semillas(cfg.semilla)
    seleccion_json = cfg.carpeta_registro / "ajuste" / "seleccion.json"
    if not cfg.serie.is_file() or not seleccion_json.is_file():
        log.error("faltan %s o %s. Ejecute antes preprocesamiento.py y modelado/ajuste.py",
                  cfg.serie, seleccion_json)
        return 2
    y = (pd.read_csv(cfg.serie, parse_dates=["fecha"]).set_index("fecha")[cfg.objetivo]
         .astype(float).sort_index())
    validar_contra_serie(cfg, y.index)
    X = construir_X(y)
    seleccion = json.loads(seleccion_json.read_text(encoding="utf-8"))
    finales = pd.read_csv(cfg.carpeta_registro / "ajuste" / "metricas_finales.csv", index_col=0)
    hp = {m: seleccion["elegidos"][f"arboles.{m}"]["hiperparametros"] for m in MODELOS}
    individuales = {c: [c] for cols in GRUPOS.values() for c in cols}
    assert sorted(individuales) == sorted(X.columns), "los grupos no cubren las predictoras"

    tr, ev = particion(cfg, y.index)
    fin_tr = y.index[tr].max()
    Xev, yev = X[ev], y[ev]
    salida = a.salida
    salida.mkdir(parents=True, exist_ok=True)

    imp_ev, imp_var, imp_pl, preds, cotejo, festivo = [], [], [], {}, {}, {}
    for m in MODELOS:
        modelo = entrenar(m, hp[m], semilla, X, y, fin_tr)
        pred = pd.Series(modelo.predict(Xev), index=Xev.index)
        preds[m] = pred
        reproducido, citado = mae(yev, pred), float(finales.loc[m, "MAE"])
        cotejo[m] = {"MAE_reproducido": round(reproducido, 4), "MAE_ajuste_45": citado,
                     "coincide": abs(reproducido - citado) <= TOLERANCIA}
        if not cotejo[m]["coincide"]:
            log.warning("%s: MAE %.2f frente a %.2f de #45 (¿otro entorno?)", m, reproducido, citado)
        log.info("%s: permutación en evaluación (%d repeticiones)", m, a.repeticiones)
        imp_ev.append(importancia_permutacion(modelo, Xev, yev, GRUPOS, a.repeticiones, semilla)
                      .assign(modelo=m))
        imp_var.append(importancia_permutacion(modelo, Xev, yev, individuales, a.repeticiones,
                                               semilla).assign(modelo=m))
        festivo[m] = respuesta_festivo(modelo, X[tr].dropna())
        for pl in pliegues(cfg, y.index[tr]):
            dias = (y.index > pl.fin_entrenamiento) & (y.index <= pl.fin_evaluacion)
            mp = entrenar(m, hp[m], semilla, X, y, pl.fin_entrenamiento)
            imp_pl.append(importancia_permutacion(mp, X[dias], y[dias], GRUPOS,
                                                  max(1, a.repeticiones // 2), semilla)
                          .assign(modelo=m, pliegue=pl.numero))
        log.info("%s: pliegues listos", m)

    imp_ev, imp_var, imp_pl = (pd.concat(x, ignore_index=True) for x in (imp_ev, imp_var, imp_pl))
    res_ev = resumir(imp_ev, ["modelo", "grupo"])
    res_var = resumir(imp_var, ["modelo", "grupo"]).rename(columns={"grupo": "variable"})
    res_pl_det = resumir(imp_pl, ["modelo", "pliegue", "grupo"])
    res_pl = (res_pl_det.groupby(["modelo", "grupo"])
              .agg(aumento_MAE=("aumento_MAE", "mean"), aumento_pct=("aumento_pct", "mean"),
                   pct_min=("aumento_pct", "min"), pct_max=("aumento_pct", "max"))
              .reset_index())
    for t in (res_ev, res_pl):
        t["puesto"] = t.groupby("modelo")["aumento_pct"].rank(ascending=False, method="min")
    perfil = perfil_semanal(yev, preds)

    redondeo = {"aumento_MAE": 3, "p05": 3, "p95": 3, "MAE_base": 3, "aumento_pct": 2,
                "pct_min": 2, "pct_max": 2}
    res_ev.round(redondeo).to_csv(salida / "importancia_grupos_evaluacion.csv", index=False)
    res_pl.round(redondeo).to_csv(salida / "importancia_grupos_pliegues.csv", index=False)
    res_pl_det.round(redondeo).to_csv(salida / "importancia_grupos_por_pliegue.csv", index=False)
    (res_var.round(redondeo).sort_values(["modelo", "aumento_pct"], ascending=[True, False])
     .to_csv(salida / "importancia_variables_evaluacion.csv", index=False))
    perfil.round(2).to_csv(salida / "perfil_semanal_evaluacion.csv", index_label="dia_semana")

    eda = json.loads((RAIZ / "outputs" / "eda" / "resumen_eda.json").read_text(encoding="utf-8"))
    dias_eda = pd.read_csv(RAIZ / "outputs" / "eda" / "temporal_dia_semana.csv", index_col=0)["media"]
    resumen = {
        "pregunta": "en qué variables se apoyan los modelos de árboles de #45; descriptivo, no causal",
        "metodo": "importancia por permutación agrupada; aumento del MAE; semilla fija",
        "repeticiones_evaluacion": a.repeticiones,
        "repeticiones_por_pliegue": max(1, a.repeticiones // 2),
        "semilla": semilla,
        "grupos": GRUPOS,
        "hiperparametros": hp,
        "cotejo_con_45": cotejo,
        "eda": {"viernes_sobre_domingo_pct": round(100 * (dias_eda["viernes"] / dias_eda["domingo"] - 1), 2),
                "lunes_festivo_vs_laborable_pct": eda["temporal"]["festivos"]["diferencia_lunes_pct"]},
        "perfil_evaluacion_viernes_sobre_domingo_pct": {
            c: round(100 * (perfil.loc["viernes", c] / perfil.loc["domingo", c] - 1), 2)
            for c in perfil.columns},
        "respuesta_al_festivo_en_entrenamiento": {
            m: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}
            for m, d in festivo.items()},
        "puesto_por_grupo": {
            m: {"evaluacion": res_ev[res_ev["modelo"] == m].sort_values("puesto")["grupo"].tolist(),
                "pliegues": res_pl[res_pl["modelo"] == m].sort_values("puesto")["grupo"].tolist()}
            for m in MODELOS},
    }
    (salida / "resumen_interpretacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    carpeta_fig = salida / "figuras"
    carpeta_fig.mkdir(exist_ok=True)
    figura(res_ev, res_pl, carpeta_fig, None if a.sin_informe else RAIZ / "Informe" / "figuras")

    print(res_ev.sort_values(["modelo", "puesto"]).to_string(index=False))
    print(res_pl.sort_values(["modelo", "puesto"]).to_string(index=False))
    print(perfil.round(1).to_string())
    print(json.dumps({k: resumen[k] for k in ("cotejo_con_45", "eda",
                                              "perfil_evaluacion_viernes_sobre_domingo_pct",
                                              "respuesta_al_festivo_en_entrenamiento")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
