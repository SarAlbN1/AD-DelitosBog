"""Arnés de evaluación compartido (#42).

El criterio de aceptación de #42 es que **los comparadores usen exactamente los mismos pliegues que
los modelos**. Que ambos «sigan el mismo protocolo» no basta: con dos implementaciones separadas,
un cambio en una no se refleja en la otra y los números dejan de ser comparables sin que nada
avise. Es el mismo problema que la ruta de Línea 123 duplicada (#34).

Así que aquí vive **la única** definición de los pliegues, de la partición y de las métricas. Los
comparadores (`modelado.referencia`) y los modelos usan estas funciones, no sus copias.

Un **predictor** es cualquier función con esta firma:

    predictor(y: pd.Series, X: pd.DataFrame | None, entrena: np.ndarray,
              indice: pd.DatetimeIndex) -> pd.Series

Devuelve la predicción para `indice`. Recibe la serie observada completa y la máscara del tramo de
entrenamiento, con un contrato explícito: **puede usar `y[s]` solo para `s` estrictamente anterior
al día que predice**, y puede ajustar parámetros solo con `entrena`.

Recibir la serie completa es necesario, no una concesión. El horizonte es de un día: para predecir
`t` se usa el conteo de `t-1`, que **ya es pasado** y está observado, también dentro de la ventana
de evaluación. Es lo que fija el protocolo: «avanzar un día a la vez usando el conteo observado del
día anterior cuando ya pertenece al pasado del pronóstico».

Retener el tramo de evaluación rompería el pronóstico en lugar de protegerlo: un comparador ingenuo
solo podría predecir el primer día de la ventana y el resto saldría vacío. Lo que protege del uso
indebido no es ocultar los datos, es la **prueba de perturbación**: alterar `y` desde un día hacia
adelante no puede cambiar la predicción de ese día. Está en `tests/test_evaluacion.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

import numpy as np
import pandas as pd

#: Versión de la semántica del arnés. **Se sube a mano** cuando cambia cómo se calcula un
#: resultado: los pliegues, el contrato del predictor, el denominador del MASE o las métricas.
#:
#: Existe porque el registro de experimentos identifica una corrida por su huella, y la huella
#: no puede mirar el código. Sin esta versión, arreglar un error del arnés producía la misma
#: huella con métricas distintas y el registro se negaba a seguir —correctamente, pero sin salida.
#: Pasó al corregir el contrato del predictor: la versión 1 retenía el tramo de evaluación y un
#: comparador ingenuo solo podía predecir el primer día de la ventana.
#:
#: No se sube por cambios de comentarios, nombres ni mensajes de registro: solo si el número
#: resultante puede cambiar.
VERSION_ARNES = 2

#: Firma de un predictor.
Predictor = Callable[[pd.Series, "pd.DataFrame | None", "np.ndarray", pd.DatetimeIndex],
                     pd.Series]


class ConfigLike(Protocol):
    fin_entrenamiento: str
    pliegues: int
    dias_pliegue: int
    minimo_entrenamiento: int
    periodo_estacional_mase: int
    metricas: tuple[str, ...]
    metrica_principal: str


@dataclass(frozen=True)
class Pliegue:
    """Un pliegue de la validación de origen rodante."""

    numero: int
    fin_entrenamiento: pd.Timestamp
    fin_evaluacion: pd.Timestamp

    def mascaras(self, indice: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
        entrena = indice <= self.fin_entrenamiento
        evalua = (indice > self.fin_entrenamiento) & (indice <= self.fin_evaluacion)
        return entrena, evalua


def mae_ingenuo_estacional(y: pd.Series, periodo: int) -> float:
    """Denominador del MASE: MAE del ingenuo estacional sobre el tramo que se pase."""
    e = (y - y.shift(periodo)).abs().dropna()
    if e.empty:
        raise ValueError(f"no hay suficientes observaciones para un periodo de {periodo} días")
    return float(e.mean())


def metricas(y: pd.Series, pred: pd.Series, denominador_mase: float) -> dict:
    """MAE, RMSE, MAPE y MASE sobre los días en que la predicción existe."""
    m = y.notna() & pred.reindex(y.index).notna()
    if not m.any():
        raise ValueError("no hay días con predicción para evaluar")
    e = (y[m] - pred.reindex(y.index)[m]).to_numpy(dtype=float)
    obs = y[m].to_numpy(dtype=float)
    return {
        "n": int(m.sum()),
        "MAE": round(float(np.mean(np.abs(e))), 2),
        "RMSE": round(float(np.sqrt(np.mean(e ** 2))), 2),
        "MAPE": round(float(np.mean(np.abs(e) / obs) * 100), 2),
        "MASE": round(float(np.mean(np.abs(e)) / denominador_mase), 3),
    }


def pliegues(cfg: ConfigLike, indice: pd.DatetimeIndex) -> list[Pliegue]:
    """Los pliegues de origen rodante, dentro del entrenamiento y nunca tocando la evaluación.

    Se construyen desde el final del entrenamiento hacia atrás, de modo que el último pliegue
    termina justo en `cfg.fin_entrenamiento`. Cada pliegue entrena con todo lo anterior a su origen,
    así que el conjunto de entrenamiento crece y nunca contiene días posteriores a los que evalúa.
    """
    limite = pd.Timestamp(cfg.fin_entrenamiento)
    entrena = indice[indice <= limite]
    if entrena.empty:
        raise ValueError(f"la partición en {cfg.fin_entrenamiento} deja el entrenamiento vacío")

    salida: list[Pliegue] = []
    fin = len(entrena)
    for _ in range(cfg.pliegues):
        ini = fin - cfg.dias_pliegue
        if ini <= cfg.minimo_entrenamiento:
            break
        salida.append(Pliegue(0, entrena[ini - 1], entrena[fin - 1]))
        fin = ini
    salida.reverse()
    return [Pliegue(i + 1, p.fin_entrenamiento, p.fin_evaluacion) for i, p in enumerate(salida)]


def particion(cfg: ConfigLike, indice: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """Las máscaras de entrenamiento y evaluación finales."""
    limite = pd.Timestamp(cfg.fin_entrenamiento)
    return indice <= limite, indice > limite


def evaluar(cfg: ConfigLike, y: pd.Series, predictor: Predictor, X: pd.DataFrame | None = None,
            nombre: str = "modelo") -> dict:
    """Evalúa un predictor con el protocolo completo: pliegues rodantes y evaluación final.

    El denominador del MASE se calcula con el entrenamiento **de cada tramo**: el del pliegue para
    el pliegue, y el del entrenamiento completo para la evaluación final. Si se usara el mismo para
    todo, el MASE de los pliegues no sería comparable con su propia referencia.
    """
    idx = y.index
    tr_final, ev_final = particion(cfg, idx)
    if not tr_final.any() or not ev_final.any():
        raise ValueError(f"la partición en {cfg.fin_entrenamiento} deja un lado vacío")

    por_pliegue = []
    for p in pliegues(cfg, idx):
        tr, ev = p.mascaras(idx)
        if not ev.any():
            continue
        den = mae_ingenuo_estacional(y[tr], cfg.periodo_estacional_mase)
        pred = predictor(y, X, tr, idx[ev])
        m = metricas(y[ev], pred, den)
        por_pliegue.append({"pliegue": p.numero,
                            "fin_entrenamiento": p.fin_entrenamiento.date().isoformat(),
                            "fin_evaluacion": p.fin_evaluacion.date().isoformat(),
                            "dias_entrenamiento": int(tr.sum()), **m})

    den_final = mae_ingenuo_estacional(y[tr_final], cfg.periodo_estacional_mase)
    pred_final = predictor(y, X, tr_final, idx[ev_final])
    final = metricas(y[ev_final], pred_final, den_final)

    principal = cfg.metrica_principal
    valores = [p[principal] for p in por_pliegue]
    return {
        "nombre": nombre,
        "final": final,
        "denominador_mase": round(den_final, 2),
        "por_pliegue": por_pliegue,
        "resumen_pliegues": {
            f"{principal}_medio": round(float(np.mean(valores)), 2) if valores else None,
            f"{principal}_desv": round(float(np.std(valores, ddof=1)), 2) if len(valores) > 1 else None,
            f"{principal}_peor": round(max(valores), 2) if valores else None,
            "pliegues": len(por_pliegue),
        },
    }


def huella_pliegues(cfg: ConfigLike, indice: pd.DatetimeIndex) -> str:
    """Identifica el conjunto de pliegues, para comprobar que dos evaluaciones usaron los mismos."""
    import hashlib
    material = ";".join(f"{p.numero}:{p.fin_entrenamiento.date()}:{p.fin_evaluacion.date()}"
                        for p in pliegues(cfg, indice))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
