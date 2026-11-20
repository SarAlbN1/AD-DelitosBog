"""Semilla global del modelado (#41).

La semilla está en `config/modelado.json` y vale **42**. Se fija en los tres sitios de los que
depende la reproducibilidad: el módulo `random`, el generador global de NumPy y la variable de
entorno `PYTHONHASHSEED`, que afecta al orden de iteración de conjuntos y diccionarios con claves
de texto.

Fijar la semilla no basta por sí sola: los modelos que la aceptan deben recibirla explícitamente
(`random_state`), porque muchos estimadores de scikit-learn no leen el estado global. Por eso
`fijar_semillas` devuelve el valor, para pasarlo.
"""

from __future__ import annotations

import os
import random


def fijar_semillas(semilla: int) -> int:
    """Fija la aleatoriedad del proceso y devuelve la semilla, para pasarla a los estimadores."""
    if not isinstance(semilla, int) or isinstance(semilla, bool):
        raise TypeError(f"la semilla debe ser un entero, no {type(semilla).__name__}")
    os.environ["PYTHONHASHSEED"] = str(semilla)
    random.seed(semilla)
    try:
        import numpy as np
        np.random.seed(semilla)
    except ImportError:  # pragma: no cover - numpy es una dependencia declarada
        pass
    return semilla
