#!/usr/bin/env python3
"""Genera las páginas del tablero de Power BI en formato PBIR (#106).

El tablero vive en `powerbi/` como proyecto de Power BI (`.pbip`):

* `Tablero-DelitosBOG.SemanticModel/` — el modelo en TMDL: tablas, relaciones y medidas. Lee las
  hojas de `outputs/powerbi/` en la copia local del repositorio (parámetro `RutaRepo`).
* `Tablero-DelitosBOG.Report/` — las páginas. Las escribe **este script**, de modo que el diseño
  también es código: cambiar un visual es cambiar una línea aquí y volver a ejecutar.

Nada de lo que se dibuja trae cifras escritas a mano: todos los visuales usan las medidas del modelo.

Uso::

    python scripts/generar_reporte_powerbi.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PBIP = RAIZ / "powerbi"
NOMBRE = "Tablero-DelitosBOG"
REPORTE = PBIP / f"{NOMBRE}.Report"
DEF = REPORTE / "definition"

ESQ = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
W, H = 1280, 720

# Paleta: fondo azul noche y una escala de calor (amarillo → rojo) para lo que mide hurto.
FONDO, PANEL, BORDE = "#0F172A", "#1E293B", "#334155"
TEXTO, TEXTO_2 = "#F1F5F9", "#94A3B8"
CALOR = ("#FDE68A", "#F97316", "#B91C1C")
ACENTO = "#F97316"


# ---------------------------------------------------------------- expresiones del lenguaje de consulta
def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def color(hexa):
    return {"solid": {"color": lit(hexa)}}


def col(tabla, columna):
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": columna}}


def med(nombre):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": nombre}}


def ref(campo):
    k = next(iter(campo))
    return f"{campo[k]['Expression']['SourceRef']['Entity']}.{campo[k]['Property']}"


def proy(campo, nombre=None):
    if "Aggregation" in campo:
        q, n = _ref_agregada(campo)
        p = {"field": campo, "queryRef": q, "nativeQueryRef": n}
    else:
        p = {"field": campo, "queryRef": ref(campo), "nativeQueryRef": campo[next(iter(campo))]["Property"]}
    if nombre:
        p["displayName"] = nombre
    return p


def gradiente(campo):
    """Relleno condicional de calor: mínimo amarillo, medio naranja, máximo rojo."""
    return {"solid": {"color": {"expr": {"FillRule": {
        "Input": campo,
        "FillRule": {"linearGradient3": {
            "min": {"color": {"Literal": {"Value": f"'{CALOR[0]}'"}}},
            "mid": {"color": {"Literal": {"Value": f"'{CALOR[1]}'"}}},
            "max": {"color": {"Literal": {"Value": f"'{CALOR[2]}'"}}},
            "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}},
        }}}}}}}


def selector_todos(campo):
    return {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref(campo)}


def filtro_en(tabla, columna, valores, nombre):
    def v(x):
        return [{"Literal": {"Value": f"{x}L" if isinstance(x, int) else "'" + x + "'"}}]
    return {"name": nombre, "field": col(tabla, columna), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": tabla, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}},
                                                       "Property": columna}}],
                           "Values": [v(x) for x in valores]}}}]},
            "howCreated": "User"}


# ---------------------------------------------------------------- visuales
class Pagina:
    def __init__(self, nombre, titulo, subtitulo):
        self.nombre, self.titulo, self.subtitulo = nombre, titulo, subtitulo
        self.visuales: list[dict] = []

    def _id(self, etiqueta):
        return hashlib.sha1(f"{self.nombre}/{etiqueta}".encode()).hexdigest()[:20]

    def agregar(self, etiqueta, tipo, x, y, w, h, roles=None, objetos=None, titulo=None,
                contenedor=None, orden=None, filtros=None, panel=True):
        vc = contenedor or {}
        if titulo is not None:
            vc["title"] = [{"properties": {"show": lit(True), "text": lit(titulo),
                                           "fontColor": color(TEXTO), "fontSize": lit(11.0)}}]
        if panel:
            vc.setdefault("background", [{"properties": {"show": lit(True), "color": color(PANEL),
                                                         "transparency": lit(0.0)}}])
            vc.setdefault("border", [{"properties": {"show": lit(True), "color": color(BORDE),
                                                     "radius": lit(10.0)}}])
        visual = {"visualType": tipo, "drillFilterOtherVisuals": True}
        if roles:
            qs = {rol: {"projections": [proy(*c) if isinstance(c, tuple) else proy(c) for c in campos]}
                  for rol, campos in roles.items()}
            visual["query"] = {"queryState": qs}
            if orden:
                campo, dirr = orden
                visual["query"]["sortDefinition"] = {
                    "sort": [{"field": campo, "direction": dirr}], "isDefaultSort": False}
        if objetos:
            visual["objects"] = objetos
        if vc:
            visual["visualContainerObjects"] = vc
        v = {"$schema": f"{ESQ}/visualContainer/1.0.0/schema.json", "name": self._id(etiqueta),
             "position": {"x": x, "y": y, "z": len(self.visuales) * 1000, "width": w, "height": h,
                          "tabOrder": len(self.visuales) * 1000},
             "visual": visual}
        if filtros:
            v["filterConfig"] = {"filters": filtros}
        self.visuales.append(v)
        return v

    # -- piezas reutilizables
    def texto(self, etiqueta, x, y, w, h, parrafos):
        pars = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{tam}pt", "color": c,
                                                           **({"fontWeight": "bold"} if neg else {})}}]}
                for t, tam, c, neg in parrafos]
        self.agregar(etiqueta, "textbox", x, y, w, h, panel=False,
                     objetos={"general": [{"properties": {"paragraphs": pars}}]},
                     contenedor={"background": [{"properties": {"show": lit(False)}}],
                                 "border": [{"properties": {"show": lit(False)}}]})

    def encabezado(self, con_filtro=True):
        self.texto("titulo", 20, 10, 760, 60, [
            (self.titulo, 20, TEXTO, True), (self.subtitulo, 10, TEXTO_2, False)])
        if con_filtro:
            self.agregar("filtro_anio", "slicer", 1010, 12, 250, 58,
                         roles={"Values": [(col("dim_anio", "anio_texto"), "Año")]},
                         objetos={"data": [{"properties": {"mode": lit("Dropdown")}}],
                                  "header": [{"properties": {"show": lit(True), "fontColor": color(TEXTO_2),
                                                             "text": lit("Año  (* atípico · † truncado)")}}],
                                  "items": [{"properties": {"fontColor": color(TEXTO), "background": color(PANEL)}}],
                                  "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True)}}]})

    def tarjeta(self, etiqueta, x, y, w, h, medida, rotulo, color_valor=TEXTO):
        self.agregar(etiqueta, "card", x, y, w, h,
                     roles={"Values": [(med(medida), rotulo)]},
                     objetos={"labels": [{"properties": {"color": color(color_valor), "fontSize": lit(24.0)}}],
                              "categoryLabels": [{"properties": {"show": lit(True), "color": color(TEXTO_2),
                                                                 "fontSize": lit(10.0)}}]},
                     contenedor={"border": [{"properties": {"show": lit(True), "color": color(ACENTO),
                                                            "radius": lit(10.0)}}]})

    def fila_tarjetas(self, y, tarjetas, h=92):
        n = len(tarjetas)
        ancho = (W - 40 - (n - 1) * 12) / n
        for i, (medida, rotulo, *c) in enumerate(tarjetas):
            self.tarjeta(f"kpi_{i}", round(20 + i * (ancho + 12)), y, round(ancho), h, medida, rotulo,
                         *(c or []))


def ejes():
    return {"categoryAxis": [{"properties": {"labelColor": color(TEXTO_2), "showAxisTitle": lit(False)}}],
            "valueAxis": [{"properties": {"labelColor": color(TEXTO_2), "gridlineColor": color(BORDE),
                                          "showAxisTitle": lit(False)}}],
            "legend": [{"properties": {"labelColor": color(TEXTO_2), "position": lit("Top")}}]}


def con_etiquetas(obj, formato=None):
    obj = dict(obj)
    obj["labels"] = [{"properties": {"show": lit(True), "color": color(TEXTO), "fontSize": lit(9.0)}}]
    return obj


# ---------------------------------------------------------------- páginas
def pagina_panorama():
    p = Pagina("panorama", "Hurto a personas en Bogotá",
               "Panorama 2020–2025 · Policía Nacional (registro de víctimas). Serie hasta el 31-oct-2025")
    p.encabezado()
    p.fila_tarjetas(80, [("Víctimas", "Víctimas registradas"), ("Media diaria", "Víctimas por día"),
                         ("Var. media diaria vs año anterior", "Variación vs año anterior"),
                         ("Máximo diario", "Día con más víctimas"),
                         ("Efecto festivo %", "Lunes festivo vs laborable"),
                         ("Registros Policía auditados", "Registros auditados (mín. 500.000)")])
    p.agregar("serie_mensual", "lineChart", 20, 184, 820, 262,
              titulo="Víctimas por día, mes a mes",
              roles={"Category": [(col("dim_periodo", "fecha_mes"), "Mes")],
                     "Y": [(med("Media diaria"), "Víctimas por día")]},
              objetos={**ejes(), "dataPoint": [{"properties": {"fill": color(ACENTO)}}],
                       "lineStyles": [{"properties": {"strokeWidth": lit(3)}}]})
    p.agregar("tipo_dia", "donutChart", 852, 184, 408, 262,
              titulo="¿Qué tipo de día? Reparto de las víctimas",
              roles={"Category": [(col("dim_calendario", "tipo_dia"), "Tipo de día")],
                     "Y": [(med("Víctimas"), "Víctimas")]},
              objetos={"legend": [{"properties": {"show": lit(True), "labelColor": color(TEXTO_2),
                                                  "position": lit("Bottom")}}],
                       "labels": [{"properties": {"color": color(TEXTO), "labelStyle": lit("Category, percent of total")}}]})
    p.agregar("dia_semana", "clusteredColumnChart", 20, 458, 410, 246,
              titulo="Perfil semanal: víctimas por día",
              roles={"Category": [(col("dim_calendario", "dia_semana"), "Día")],
                     "Y": [(med("Media diaria"), "Víctimas por día")]},
              orden=(col("dim_calendario", "dia_semana"), "Ascending"),
              objetos=con_etiquetas({**ejes(), "dataPoint": [
                  {"properties": {"fill": gradiente(med("Media diaria"))},
                   "selector": selector_todos(med("Media diaria"))}]}))
    p.agregar("por_anio", "clusteredBarChart", 442, 458, 410, 246,
              titulo="Media diaria por año (se compara la media, no el total)",
              roles={"Category": [(col("dim_anio", "anio_texto"), "Año")],
                     "Y": [(med("Media diaria"), "Víctimas por día")]},
              orden=(col("dim_anio", "anio_texto"), "Ascending"),
              objetos=con_etiquetas({**ejes(), "dataPoint": [
                  {"properties": {"fill": gradiente(med("Media diaria"))},
                   "selector": selector_todos(med("Media diaria"))}]}),
              filtros=[filtro_en("dim_anio", "anio", [2020, 2021, 2022, 2023, 2024, 2025], "f_anios_serie")])
    p.agregar("tabla_anios", "tableEx", 864, 458, 396, 246,
              titulo="Total y media diaria, lado a lado",
              roles={"Values": [(col("dim_anio", "anio_texto"), "Año"), (med("Víctimas"), "Total"),
                                (med("Media diaria"), "Por día"), (med("Días con datos"), "Días"),
                                (col("dim_anio", "nota_anio"), "Lectura")]},
              objetos={"columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE)}}],
                       "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(PANEL),
                                                  "fontColorSecondary": color(TEXTO), "backColorSecondary": color(FONDO)}}],
                       "total": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE)}}]},
              filtros=[filtro_en("dim_anio", "anio", [2020, 2021, 2022, 2023, 2024, 2025], "f_anios_tabla")])
    return p


def pagina_territorio():
    p = Pagina("territorio", "Mapa de calor del hurto por localidad",
               "Llamadas de hurto a la Línea 123 por 100.000 habitantes (personas-año, SDP). "
               "Se colorea la tasa, no el conteo")
    p.encabezado()
    p.fila_tarjetas(80, [("Llamadas 123", "Llamadas de hurto (Línea 123)"),
                         ("Tasa ciudad por 100k", "Tasa de la ciudad por 100.000 hab."),
                         ("Peso 10 primeras UPZ %", "Peso de las 10 UPZ con más llamadas"),
                         ("UPZ con llamadas", "UPZ con llamadas")])
    tasa = med("Tasa 123 por 100k")
    p.agregar("mapa_calor", "azureMap", 20, 184, 620, 520,
              titulo="Mapa de calor: tasa por localidad (área urbana)",
              roles={"Category": [(col("dim_localidad", "localidad"), "Localidad")],
                     "Y": [(col("dim_localidad", "latitud"), "Latitud")],
                     "X": [(col("dim_localidad", "longitud"), "Longitud")],
                     "Size": [(tasa, "Tasa por 100.000")],
                     "Tooltips": [(med("Llamadas 123"), "Llamadas"), (med("Puesto por tasa"), "Puesto por tasa"),
                                  (med("Puesto por conteo"), "Puesto por conteo"),
                                  (col("dim_localidad", "lectura"), "Lectura")]},
              objetos={"heatMapLayer": [{"properties": {
                           "show": lit(True), "heatMapUseSize": lit(True), "heatMapRadius": lit(1500.0),
                           "heatMapRadiusUnit": lit("meters"), "heatMapIntensity": lit(1.0),
                           "heatMapColorLow": color(CALOR[0]), "heatMapColorCenter": color(CALOR[1]),
                           "heatMapColorHigh": color(CALOR[2]), "mapTransparency": lit(25.0)}}],
                       "bubbleLayer": [{"properties": {"show": lit(True), "bubbleRadius": lit(6.0),
                                                       "minBubbleRadius": lit(4.0), "maxRadius": lit(18.0),
                                                       "mapTransparency": lit(10.0)}}],
                       "dataPoint": [{"properties": {"fill": gradiente(tasa)}, "selector": selector_todos(tasa)}],
                       "categoryLabels": [{"properties": {"show": lit(True), "color": color("#0F172A"),
                                                          "fontSize": lit(8.0)}}],
                       "mapControls": [{"properties": {"autoZoom": lit(True), "defaultStyle": lit("grayscale_dark"),
                                                       "showNavigationControls": lit(True)}}],
                       "legend": [{"properties": {"show": lit(False)}}]},
              filtros=[filtro_en("dim_localidad", "en_mapa_urbano", [1], "f_urbano")])
    p.agregar("matriz_calor", "pivotTable", 652, 184, 608, 300,
              titulo="Matriz de calor: tasa por localidad y año",
              roles={"Rows": [(col("dim_localidad", "localidad"), "Localidad")],
                     "Columns": [(col("dim_anio", "anio"), "Año")],
                     "Values": [(tasa, "Tasa")]},
              objetos={"values": [{"properties": {"backColor": gradiente(tasa), "fontColorPrimary": color("#0F172A")},
                                   "selector": selector_todos(tasa)},
                                  {"properties": {"fontColorPrimary": color("#0F172A"), "fontSize": lit(8.0)}}],
                       "columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE)}}],
                       "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(PANEL), "fontSize": lit(8.0)}}],
                       "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}]},
              filtros=[filtro_en("dim_anio", "anio", [2020, 2021, 2022, 2023, 2024, 2025], "f_anios_pob")])
    p.agregar("barras_tasa", "clusteredBarChart", 652, 496, 300, 208,
              titulo="Tasa por 100.000 hab. (orden de la tasa)",
              roles={"Category": [(col("dim_localidad", "localidad"), "Localidad")], "Y": [(tasa, "Tasa")]},
              orden=(tasa, "Descending"),
              objetos={**ejes(), "dataPoint": [{"properties": {"fill": gradiente(tasa)}, "selector": selector_todos(tasa)}]})
    p.agregar("dona_lectura", "donutChart", 964, 496, 296, 208,
              titulo="Llamadas según el tipo de localidad",
              roles={"Category": [(col("dim_localidad", "lectura"), "Tipo")], "Y": [(med("Llamadas 123"), "Llamadas")]},
              objetos={"legend": [{"properties": {"show": lit(True), "labelColor": color(TEXTO_2), "position": lit("Bottom")}}],
                       "labels": [{"properties": {"color": color(TEXTO), "labelStyle": lit("Percent of total")}}]})
    p.texto("nota_mapa", 24, 676, 612, 24, [(
        "Sumapaz (rural) y «SIN LOCALIZACION» quedan fuera del mapa. Kennedy es 1.ª por conteo y 13.ª por tasa.",
        8, TEXTO_2, False)])
    return p


def pagina_fuentes():
    p = Pagina("fuentes", "Fuentes y calidad de los datos",
               "Cada fuente mide algo distinto: se comparan por índice (media mensual = 100) y nunca se suman")
    p.encabezado()
    p.fila_tarjetas(80, [("Registros Policía auditados", "Registros Policía (2020–2025)"),
                         ("Fuentes que sostienen el mínimo", "Fuentes con ≥ 500.000 registros"),
                         ("Media diaria periodo completo", "Víctimas por día (periodo completo)")])
    p.agregar("indice_fuentes", "lineChart", 20, 184, 820, 300,
              titulo="Índice mensual por fuente (media comparable = 100)",
              roles={"Category": [(col("dim_periodo", "fecha_mes"), "Mes")],
                     "Series": [(col("fact_fuentes_mensual", "fuente"), "Fuente")],
                     "Y": [(med("Índice de la fuente"), "Índice")]},
              objetos=ejes(),
              filtros=[filtro_en("dim_periodo", "comparable", ["sí"], "f_comparable")])
    p.agregar("embudo", "funnel", 852, 184, 408, 300,
              titulo="Embudo del preprocesamiento (Policía)",
              roles={"Category": [(col("qa_embudo", "paso"), "Paso")],
                     "Y": [({"Aggregation": {"Expression": col("qa_embudo", "filas_despues"), "Function": 0}},
                            "Filas")]},
              objetos={"dataPoint": [{"properties": {"fill": color(ACENTO)}}],
                       "labels": [{"properties": {"color": color(TEXTO)}}],
                       "categoryAxis": [{"properties": {"color": color(TEXTO_2)}}]},
              filtros=[filtro_en("qa_embudo", "fuente", ["policia_registro"], "f_policia")])
    tabla_obj = {"columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE)}}],
                 "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(PANEL),
                                            "fontColorSecondary": color(TEXTO), "backColorSecondary": color(FONDO),
                                            "wordWrap": lit(True)}}]}
    p.agregar("tabla_fuentes", "tableEx", 20, 496, 620, 208, titulo="Las cuatro fuentes",
              roles={"Values": [(col("dim_fuente", "fuente"), "Fuente"),
                                (col("dim_fuente", "unidad_observacion"), "Unidad de observación"),
                                (col("dim_fuente", "filas_auditadas"), "Filas auditadas"),
                                (col("dim_fuente", "sostiene_el_minimo"), "≥ 500.000"),
                                (col("dim_fuente", "es_la_serie_objetivo"), "Serie objetivo")]},
              objetos=tabla_obj)
    p.agregar("tabla_reglas", "tableEx", 652, 496, 608, 208, titulo="Reglas de lectura del tablero",
              roles={"Values": [(col("qa_reglas", "regla"), "Regla"), (col("qa_reglas", "por_que"), "Por qué")]},
              objetos=tabla_obj)
    return p


def pagina_modelado():
    p = Pagina("modelado", "Pronóstico: la barra a batir",
               "Comparadores de referencia sobre los últimos 184 días y validación rodante (6 pliegues)")
    p.encabezado(con_filtro=False)
    p.fila_tarjetas(80, [("Barra MAE", "MAE de la barra (víctimas/día)"),
                         ("Mejor comparador", "Mejor comparador"),
                         ("MASE de la barra", "MASE de la barra")])
    mae = {"Aggregation": {"Expression": col("fact_comparadores", "MAE"), "Function": 3}}
    p.agregar("mae_comparador", "clusteredBarChart", 20, 184, 500, 300,
              titulo="MAE por comparador (menor es mejor)",
              roles={"Category": [(col("fact_comparadores", "comparador"), "Comparador")], "Y": [(mae, "MAE")]},
              orden=(mae, "Ascending"),
              objetos=con_etiquetas({**ejes(), "dataPoint": [{"properties": {"fill": color(ACENTO)}}]}))
    p.agregar("pliegues", "lineChart", 532, 184, 728, 300,
              titulo="MAE por pliegue de validación rodante: el orden no es estable",
              roles={"Category": [(col("fact_validacion_rodante", "fin_evaluacion"), "Fin de la evaluación")],
                     "Series": [(col("fact_validacion_rodante", "comparador"), "Comparador")],
                     "Y": [(med("MAE pliegue"), "MAE")]},
              objetos=ejes())
    p.agregar("tabla_metricas", "tableEx", 20, 496, 1240, 208, titulo="Métricas de evaluación final",
              roles={"Values": [(col("fact_comparadores", "comparador"), "Comparador"),
                                ({"Aggregation": {"Expression": col("fact_comparadores", "MAE"), "Function": 3}}, "MAE"),
                                ({"Aggregation": {"Expression": col("fact_comparadores", "RMSE"), "Function": 3}}, "RMSE"),
                                ({"Aggregation": {"Expression": col("fact_comparadores", "MAPE"), "Function": 3}}, "MAPE %"),
                                ({"Aggregation": {"Expression": col("fact_comparadores", "MASE"), "Function": 3}}, "MASE")]},
              objetos={"columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE)}}],
                       "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(PANEL),
                                                  "fontColorSecondary": color(TEXTO), "backColorSecondary": color(FONDO)}}]})
    return p


# ---------------------------------------------------------------- escritura
def _ref_agregada(campo):
    """queryRef de una agregación: Min(tabla.col)."""
    a = campo["Aggregation"]
    funcs = {0: "Sum", 1: "Avg", 3: "Min", 4: "Max"}
    c = a["Expression"]["Column"]
    return f"{funcs[a['Function']]}({c['Expression']['SourceRef']['Entity']}.{c['Property']})", c["Property"]


def _corregir_agregados(nodo):
    if isinstance(nodo, dict):
        if "field" in nodo and "queryRef" in nodo and "Aggregation" in nodo["field"]:
            nodo["queryRef"], nodo["nativeQueryRef"] = _ref_agregada(nodo["field"])
        for v in nodo.values():
            _corregir_agregados(v)
    elif isinstance(nodo, list):
        for v in nodo:
            _corregir_agregados(v)


def tema():
    return {
        "name": "TemaDelitosBOG",
        "dataColors": [ACENTO, "#38BDF8", "#A78BFA", "#FACC15", "#F43F5E", "#34D399", "#94A3B8", "#E879F9"],
        "background": FONDO, "foreground": TEXTO, "tableAccent": ACENTO,
        "good": "#34D399", "neutral": "#FACC15", "bad": "#F43F5E",
        "maximum": CALOR[2], "center": CALOR[1], "minimum": CALOR[0],
        "textClasses": {
            "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": TEXTO},
            "title": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
            "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
            "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": TEXTO_2}},
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": {"solid": {"color": PANEL}}, "transparency": 0}],
                "border": [{"show": True, "color": {"solid": {"color": BORDE}}, "radius": 10}],
                "title": [{"fontColor": {"solid": {"color": TEXTO}}, "fontSize": 11}],
                "categoryAxis": [{"labelColor": {"solid": {"color": TEXTO_2}}}],
                "valueAxis": [{"labelColor": {"solid": {"color": TEXTO_2}},
                               "gridlineColor": {"solid": {"color": BORDE}}}],
                "legend": [{"labelColor": {"solid": {"color": TEXTO_2}}}],
                "visualHeader": [{"background": {"solid": {"color": PANEL}},
                                  "foreground": {"solid": {"color": TEXTO_2}}}]}},
            "page": {"*": {"background": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}],
                           "outspace": [{"color": {"solid": {"color": "#0B1220"}}, "transparency": 0}]}},
            "textbox": {"*": {"background": [{"show": False}], "border": [{"show": False}]}},
        },
    }


def tema_base() -> Path:
    """El tema base de Power BI Desktop instalado (CY24SU10)."""
    import glob
    candidatos = glob.glob(r"C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_*\bin"
                           r"\WebView2Resources\minerva\sharedresources\BaseThemes\CY24SU10.json")
    return Path(sorted(candidatos)[-1]) if candidatos else None


def escribir(ruta: Path, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if DEF.exists():
        shutil.rmtree(DEF)
    paginas = [pagina_panorama(), pagina_territorio(), pagina_fuentes(), pagina_modelado()]

    escribir(REPORTE / "definition.pbir",
             {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}}})
    escribir(DEF / "version.json", {"$schema": f"{ESQ}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    escribir(DEF / "report.json", {
        "$schema": f"{ESQ}/report/1.0.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59", "type": "SharedResources"},
            "customTheme": {"name": "TemaDelitosBOG.json", "reportVersionAtImport": "5.59",
                            "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "TemaDelitosBOG.json", "path": "TemaDelitosBOG.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True}})
    escribir(DEF / "pages" / "pages.json", {"$schema": f"{ESQ}/pagesMetadata/1.0.0/schema.json",
                                            "pageOrder": [p.nombre for p in paginas],
                                            "activePageName": paginas[0].nombre})
    for p in paginas:
        escribir(DEF / "pages" / p.nombre / "page.json", {
            "$schema": f"{ESQ}/page/1.0.0/schema.json", "name": p.nombre, "displayName": {
                "panorama": "Panorama", "territorio": "Territorio", "fuentes": "Fuentes y calidad",
                "modelado": "Modelado"}[p.nombre],
            "displayOption": "FitToPage", "height": H, "width": W,
            "objects": {"background": [{"properties": {"color": color(FONDO), "transparency": lit(0.0)}}],
                        "outspace": [{"properties": {"color": color("#0B1220"), "transparency": lit(0.0)}}]}})
        for v in p.visuales:
            _corregir_agregados(v)
            escribir(DEF / "pages" / p.nombre / "visuals" / v["name"] / "visual.json", v)

    estaticos = REPORTE / "StaticResources"
    escribir(estaticos / "RegisteredResources" / "TemaDelitosBOG.json", tema())
    base = tema_base()
    destino = estaticos / "SharedResources" / "BaseThemes" / "CY24SU10.json"
    if base:
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base, destino)
    elif not destino.exists():
        raise SystemExit("No se encontró el tema base CY24SU10 de Power BI Desktop")

    escribir(PBIP / f"{NOMBRE}.pbip", {
        "version": "1.0", "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}],
        "settings": {"enableAutoRecovery": True}})
    escribir(PBIP / f"{NOMBRE}.SemanticModel" / "definition.pbism", {"version": "4.2", "settings": {}})
    n = sum(len(p.visuales) for p in paginas)
    print(f"{len(paginas)} páginas y {n} visuales en {REPORTE.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
