#!/usr/bin/env python3
"""Extrae de `outputs/` las cifras que usa la presentación y las escribe en `src/data/generado/`.

Ninguna cifra de las diapositivas se escribe a mano: los gráficos leen estos JSON, y este script solo
lee archivos versionados del repositorio. Se ejecuta desde la carpeta `presentacion/`:

    python scripts/preparar_datos.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
OUT = RAIZ / "outputs"
DEST = Path(__file__).resolve().parents[1] / "src" / "data" / "generado"

# Modelos finales del informe (tabla tab:resultados): #45 para SARIMA, ETS y árboles; #144 para la regresión.
FINALES = {
    "gradiente_histogramas": ("#45", "Gradiente por histogramas", "arboles"),
    "ets": ("#45", "ETS", "estadistico"),
    "sarima": ("#45", "SARIMA", "estadistico"),
    "bosque_aleatorio": ("#45", "Bosque aleatorio", "arboles"),
    "regresion_lineal": ("#144", "Regresión lineal", "regresion"),
}
COMPARADORES = {
    "ingenuo_estacional": "Ingenuo estacional (barra)",
    "media_movil_7": "Media móvil de 7 días",
    "ingenuo": "Ingenuo",
    "media_movil_28": "Media móvil de 28 días",
}


def r(x, n=2):
    return None if pd.isna(x) else round(float(x), n)


def guardar(nombre: str, obj) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / f"{nombre}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito", nombre)


def serie() -> None:
    s = pd.read_csv(OUT / "powerbi" / "fact_serie_diaria.csv", parse_dates=["fecha"])
    mensual = (s.groupby(s["fecha"].dt.to_period("M"))["victimas"].mean().reset_index())
    eda = json.loads((OUT / "eda" / "resumen_eda.json").read_text(encoding="utf-8"))
    t = eda["temporal"]
    guardar("serie", {
        "dias": int(len(s)),
        "victimas": int(s["victimas"].sum()),
        "inicio": s["fecha"].min().date().isoformat(),
        "fin": s["fecha"].max().date().isoformat(),
        "media": r(s["victimas"].mean(), 1),
        "mensual": [{"mes": str(p), "media": r(v, 1)} for p, v in zip(mensual["fecha"], mensual["victimas"])],
        "anual": [{"anio": int(k), "media": r(v["media_diaria"], 1), "victimas": int(v["victimas"]),
                   "dias": int(v["dias"]), "completo": bool(v["anio_completo"])} for k, v in t["anual"].items()],
        "dia_semana": [{"dia": k, "media": v} for k, v in t["por_dia_semana"].items()],
        "por_mes": [{"mes": k, "media": v} for k, v in t["por_mes"].items()],
        "festivos": t["festivos"],
    })


def auditoria() -> None:
    e = pd.read_csv(OUT / "powerbi" / "qa_embudo.csv")
    p = e[e["fuente"] == "policia_registro"]
    guardar("embudo", [{"paso": a, "filas": int(b), "motivo": m}
                       for a, b, m in zip(p["paso"], p["filas_despues"], p["motivo"])])


def fuentes() -> None:
    f = pd.read_csv(OUT / "powerbi" / "fact_fuentes_mensual.csv")
    f = f[(f["anio"] >= 2020) & (f["fuente"] != "MinDefensa (agregado)")]
    ancho = f.pivot_table(index="fecha", columns="fuente", values="valor").sort_index()
    ancho = ancho.loc[ancho.index <= "2025-10"]
    # Índice: cada fuente dividida por su media del periodo común (100 = su media). No se suman.
    comunes = ancho.dropna()
    indice = (ancho / comunes.mean() * 100).round(1)
    corr = pd.read_csv(OUT / "eda" / "fuentes_correlacion_pearson.csv", index_col=0)
    sin20 = pd.read_csv(OUT / "eda" / "fuentes_correlacion_pearson_sin_2020.csv", index_col=0)
    guardar("fuentes", {
        "meses": int(len(comunes)),
        "serie": [{"mes": m, **{k: (None if pd.isna(v) else float(v)) for k, v in fila.items()}}
                  for m, fila in indice.iterrows()],
        "correlaciones": {
            "policia_fiscalia": r(corr.loc["Policía (víctimas)", "Fiscalía (proceso–delito)"], 3),
            "policia_linea123": r(corr.loc["Policía (víctimas)", "Línea 123 (llamadas)"], 3),
            "policia_linea123_sin2020": r(sin20.loc["Policía (víctimas)", "Línea 123 (llamadas)"], 3),
        },
    })


def territorio() -> None:
    t = pd.read_csv(OUT / "eda" / "territorial_tasas.csv")
    t["puesto_conteo"] = t["incidentes"].rank(ascending=False, method="min").astype(int)
    t["puesto_tasa"] = t["tasa_100k_periodo"].rank(ascending=False, method="min").astype(int)
    t = t.sort_values("puesto_tasa")
    guardar("territorio", [{"localidad": l, "incidentes": int(i), "tasa": r(ta, 1), "puesto_conteo": int(pc),
                            "puesto_tasa": int(pt)} for l, i, ta, pc, pt in
                           zip(t["localidad"], t["incidentes"], t["tasa_100k_periodo"], t["puesto_conteo"],
                               t["puesto_tasa"])])


def modelos() -> None:
    tc = pd.read_csv(OUT / "modelado" / "comparacion" / "tabla_comparativa.csv")
    tc = tc[~tc["sensibilidad"]]
    filas = []
    for m, (origen, nombre, familia) in FINALES.items():
        x = tc[(tc["modelo"] == m) & (tc["origen"] == origen)].iloc[0]
        filas.append({"id": m, "nombre": nombre, "familia": familia, "MAE": r(x.MAE), "RMSE": r(x.RMSE),
                      "MAPE": r(x.MAPE), "MASE": r(x.MASE, 3), "delta_pct": r(x.MAE_vs_barra_pct, 1),
                      "p": float(x.p_DM_abs), "mae_medio_pliegues": r(x.MAE_medio_pliegues),
                      "desv_pliegues": r(x.MAE_desv_pliegues), "peor_pliegue": r(x.MAE_peor_pliegue),
                      "pliegues_ganados": int(x.pliegues_ganados_a_barra)})
    for m, nombre in COMPARADORES.items():
        x = tc[tc["modelo"] == m].iloc[0]
        filas.append({"id": m, "nombre": nombre, "familia": "comparador", "MAE": r(x.MAE), "RMSE": r(x.RMSE),
                      "MAPE": r(x.MAPE), "MASE": r(x.MASE, 3), "delta_pct": r(x.MAE_vs_barra_pct, 1),
                      "p": None if pd.isna(x.p_DM_abs) else float(x.p_DM_abs),
                      "mae_medio_pliegues": r(x.MAE_medio_pliegues), "desv_pliegues": r(x.MAE_desv_pliegues),
                      "peor_pliegue": r(x.MAE_peor_pliegue), "pliegues_ganados": None})

    # MAE por pliegue de los cinco modelos finales y de la barra
    mp = pd.read_csv(OUT / "modelado" / "comparacion" / "mae_por_pliegue.csv")
    pliegues = []
    for k in range(1, 7):
        fila = {"pliegue": k}
        for m, (origen, _, _) in FINALES.items():
            fila[m] = r(mp[(mp.modelo == m) & (mp.origen == origen) & (mp.pliegue == k)]["MAE"].iloc[0])
        fila["barra"] = r(mp[(mp.modelo == "ingenuo_estacional") & (mp.pliegue == k)]["MAE"].iloc[0])
        pliegues.append(fila)

    # Comparadores en los pliegues (tabla tab:pliegues-mae)
    vr = pd.read_csv(OUT / "baselines" / "validacion_rodante.csv")

    dm = pd.read_csv(OUT / "modelado" / "comparacion" / "diebold_mariano_entre_modelos.csv")
    ep = pd.read_csv(OUT / "modelado" / "comparacion" / "errores_por_periodo.csv")
    fest = []
    for m, (origen, nombre, _) in list(FINALES.items()) + [("ingenuo_estacional", ("#42", "Ingenuo estacional (barra)", ""))]:
        q = ep[(ep.dimension == "tipo_dia") & (ep.modelo == m) & (ep.origen == origen)]
        f1 = q[q.valor == "festivo"].iloc[0]
        f0 = q[q.valor == "no festivo"].iloc[0]
        fest.append({"nombre": nombre, "mae_festivo": r(f1.MAE), "sesgo_festivo": r(f1.sesgo),
                     "mae_no_festivo": r(f0.MAE), "sesgo_no_festivo": r(f0.sesgo)})
    guardar("modelos", {
        "tabla": filas,
        "pliegues": pliegues,
        "comparadores_pliegues": json.loads(vr.to_json(orient="records", force_ascii=False)),
        "dm": [{"a": a, "b": b, "p_hln": float(c), "p_nw": float(d)} for a, b, c, d in
               zip(dm.modelo_a, dm.modelo_b, dm.p_DM_abs, dm.p_DM_abs_HAC7)],
        "festivos": fest,
    })


def pronostico() -> None:
    p = pd.read_csv(OUT / "modelado" / "ajuste" / "predicciones_por_pliegue.csv")
    p = p[p.pliegue == "final"]
    reg = pd.read_csv(OUT / "modelado" / "regresion" / "predicciones_por_pliegue.csv")
    reg = reg[(reg.pliegue == "final") & (reg.modelo == "regresion_lineal")]
    s = pd.read_csv(OUT / "powerbi" / "fact_serie_diaria.csv")
    base = p[p.modelo == "gradiente_histogramas"][["fecha", "real"]].copy()
    for m in ["gradiente_histogramas", "ets", "sarima", "bosque_aleatorio"]:
        base = base.merge(p[p.modelo == m][["fecha", "prediccion"]].rename(columns={"prediccion": m}), on="fecha")
    base = base.merge(reg[["fecha", "prediccion"]].rename(columns={"prediccion": "regresion_lineal"}), on="fecha")
    base = base.merge(s[["fecha", "rezago_7", "festivo"]].rename(columns={"rezago_7": "barra"}), on="fecha")
    assert len(base) == 184, len(base)
    guardar("pronostico", [{k: (v if k in ("fecha",) else (int(v) if k == "festivo" else r(v, 1)))
                            for k, v in fila.items()} for fila in base.to_dict("records")])


def interpretacion() -> None:
    g = pd.read_csv(OUT / "modelado" / "interpretacion" / "importancia_grupos_evaluacion.csv")
    nombres = {"rezago_1": "Rezago de 1 día", "dia_semana": "Día de la semana",
               "rezagos_semanales": "Rezagos de 7, 14 y 28 días", "festivos": "Festivos y puentes",
               "calendario_lento": "Año, mes y día del mes", "medias_previas": "Medias y desviaciones previas",
               "anio_2020": "Indicador de 2020"}
    filas = []
    for k, n in nombres.items():
        a = g[(g.modelo == "gradiente_histogramas") & (g.grupo == k)].iloc[0]
        b = g[(g.modelo == "bosque_aleatorio") & (g.grupo == k)].iloc[0]
        filas.append({"grupo": n, "gradiente": r(a.aumento_pct, 1), "bosque": r(b.aumento_pct, 1)})
    c = pd.read_csv(OUT / "modelado" / "regresion" / "coeficientes.csv")
    c = c[c.tipo != "intercepto"].copy()
    c["abs"] = c.coef_estandarizado.abs()
    top = c.sort_values("abs", ascending=False).head(8)
    ri = json.loads((OUT / "modelado" / "interpretacion" / "resumen_interpretacion.json").read_text(encoding="utf-8"))
    guardar("interpretacion", {
        "grupos": filas,
        "coeficientes": [{"variable": v, "tipo": t, "estandarizado": r(e, 2), "por_unidad": r(u, 3)}
                         for v, t, e, u in zip(top.variable, top.tipo, top.coef_estandarizado, top.coef_por_unidad)],
        "resumen": ri,
    })


if __name__ == "__main__":
    serie()
    auditoria()
    fuentes()
    territorio()
    modelos()
    pronostico()
    interpretacion()
