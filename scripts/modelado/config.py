"""Carga y validación de `config/modelado.json` (#41).

Este archivo es la **única** codificación del protocolo que fija D-04. La razón de centralizarlo es
concreta: la ruta de Línea 123 ya estuvo escrita en dos scripts y divergió, y nadie lo notó hasta
que alguien lo buscó. Con la partición, los pliegues y las métricas pasaría lo mismo y sería peor,
porque un modelo evaluado con otra partición da otro número sin avisar.

La validación no es decorativa. Comprueba lo que, si estuviera mal, produciría resultados
plausibles pero falsos: una partición que deja un lado vacío, pliegues que no caben en el
entrenamiento, o una métrica principal que no está entre las reportadas.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

#: Métricas que el proyecto sabe calcular (`scripts/baselines.py`).
METRICAS_CONOCIDAS = {"MAE", "RMSE", "MAPE", "MASE"}

#: Esquemas de validación admitidos. Una validación aleatoria no es admisible en una serie.
ESQUEMAS = {"origen_rodante"}


class ErrorConfig(Exception):
    """Configuración inválida, con un mensaje que dice qué corregir."""


@dataclass(frozen=True)
class Config:
    """El protocolo, ya validado."""

    semilla: int
    horizonte_dias: int
    objetivo: str
    serie: Path
    features: Path
    fin_entrenamiento: str
    esquema: str
    pliegues: int
    dias_pliegue: int
    minimo_entrenamiento: int
    metrica_principal: str
    metricas: tuple[str, ...]
    periodo_estacional_mase: int
    criterio_barra: str
    anio_atipico: int
    indicador_atipico: str
    prueba_sensibilidad: bool
    excluidas_por_fuga: tuple[str, ...]
    carpeta_registro: Path
    indice_registro: str
    ruta: Path
    sha256: str
    crudo: dict = field(repr=False, default_factory=dict)

    def resumen(self) -> dict:
        """Lo que se guarda en el registro de cada corrida para poder reproducirla."""
        return {
            "config": self.ruta.as_posix(),
            "config_sha256": self.sha256,
            "semilla": self.semilla,
            "horizonte_dias": self.horizonte_dias,
            "fin_entrenamiento": self.fin_entrenamiento,
            "esquema_validacion": self.esquema,
            "pliegues": self.pliegues,
            "dias_pliegue": self.dias_pliegue,
            "metrica_principal": self.metrica_principal,
            "metricas": list(self.metricas),
        }


def _fecha(valor: str, campo: str) -> str:
    try:
        dt.date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ErrorConfig(f"{campo} debe ser una fecha AAAA-MM-DD, no {valor!r}") from None
    return valor


def _entero_positivo(valor, campo: str) -> int:
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise ErrorConfig(f"{campo} debe ser un entero positivo, no {valor!r}")
    return valor


def cargar(ruta: Path | str | None = None) -> Config:
    """Lee la configuración, la valida y devuelve un `Config` inmutable."""
    ruta = Path(ruta) if ruta else Path(__file__).resolve().parents[2] / "config" / "modelado.json"
    if not ruta.is_file():
        raise ErrorConfig(f"no existe {ruta}")
    crudo = ruta.read_bytes()
    try:
        d = json.loads(crudo)
    except json.JSONDecodeError as e:
        raise ErrorConfig(f"{ruta} no es JSON válido: {e}") from e

    for clave in ("semilla", "particion", "validacion", "metricas"):
        if clave not in d:
            raise ErrorConfig(f"falta la clave {clave!r} en {ruta}")

    val, met = d["validacion"], d["metricas"]
    if val.get("esquema") not in ESQUEMAS:
        raise ErrorConfig(
            f"esquema de validación {val.get('esquema')!r} no admitido. Admitidos: {sorted(ESQUEMAS)}. "
            f"Una validación aleatoria pondría futuro en el entrenamiento.")

    metricas = tuple(met.get("reportadas", []))
    if not metricas:
        raise ErrorConfig("metricas.reportadas no puede estar vacío")
    desconocidas = set(metricas) - METRICAS_CONOCIDAS
    if desconocidas:
        raise ErrorConfig(f"métricas desconocidas: {sorted(desconocidas)}. "
                          f"Conocidas: {sorted(METRICAS_CONOCIDAS)}")
    principal = met.get("principal")
    if principal not in metricas:
        raise ErrorConfig(f"la métrica principal {principal!r} no está entre las reportadas "
                          f"{list(metricas)}: se decidiría con una métrica que no se reporta")

    pliegues = _entero_positivo(val.get("pliegues"), "validacion.pliegues")
    dias = _entero_positivo(val.get("dias_pliegue"), "validacion.dias_pliegue")
    minimo = _entero_positivo(val.get("minimo_entrenamiento"), "validacion.minimo_entrenamiento")

    raiz = ruta.resolve().parents[1]
    atip = d.get("anio_atipico") or {}
    reg = d.get("registro") or {}
    return Config(
        semilla=_entero_positivo(d["semilla"], "semilla"),
        horizonte_dias=_entero_positivo(d.get("horizonte_dias", 1), "horizonte_dias"),
        objetivo=d.get("objetivo", "victimas"),
        serie=raiz / d.get("serie", "data/processed/serie_objetivo_diaria.csv"),
        features=raiz / d.get("features", "data/processed/features_diarias.csv"),
        fin_entrenamiento=_fecha(d["particion"].get("fin_entrenamiento"),
                                 "particion.fin_entrenamiento"),
        esquema=val["esquema"],
        pliegues=pliegues,
        dias_pliegue=dias,
        minimo_entrenamiento=minimo,
        metrica_principal=principal,
        metricas=metricas,
        periodo_estacional_mase=_entero_positivo(met.get("periodo_estacional_mase", 7),
                                                 "metricas.periodo_estacional_mase"),
        criterio_barra=(d.get("barra") or {}).get("criterio", "mejor_comparador_en_evaluacion"),
        anio_atipico=_entero_positivo(atip.get("anio", 2020), "anio_atipico.anio"),
        indicador_atipico=atip.get("indicador", "anio_atipico_2020"),
        prueba_sensibilidad=bool(atip.get("prueba_sensibilidad", True)),
        excluidas_por_fuga=tuple(d.get("excluidas_por_fuga", [])),
        carpeta_registro=raiz / reg.get("carpeta", "outputs/modelado"),
        indice_registro=reg.get("indice", "experimentos.csv"),
        ruta=ruta,
        sha256=hashlib.sha256(crudo).hexdigest(),
        crudo=d,
    )


def validar_contra_serie(cfg: Config, indice) -> None:
    """Comprueba que la partición y los pliegues caben en la serie que se va a usar.

    Es la comprobación que atrapa el error silencioso: una partición fuera del rango deja un lado
    vacío, y unos pliegues que no caben se recortan sin avisar y la validación pasa a tener menos
    pliegues de los que el informe dice.
    """
    import pandas as pd

    fin = pd.Timestamp(cfg.fin_entrenamiento)
    if fin < indice.min() or fin >= indice.max():
        raise ErrorConfig(
            f"la partición en {cfg.fin_entrenamiento} deja un lado vacío: la serie va de "
            f"{indice.min().date()} a {indice.max().date()}")
    entrena = int((indice <= fin).sum())
    necesarios = cfg.minimo_entrenamiento + cfg.pliegues * cfg.dias_pliegue
    if entrena < necesarios:
        raise ErrorConfig(
            f"no caben {cfg.pliegues} pliegues de {cfg.dias_pliegue} días con un mínimo de "
            f"{cfg.minimo_entrenamiento} de entrenamiento: harían falta {necesarios} días y el "
            f"entrenamiento tiene {entrena}")
