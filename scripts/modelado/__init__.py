"""Paquete de modelado (#41).

Todo lo que define el protocolo vive en `config/modelado.json`, que es la codificación de D-04.
Ningún módulo repite la partición, los pliegues, las métricas ni la semilla: se leen de ahí.

* `config`  — carga y valida la configuración.
* `semillas` — fija la aleatoriedad de forma reproducible.
* `registro` — registra cada corrida con su configuración, versiones y métricas.
"""

from .config import Config, cargar  # noqa: F401
from .registro import Registro, registrar  # noqa: F401
from .semillas import fijar_semillas  # noqa: F401

__all__ = ["Config", "cargar", "Registro", "registrar", "fijar_semillas"]
