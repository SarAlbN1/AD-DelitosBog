"""Frecuencias de los atributos procesales de Fiscalía V3 en la población 2018–2025.

Completa el diccionario de datos (#19). Entrada: el CSV de Bogotá descargado con
``scripts/descargar_fiscalia.py`` (``capitulo_delito = 'Del Hurto'``). Salida:
``outputs/informe/fiscalia_atributos.csv``, con una fila por variable y valor.

Uso::

    python scripts/fiscalia_atributos.py --entrada data/raw/fiscalia/fiscalia_v3_bogota_hurto.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

VARIABLES = ["grado_delito", "seccional", "delito_querellable", "proceso_conexado", "proceso_con_conexidad",
             "es_ruptura", "procedimiento_abreviado", "tipo_delito", "ley", "estado", "etapa", "tipo_noticia"]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--entrada", default="data/raw/fiscalia/fiscalia_v3_bogota_hurto.csv")
    p.add_argument("--salida", default="outputs/informe/fiscalia_atributos.csv")
    a = p.parse_args()

    d = pd.read_csv(a.entrada, dtype=str, usecols=VARIABLES + ["a_o_hecho"])
    d = d[d["a_o_hecho"].isin([str(y) for y in range(2018, 2026)])]
    partes = []
    for v in VARIABLES:
        vc = d[v].fillna("(nulo)").value_counts()
        partes.append(pd.DataFrame({"variable": v, "valor": vc.index, "filas": vc.values,
                                    "pct": (100 * vc.values / len(d)).round(3)}))
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(partes).to_csv(salida, index=False)
    print(f"{len(d)} filas; salida en {salida}")


if __name__ == "__main__":
    main()
