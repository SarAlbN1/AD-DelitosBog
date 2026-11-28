#!/usr/bin/env python3
"""Genera las páginas del tablero de Power BI en formato PBIR (#106).

El tablero vive en `powerbi/` como proyecto de Power BI (`.pbip`):

* `Tablero-DelitosBOG.SemanticModel/` — el modelo en TMDL: tablas, relaciones y medidas. Lee las
  hojas de `outputs/powerbi/` en la copia local del repositorio (parámetro `RutaRepo`).
* `Tablero-DelitosBOG.Report/` — las cuatro páginas (Panorama, ¿Cuándo?, ¿Dónde?, Pronóstico). Las escribe **este script**, de modo que el diseño
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
# Cada página tiene su propio color de acento, para que se distingan a simple vista.
FONDO, PANEL, BORDE = "#0B1120", "#131E36", "#2A3A5C"
TEXTO, TEXTO_2 = "#FFFFFF", "#CBD5E1"
PANEL_NOTA = "#1B2A4A"   # fondo de las notas: más claro que los paneles, para que el texto resalte
CALOR = ("#FDE68A", "#F97316", "#B91C1C")
ACENTO = "#F59E0B"
ACENTOS = {"panorama": "#F59E0B", "patrones": "#A78BFA", "territorio": "#F87171", "pronostico": "#22D3EE"}
# Colores fijos por familia de modelos y por fuente, iguales en todas las páginas.
COLOR_FAMILIA = {"Referencia": "#94A3B8", "Estadístico": "#A78BFA", "Árboles": "#22D3EE", "Regresión": "#F59E0B"}
COLOR_FUENTE = {"Policía (registro)": "#F59E0B", "Línea 123": "#F87171", "Fiscalía (Procesos V3)": "#A78BFA",
                "MinDefensa (agregado)": "#34D399"}


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


def colores_serie(campo, mapa):
    """Un color fijo para cada valor de una columna de serie (familia de modelos, fuente...)."""
    return [{"properties": {"fill": color(hexa)},
             "selector": {"data": [{"scopeId": {"Comparison": {
                 "ComparisonKind": 0, "Left": campo,
                 "Right": {"Literal": {"Value": "'" + valor.replace("'", "''") + "'"}}}}}]}}
            for valor, hexa in mapa.items()]


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
        self.acento = ACENTOS.get(nombre, ACENTO)
        self.visuales: list[dict] = []

    def _id(self, etiqueta):
        return hashlib.sha1(f"{self.nombre}/{etiqueta}".encode()).hexdigest()[:20]

    def agregar(self, etiqueta, tipo, x, y, w, h, roles=None, objetos=None, titulo=None,
                contenedor=None, orden=None, filtros=None, panel=True):
        vc = contenedor or {}
        if titulo is not None:
            # titleWrap: un título largo pasa a una segunda línea en vez de cortarse con «…».
            vc["title"] = [{"properties": {"show": lit(True), "text": lit(titulo), "titleWrap": lit(True),
                                           "fontColor": color(TEXTO), "fontSize": lit(13.0), "bold": lit(True)}}]
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
        self.agregar("barra_acento", "shape", 24, 16, 6, 56, panel=False,
                     objetos={"shape": [{"properties": {"tileShape": lit("rectangle")}}],
                              "fill": [{"properties": {"fillColor": color(self.acento), "transparency": lit(0.0)}}],
                              "outline": [{"properties": {"show": lit(False)}}]},
                     contenedor={"background": [{"properties": {"show": lit(False)}}],
                                 "border": [{"properties": {"show": lit(False)}}]})
        ancho = W - 24 - 40 - (300 if con_filtro else 0)
        self.texto("titulo", 40, 8, ancho, 72, [
            (self.titulo, 22, TEXTO, True), (self.subtitulo, 11, TEXTO_2, False)])
        if con_filtro:
            self.agregar("filtro_anio", "slicer", W - 24 - 277, 14, 277, 74,
                         roles={"Values": [(col("dim_anio", "anio_texto"), "Año")]},
                         objetos={"data": [{"properties": {"mode": lit("Dropdown")}}],
                                  "header": [{"properties": {"show": lit(True), "fontColor": color(TEXTO_2),
                                                             "text": lit("Año  (* atípico · † truncado)")}}],
                                  "items": [{"properties": {"fontColor": color(TEXTO), "background": color(PANEL)}}],
                                  "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True)}}]})

    def tarjeta(self, etiqueta, x, y, w, h, medida, rotulo, tam=28.0):
        """Una cifra clave. Los valores de texto largos (un nombre de modelo) usan letra más pequeña."""
        self.agregar(etiqueta, "card", x, y, w, h,
                     roles={"Values": [(med(medida), rotulo)]},
                     objetos={"labels": [{"properties": {"color": color(TEXTO), "fontSize": lit(float(tam))}}],
                              "categoryLabels": [{"properties": {"show": lit(True), "color": color(TEXTO_2),
                                                                 "fontSize": lit(12.0)}}],
                              "wordWrap": [{"properties": {"show": lit(True)}}]},
                     contenedor={"border": [{"properties": {"show": lit(True), "color": color(self.acento),
                                                            "radius": lit(10.0)}}]})

    def hallazgo(self, etiqueta, x, y, w, h, medida, titulo="Hallazgo", tam=14.0):
        """Una frase calculada por una medida: el dato convertido en información.

        El alto de cada hallazgo deja sitio para la frase completa: a 13 pt caben unos 7 px por carácter."""
        self.agregar(etiqueta, "card", x, y, w, h,
                     roles={"Values": [(med(medida), "Hallazgo")]},
                     objetos={"labels": [{"properties": {"color": color(TEXTO), "fontSize": lit(float(tam))}}],
                              "categoryLabels": [{"properties": {"show": lit(False)}}],
                              "wordWrap": [{"properties": {"show": lit(True)}}]},
                     contenedor={"background": [{"properties": {"show": lit(True), "color": color(PANEL_NOTA),
                                                                "transparency": lit(0.0)}}],
                                 "border": [{"properties": {"show": lit(True), "color": color(self.acento),
                                                            "radius": lit(10.0)}}],
                                 "title": [{"properties": {"show": lit(True), "text": lit("▶ " + titulo),
                                                           "fontColor": color(self.acento), "fontSize": lit(12.0),
                                                           "bold": lit(True)}}]})

    def fila_tarjetas(self, y, tarjetas, h=100, x0=24, ancho_total=None, sep=20, prefijo="kpi"):
        """Tarjetas en fila. Cada una es (medida, rótulo) o (medida, rótulo, tamaño de letra)."""
        n = len(tarjetas)
        total = ancho_total or (W - 2 * x0)
        ancho = (total - (n - 1) * sep) / n
        for i, (medida, rotulo, *tam) in enumerate(tarjetas):
            self.tarjeta(f"{prefijo}_{i}", round(x0 + i * (ancho + sep)), y, round(ancho), h, medida, rotulo,
                         tam=tam[0] if tam else 28.0)

    def columna_tarjetas(self, x, y, w, tarjetas, h=88, sep=16):
        """Tarjetas apiladas en una columna. Devuelve la y donde termina la última."""
        for i, (medida, rotulo, *tam) in enumerate(tarjetas):
            self.tarjeta(f"kpi_{i}", x, y + i * (h + sep), w, h, medida, rotulo, tam=tam[0] if tam else 28.0)
        return y + len(tarjetas) * (h + sep) - sep


def ejes():
    return {"categoryAxis": [{"properties": {"labelColor": color(TEXTO_2), "showAxisTitle": lit(False),
                                             "fontSize": lit(12.0)}}],
            "valueAxis": [{"properties": {"labelColor": color(TEXTO_2), "gridlineColor": color(BORDE),
                                          "showAxisTitle": lit(False), "fontSize": lit(12.0)}}],
            "legend": [{"properties": {"labelColor": color(TEXTO), "position": lit("Top"), "fontSize": lit(12.0)}}]}


def con_etiquetas(obj, formato=None):
    obj = dict(obj)
    obj["labels"] = [{"properties": {"show": lit(True), "color": color(TEXTO), "fontSize": lit(12.0)}}]
    return obj


# ---------------------------------------------------------------- páginas
# Rejilla: margen M, separación G. Filas fijas: encabezado, tarjetas, hallazgo y cuerpo.
M, G = 24, 20
Y_KPI, H_KPI = 84, 100
Y_HALL, H_HALL = Y_KPI + H_KPI + G, 72
Y_CUERPO = Y_HALL + H_HALL + G
H_CUERPO = H - M - Y_CUERPO
ANCHO = W - 2 * M


def columnas(*fracciones):
    """Reparte el ancho útil en columnas proporcionales: devuelve (x, ancho) de cada una."""
    util = ANCHO - G * (len(fracciones) - 1)
    total = sum(fracciones)
    x, out = M, []
    for f in fracciones:
        w = round(util * f / total)
        out.append((x, w))
        x += w + G
    return out


ANIOS_SERIE = [2020, 2021, 2022, 2023, 2024, 2025]


def barras_calor(medida):
    return {"dataPoint": [{"properties": {"fill": gradiente(med(medida))}, "selector": selector_todos(med(medida))}]}


def matriz_calor(medida, filas, columnas_):
    m = med(medida)
    return {"values": [{"properties": {"backColor": gradiente(m), "fontColorPrimary": color("#111827")},
                        "selector": selector_todos(m)},
                       {"properties": {"fontColorPrimary": color("#111827"), "fontSize": lit(12.0)}}],
            "columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE),
                                              "fontSize": lit(12.0)}}],
            "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(PANEL),
                                           "fontSize": lit(12.0)}}],
            "subTotals": [{"properties": {"rowSubtotals": lit(False), "columnSubtotals": lit(False)}}],
            "grid": [{"properties": {"rowPadding": lit(filas)}}]}


def color_medida(medida, hexa):
    """Color fijo de una serie que es una medida (por ejemplo, Observado frente a Pronóstico)."""
    return {"properties": {"fill": color(hexa)}, "selector": {"metadata": f"Medidas.{medida}"}}


# Cada página tiene su propia composición y ningún tipo de gráfico se repite entre páginas:
# Panorama (área y columnas), ¿Cuándo? (matriz de calor y anillo), ¿Dónde? (mapa, mapa de árbol y
# tabla) y Pronóstico (líneas y barras).
Y0 = 96                      # bajo el encabezado
H_UTIL = H - M - Y0          # alto útil del cuerpo


def pagina_panorama():
    p = Pagina("panorama", "Hurto a personas en Bogotá",
               "¿Cuánto hurto hay y hacia dónde va? · Policía Nacional, víctimas registradas 2020 – oct. 2025")
    p.encabezado()
    # Columna izquierda: cifras clave y cómo leerlas.
    wl = 270
    fin = p.columna_tarjetas(M, Y0, wl, [("Víctimas", "Víctimas registradas"),
                                          ("Media diaria", "Víctimas por día"),
                                          ("Var. media diaria vs año anterior", "Frente al año anterior"),
                                          ("Registros Policía auditados", "Registros auditados (mín. 500.000)", 24.0)],
                             h=100)
    p.hallazgo("aviso", M, fin + 16, wl, H - M - fin - 16, "Aviso de lectura", titulo="Cómo leerlo", tam=13.0)
    # Derecha: el hallazgo y la tendencia.
    xr = M + wl + G
    wr = W - M - xr
    p.hallazgo("hallazgo", xr, Y0, wr, 96, "Hallazgo tendencia", titulo="La tendencia", tam=15.0)
    p.agregar("serie_mensual", "areaChart", xr, Y0 + 96 + 16, wr, 270,
              titulo="Víctimas por día, mes a mes: la caída de 2020 y el pico de 2023",
              roles={"Category": [(col("dim_periodo", "fecha_mes"), "Mes")],
                     "Y": [(med("Media diaria"), "Víctimas por día")]},
              objetos={**ejes(), "legend": [{"properties": {"show": lit(False)}}],
                       "dataPoint": [{"properties": {"fill": color(p.acento)}}],
                       "lineStyles": [{"properties": {"strokeWidth": lit(3)}}]})
    y = Y0 + 96 + 16 + 270 + 16
    p.agregar("por_anio", "clusteredColumnChart", xr, y, wr, H - M - y,
              titulo="Media diaria por año (* atípico · † hasta octubre)",
              roles={"Category": [(col("dim_anio", "anio_texto"), "Año")],
                     "Y": [(med("Media diaria"), "Víctimas por día")]},
              orden=(col("dim_anio", "anio_texto"), "Ascending"),
              objetos=con_etiquetas({**ejes(), **barras_calor("Media diaria")}),
              filtros=[filtro_en("dim_anio", "anio", ANIOS_SERIE, "f_anios_serie")])
    return p


DIAS_COLOR = {"viernes": "#C4B5FD", "sábado": "#A78BFA", "miércoles": "#8B5CF6", "jueves": "#7C3AED",
              "martes": "#6D28D9", "lunes": "#5B21B6", "domingo": "#475569"}


def pagina_patrones():
    p = Pagina("patrones", "¿Cuándo ocurre el hurto?",
               "Patrones por día de la semana, mes y festivos · media de víctimas por día")
    p.encabezado()
    wl = 720
    p.agregar("matriz_semana_mes", "pivotTable", M, Y0, wl, H_UTIL,
              titulo="Mapa de calor: víctimas por día según el día de la semana y el mes",
              roles={"Rows": [(col("dim_calendario", "dia_semana"), "Día")],
                     "Columns": [(col("dim_periodo", "mes_corto"), "Mes")],
                     "Values": [(med("Media diaria"), "Víctimas por día")]},
              objetos=matriz_calor("Media diaria", 22, None))
    xr = M + wl + G
    wr = W - M - xr
    p.fila_tarjetas(Y0, [("Día pico", "Día con más hurtos", 22.0), ("Mes pico", "Mes con más hurtos", 22.0)],
                    h=88, x0=xr, ancho_total=wr, sep=16, prefijo="kpi")
    p.fila_tarjetas(Y0 + 88 + 16, [("Efecto festivo %", "Lunes festivo vs. laborable"),
                                   ("Media fin de semana vs laborable %", "Fin de semana vs. laborable")],
                    h=88, x0=xr, ancho_total=wr, sep=16, prefijo="kpi2")
    y = Y0 + 2 * (88 + 16)
    p.hallazgo("hallazgo_semana", xr, y, wr, 96, "Hallazgo semana", titulo="La semana")
    y += 96 + 16
    p.hallazgo("hallazgo_festivo", xr, y, wr, 104, "Hallazgo festivo", titulo="Los festivos")
    y += 104 + 16
    dia = col("dim_calendario", "dia_semana")
    p.agregar("reparto_semana", "donutChart", xr, y, wr, H - M - y,
              titulo="Reparto de las víctimas por día de la semana",
              roles={"Category": [(dia, "Día")], "Y": [(med("Víctimas"), "Víctimas")]},
              objetos={"legend": [{"properties": {"show": lit(True), "position": lit("Right"),
                                                  "labelColor": color(TEXTO), "fontSize": lit(11.0)}}],
                       "labels": [{"properties": {"show": lit(True), "labelStyle": lit("Percent of total"),
                                                  "color": color(TEXTO), "fontSize": lit(11.0)}}],
                       "dataPoint": colores_serie(dia, DIAS_COLOR)})
    return p


def pagina_territorio():
    p = Pagina("territorio", "¿Dónde ocurre el hurto?",
               "Llamadas de hurto a la Línea 123 por localidad, 2020–2025 · volumen frente a tasa por 100.000 habitantes")
    p.encabezado()
    tasa = med("Tasa 123 por 100k")
    prom = lambda c: {"Aggregation": {"Expression": col("dim_localidad", c), "Function": 1}}
    wl = 600
    p.agregar("mapa_calor", "azureMap", M, Y0, wl, H_UTIL,
              titulo="Mapa de calor: tasa por localidad (área urbana; sin Sumapaz ni «sin localización»)",
              roles={"Category": [(col("dim_localidad", "localidad"), "Localidad")],
                     # Con Ubicación en el visual, latitud y longitud deben ir agregadas (promedio).
                     "Y": [(prom("latitud"), "Latitud")],
                     "X": [(prom("longitud"), "Longitud")],
                     "Size": [(tasa, "Tasa por 100.000")],
                     "Tooltips": [(med("Llamadas 123"), "Llamadas"), (med("Puesto por tasa"), "Puesto por tasa"),
                                  (med("Puesto por conteo"), "Puesto por conteo")]},
              objetos={"heatMapLayer": [{"properties": {
                           "show": lit(True), "heatMapUseSize": lit(True), "heatMapRadius": lit(1800.0),
                           "heatMapRadiusUnit": lit("meters"), "heatMapIntensity": lit(1.0),
                           "heatMapColorLow": color(CALOR[0]), "heatMapColorCenter": color(CALOR[1]),
                           "heatMapColorHigh": color(CALOR[2]), "mapTransparency": lit(20.0)}}],
                       "bubbleLayer": [{"properties": {"show": lit(True), "bubbleRadius": lit(7.0),
                                                       "minBubbleRadius": lit(5.0), "maxRadius": lit(20.0),
                                                       "mapTransparency": lit(10.0)}}],
                       "dataPoint": [{"properties": {"fill": gradiente(tasa)}, "selector": selector_todos(tasa)}],
                       "categoryLabels": [{"properties": {"show": lit(True), "color": color(TEXTO),
                                                          "fontSize": lit(10.0)}}],
                       "mapControls": [{"properties": {"autoZoom": lit(True), "defaultStyle": lit("grayscale_dark"),
                                                       "showNavigationControls": lit(True)}}],
                       "legend": [{"properties": {"show": lit(False)}}]},
              filtros=[filtro_en("dim_localidad", "en_mapa_urbano", [1], "f_urbano")])
    xr = M + wl + G
    wr = W - M - xr
    p.fila_tarjetas(Y0, [("Llamadas 123", "Llamadas por hurto (Línea 123)", 24.0),
                         ("Tasa ciudad por 100k", "Tasa de la ciudad por 100.000 hab.", 24.0)],
                    h=84, x0=xr, ancho_total=wr, sep=16)
    y = Y0 + 84 + 16
    p.hallazgo("hallazgo", xr, y, wr, 112, "Hallazgo territorio", titulo="Volumen frente a tasa")
    y += 112 + 16
    loc = col("dim_localidad", "localidad")
    llamadas = med("Llamadas 123")
    p.agregar("volumen_localidad", "treemap", xr, y, wr, 180,
              titulo="Volumen: qué localidades concentran las llamadas",
              roles={"Group": [(loc, "Localidad")], "Values": [(llamadas, "Llamadas")]},
              objetos={"labels": [{"properties": {"show": lit(True), "color": color("#111827"),
                                                  "fontSize": lit(10.0)}}],
                       "categoryLabels": [{"properties": {"show": lit(True), "color": color("#111827"),
                                                          "fontSize": lit(11.0)}}],
                       "legend": [{"properties": {"show": lit(False)}}],
                       "dataPoint": [{"properties": {"fill": gradiente(llamadas)},
                                      "selector": selector_todos(llamadas)}]})
    y += 180 + 16
    p.agregar("ranking_tasa", "tableEx", xr, y, wr, H - M - y,
              # Orden alfabético a propósito: el tablero no presenta un ranking de peligrosidad
              # (docs/POWERBI.md, sección 4). Los dos puestos se ven lado a lado, como el salto de Kennedy.
              titulo="Volumen frente a tasa: el puesto de cada localidad por conteo y por tasa",
              roles={"Values": [(loc, "Localidad"), (llamadas, "Llamadas"),
                                (med("Puesto por conteo"), "Puesto por conteo"),
                                (tasa, "Tasa por 100.000"), (med("Puesto por tasa"), "Puesto por tasa")]},
              orden=(loc, "Ascending"),
              objetos={"values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(PANEL),
                                                  "fontColorSecondary": color(TEXTO),
                                                  "backColorSecondary": color("#18243F"), "fontSize": lit(11.0)}},
                                  {"properties": {"backColor": gradiente(tasa), "fontColor": color("#111827")},
                                   "selector": {"metadata": "Medidas.Tasa 123 por 100k"}}],
                       "columnHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE),
                                                         "fontSize": lit(11.0), "wordWrap": lit(True)}}],
                       "total": [{"properties": {"totals": lit(False)}}]})
    return p


def pagina_pronostico():
    p = Pagina("pronostico", "¿Se puede anticipar el hurto?",
               "Modelos de pronóstico diario evaluados en los últimos 184 días de la serie (2025)")
    p.encabezado(con_filtro=False)
    p.fila_tarjetas(Y0, [("Mejor modelo", "Mejor modelo", 18.0), ("MAE mejor modelo", "Error medio (víctimas/día)"),
                         ("Mejora sobre la barra %", "Menos error que la referencia"),
                         ("Barra MAE", "Error de la referencia ingenua")], h=96)
    y = Y0 + 96 + 16
    p.agregar("real_vs_pronostico", "lineChart", M, y, ANCHO, 250,
              titulo="Lo observado frente al pronóstico del mejor modelo (gradiente por histogramas), últimos 184 días",
              roles={"Category": [(col("fact_predicciones", "fecha"), "Fecha")],
                     "Y": [(med("Observado"), "Observado"), (med("Pronóstico"), "Pronóstico del gradiente")]},
              objetos={**ejes(), "lineStyles": [{"properties": {"strokeWidth": lit(2)}}],
                       "dataPoint": [color_medida("Observado", "#E2E8F0"), color_medida("Pronóstico", p.acento)]},
              filtros=[filtro_en("fact_predicciones", "modelo", ["gradiente_histogramas"], "f_modelo"),
                       filtro_en("fact_predicciones", "pliegue", ["final"], "f_final")])
    y += 250 + 16
    (x1, w1), (x2, w2) = columnas(3, 2)
    mae = med("MAE modelo")
    familia = col("fact_modelos", "familia")
    p.agregar("mae_modelos", "clusteredBarChart", x1, y, w1, H - M - y,
              titulo="Error medio por modelo (menor es mejor), por familia",
              roles={"Category": [(col("fact_modelos", "nombre"), "Modelo")],
                     "Series": [(familia, "Familia")],
                     "Y": [(mae, "MAE")]},
              orden=(mae, "Ascending"),
              objetos=con_etiquetas({**ejes(), "dataPoint": colores_serie(familia, COLOR_FAMILIA)}),
              filtros=[filtro_en("fact_modelos", "variante", ["completo"], "f_completo"),
                       filtro_en("fact_modelos", "origen", ["#42", "#45", "#144"], "f_origen")])
    p.hallazgo("hallazgo", x2, y, w2, H - M - y, "Hallazgo modelo", titulo="Cómo leer el error", tam=15.0)
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
        "dataColors": [ACENTO, "#22D3EE", "#A78BFA", "#F87171", "#34D399", "#94A3B8", "#FACC15", "#E879F9"],
        "background": FONDO, "foreground": TEXTO, "tableAccent": ACENTO,
        "good": "#34D399", "neutral": "#FACC15", "bad": "#F43F5E",
        "maximum": CALOR[2], "center": CALOR[1], "minimum": CALOR[0],
        "textClasses": {
            "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": TEXTO},
            "title": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
            "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
            "label": {"fontSize": 11, "fontFace": "Segoe UI", "color": TEXTO_2}},
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
    paginas = [pagina_panorama(), pagina_patrones(), pagina_territorio(), pagina_pronostico()]

    escribir(REPORTE / "definition.pbir",
             {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}}})
    escribir(DEF / "version.json", {"$schema": f"{ESQ}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    escribir(DEF / "report.json", {
        "$schema": f"{ESQ}/report/1.0.0/schema.json",
        "layoutOptimization": "None",
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
                "panorama": "Panorama", "patrones": "¿Cuándo?", "territorio": "¿Dónde?",
                "pronostico": "Pronóstico"}[p.nombre],
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
