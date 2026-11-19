#!/usr/bin/env python3
"""Rutas de los archivos crudos, leídas del manifiesto (#34).

`config/fuentes_auditoria.json` ya es la fuente de verdad de qué archivo es cada fuente, con su URL
y su fecha de extracción. Antes cada script repetía la ruta por su cuenta y habían divergido:
`preprocesamiento.py` y `verificar_caida_2025.py` usaban `data/raw/linea123.csv`, mientras el
manifiesto y `figuras_informe.py` apuntaban a `data/raw/linea123/<nombre oficial>.csv`. Con dos
rutas, un script podía leer un archivo y otro script otro sin que nadie lo notara.

Aquí se resuelve una sola vez. Si el manifiesto cambia, los scripts siguen la nueva ruta sin
tocarlos.

Uso::

    from rutas import ruta_fuente
    p = ruta_fuente("linea123")
"""

from __future__ import annotations

import json
from pathlib import Path

#: Manifiesto de fuentes, relativo a la raíz del repositorio.
MANIFIESTO = Path("config/fuentes_auditoria.json")


def _raiz() -> Path:
    return Path(__file__).resolve().parents[1]


def archivos_fuente(fuente: str, manifiesto: Path | None = None) -> list[Path]:
    """Todos los archivos declarados para una fuente, en el orden del manifiesto.

    Los patrones con comodín se expanden; los que no existen se devuelven igual, para que el script
    que llama pueda dar un mensaje de error con la ruta esperada.
    """
    ruta = manifiesto or (_raiz() / MANIFIESTO)
    if not ruta.is_file():
        raise FileNotFoundError(f"no existe el manifiesto {ruta}")
    cfg = json.loads(ruta.read_text(encoding="utf-8"))
    for f in cfg.get("fuentes", []):
        if f.get("id") == fuente:
            salida: list[Path] = []
            for patron in f.get("archivos", []):
                if any(c in patron for c in "*?["):
                    salida.extend(sorted(_raiz().glob(patron)))
                else:
                    salida.append(_raiz() / patron)
            return salida
    raise KeyError(f"la fuente {fuente!r} no está en {ruta}. "
                   f"Fuentes declaradas: {[f.get('id') for f in cfg.get('fuentes', [])]}")


def ruta_fuente(fuente: str, manifiesto: Path | None = None) -> Path:
    """El primer archivo de una fuente. Para las fuentes de un solo archivo."""
    archivos = archivos_fuente(fuente, manifiesto)
    if not archivos:
        raise FileNotFoundError(f"la fuente {fuente!r} no declara archivos en el manifiesto")
    return archivos[0]


if __name__ == "__main__":
    import sys
    for f in sys.argv[1:] or ["linea123", "policia_registro", "policia_agregado", "fiscalia"]:
        try:
            rs = archivos_fuente(f)
            for r in rs:
                marca = "ok " if r.is_file() else "falta"
                print(f"{marca} {f}: {r.relative_to(_raiz())}")
            if not rs:
                print(f"falta {f}: sin archivos declarados")
        except (KeyError, FileNotFoundError) as e:
            print(f"error {f}: {e}")
