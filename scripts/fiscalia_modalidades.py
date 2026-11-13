"""Clasifica los valores de ``delito`` de Fiscalía V3 por la modalidad que nombra el texto.

``delito`` codifica el tipo penal (art. 239 hurto, 240 hurto calificado, 243 abigeato), la cuantía
y, cuando la hay, la circunstancia de agravación del art. 241 o de atenuación del art. 242. No
existe un valor «hurto a personas»: es una clasificación operativa de la Policía, no un tipo del
Código Penal. Por eso este script **no filtra hurto a personas**; solo identifica las filas cuya
modalidad el texto permite excluir y cuantifica cuántas quedan sin modalidad identificable.

Entrada: el CSV de Bogotá descargado con ``scripts/descargar_fiscalia.py``
(``capitulo_delito = 'Del Hurto'``). Se cuentan los años del hecho 2018–2025, igual que la
auditoría.

Salidas en ``--salida`` (por defecto ``outputs/informe``):

* ``fiscalia_delito_valores.csv``: cada valor de ``delito`` con sus filas y el grupo asignado.
* ``fiscalia_modalidades_resumen.csv``: filas y número de valores por grupo.

Uso::

    python scripts/fiscalia_modalidades.py --entrada data/raw/fiscalia/fiscalia_v3_bogota_hurto.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Grupos excluibles, en orden de aplicación. Cada patrón se busca en el texto de ``delito``.
EXCLUIBLES = {
    "automotor": r"Automotor",
    "medios_motorizados_241_6": r"Medios Motorizados",
    "establecimiento_publico_241_11": r"Establecimiento Publico",
    "abigeato": r"Abigeato",
    "predio_rural_241_8": r"Predio Rural",
    "otros_objetos_especiales": r"Petroleo|Nucleares|Armas Destinadas|Patrimonio Cultural",
    "sin_detalle": r"^Del Hurto$",
}
# Tipos genéricos: el artículo y, como mucho, la cuantía, sin agravante que nombre la modalidad.
GENERICOS = (r"^Hurto\.? Art\. 239 C\.P\.$|^Hurto Art\. 239 C\.P\. (Menor|Mayor) Cuantia$"
             r"|^Hurto Calificado\.? Art\. 240 C\.P\.( (Menor|Mayor) Cuantia)?$"
             r"|^Hurto Agravado Art\. 239 C\.P\. Menor Cuantia$")


def clasificar(valor: str) -> str:
    for grupo, patron in EXCLUIBLES.items():
        if pd.Series([valor]).str.contains(patron, regex=True).iloc[0]:
            return grupo
    if pd.Series([valor]).str.match(GENERICOS).iloc[0]:
        return "generico_sin_modalidad"
    return "otro_no_excluible"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--entrada", default="data/raw/fiscalia/fiscalia_v3_bogota_hurto.csv")
    p.add_argument("--salida", default="outputs/informe")
    a = p.parse_args()

    d = pd.read_csv(a.entrada, dtype=str, usecols=["delito", "a_o_hecho"])
    d = d[d["a_o_hecho"].isin([str(y) for y in range(2018, 2026)])]
    vc = d["delito"].value_counts().rename_axis("delito").reset_index(name="filas")
    vc["grupo"] = vc["delito"].map(clasificar)

    resumen = vc.groupby("grupo").agg(filas=("filas", "sum"), valores=("delito", "size"))
    resumen["pct_filas"] = (100 * resumen["filas"] / resumen["filas"].sum()).round(2)
    resumen = resumen.sort_values("filas", ascending=False)

    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    vc.to_csv(salida / "fiscalia_delito_valores.csv", index=False)
    resumen.to_csv(salida / "fiscalia_modalidades_resumen.csv")

    excluible = resumen.loc[resumen.index.isin(EXCLUIBLES), "filas"].sum()
    resto = resumen["filas"].sum() - excluible
    gen = resumen["filas"].get("generico_sin_modalidad", 0)
    print(f"{len(d)} filas, {len(vc)} valores de delito. Excluibles por el texto: {excluible}. "
          f"Resto: {resto}, de las que {gen} ({gen / resto:.1%}) son tipos genéricos sin modalidad.")


if __name__ == "__main__":
    main()
