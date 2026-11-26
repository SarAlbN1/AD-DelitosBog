#!/usr/bin/env python3
"""Capa de localidades para el mapa del tablero de Power BI (#106).

Lee la capa oficial de localidades (`data/raw/localidades.geojson`, descargada del FeatureServer de
la Secretaría Distrital de Seguridad con la orden de `data/README.md`) y escribe en
`outputs/powerbi/`:

* `geo_localidades.csv`: una fila por localidad, con su código, su `clave` de cruce con Línea 123,
  el centroide (latitud y longitud) y el área relativa. Sirve para los mapas por coordenadas.
* `localidades_bogota.topojson`: los polígonos simplificados, para el mapa coroplético
  (visual *Mapa de formas*). La propiedad `clave` es la que se une con `dim_localidad[clave]`.

Solo usa la biblioteca estándar. No toma ninguna cifra de la capa: sus columnas de conteo (`CMH…`)
son de la SCJ y no del proyecto. De la capa salen la geometría, el código y el nombre.

Se excluyen dos polígonos del mapa y se dice por qué:

* «Sin Localización» (código 99) no es una localidad y no tiene geometría.
* Sumapaz es rural (`es_rural_sumapaz = 1` en `dim_localidad`). Su área es casi la mitad del
  Distrito y aplastaría el área urbana. Va en el CSV, marcada, pero no en el TopoJSON urbano.

Uso::

    python scripts/geo_localidades_powerbi.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

#: Nombres de la capa SCJ que no coinciden con la clave de Línea 123 tras quitar tildes.
EXCEPCIONES_CLAVE = {"LA CANDELARIA": "CANDELARIA"}

#: Tolerancia de simplificación en grados (~25 m). Suficiente para un mapa de 20 polígonos.
TOLERANCIA = 0.00025


def clave_de(nombre: str) -> str:
    """Mayúsculas sin tildes, igual que `dim_localidad[clave]` (la Ñ pasa a N)."""
    s = unicodedata.normalize("NFKD", nombre.strip().upper())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return EXCEPCIONES_CLAVE.get(s, s)


def _anillos(geom: dict) -> list[list[list[list[float]]]]:
    """Devuelve la geometría como lista de polígonos, cada uno lista de anillos."""
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    raise ValueError(f"geometría no soportada: {geom['type']}")


def _area_centroide(anillo: list[list[float]]) -> tuple[float, float, float]:
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(anillo, anillo[1:] + anillo[:1]):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    a /= 2.0
    if a == 0:
        return 0.0, anillo[0][0], anillo[0][1]
    return a, cx / (6 * a), cy / (6 * a)


def centroide(poligonos) -> tuple[float, float, float]:
    """Centroide de área (lon, lat) y área total, restando los huecos."""
    at = sx = sy = 0.0
    for anillos in poligonos:
        for i, anillo in enumerate(anillos):
            a, cx, cy = _area_centroide([p[:2] for p in anillo])
            a = abs(a) * (1 if i == 0 else -1)
            at += a
            sx += cx * a
            sy += cy * a
    return sx / at, sy / at, at


def _dp(puntos: list[list[float]], tol: float) -> list[list[float]]:
    """Douglas–Peucker iterativo."""
    if len(puntos) < 3:
        return puntos
    conservar = [False] * len(puntos)
    conservar[0] = conservar[-1] = True
    pila = [(0, len(puntos) - 1)]
    while pila:
        i, j = pila.pop()
        (x0, y0), (x1, y1) = puntos[i][:2], puntos[j][:2]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy)
        dmax, kmax = 0.0, -1
        for k in range(i + 1, j):
            x, y = puntos[k][:2]
            d = abs(dy * x - dx * y + x1 * y0 - y1 * x0) / n if n else math.hypot(x - x0, y - y0)
            if d > dmax:
                dmax, kmax = d, k
        if dmax > tol:
            conservar[kmax] = True
            pila += [(i, kmax), (kmax, j)]
    return [p[:2] for p, c in zip(puntos, conservar) if c]


def simplificar(anillo, tol):
    s = _dp(anillo, tol)
    if len(s) < 4:  # un anillo necesita al menos 4 puntos (cerrado)
        s = [p[:2] for p in anillo]
    return [[round(x, 5), round(y, 5)] for x, y in s]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--capa", type=Path, default=RAIZ / "data" / "raw" / "localidades.geojson")
    p.add_argument("--salida", type=Path, default=RAIZ / "outputs" / "powerbi")
    a = p.parse_args(argv)

    capa = json.loads(a.capa.read_text(encoding="utf-8"))
    filas, objetos, arcos = [], [], []
    for f in capa["features"]:
        pr = f["properties"]
        codigo = int(pr["CMIULOCAL"])
        if codigo == 99:  # «Sin Localización»: no es una localidad
            continue
        nombre = pr["CMNOMLOCAL"].strip()
        poligonos = _anillos(f["geometry"])
        lon, lat, area = centroide(poligonos)
        rural = int(codigo == 20)
        filas.append({"codigo_localidad": codigo, "localidad_capa": nombre, "clave": clave_de(nombre),
                      "latitud": round(lat, 6), "longitud": round(lon, 6),
                      "area_grados2": round(area, 8), "en_mapa_urbano": 1 - rural})
        if rural:
            continue
        idx_pol = []
        for anillos in poligonos:
            idx_an = []
            for anillo in anillos:
                arcos.append(simplificar(anillo, TOLERANCIA))
                idx_an.append([len(arcos) - 1])
            idx_pol.append(idx_an)
        objetos.append({"type": "MultiPolygon", "arcs": idx_pol,
                        "properties": {"clave": clave_de(nombre), "codigo_localidad": codigo,
                                       "localidad": nombre}})

    filas.sort(key=lambda r: r["codigo_localidad"])
    claves = [r["clave"] for r in filas]
    if len(filas) != 20 or len(set(claves)) != 20:
        raise SystemExit(f"se esperaban 20 localidades con clave única y hay {len(filas)}: {claves}")

    a.salida.mkdir(parents=True, exist_ok=True)
    with open(a.salida / "geo_localidades.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)

    topo = {"type": "Topology",
            "objects": {"localidades": {"type": "GeometryCollection",
                                        "geometries": sorted(objetos, key=lambda o: o["properties"]["codigo_localidad"])}},
            "arcs": arcos}
    (a.salida / "localidades_bogota.topojson").write_text(
        json.dumps(topo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(filas)} localidades en geo_localidades.csv; {len(objetos)} polígonos urbanos "
          f"y {sum(len(x) for x in arcos)} vértices en localidades_bogota.topojson")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
