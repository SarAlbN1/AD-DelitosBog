"""Registro de experimentos (#41).

Cada corrida deja un JSON con todo lo necesario para reproducirla y una fila en un índice CSV para
comparar corridas de un vistazo.

El criterio de aceptación de la issue es que **dos corridas con la misma semilla produzcan las
mismas métricas**. Para que eso sea verificable y no una declaración de intenciones, cada corrida
calcula una **huella**: el SHA-256 de la configuración, el modelo, sus hiperparámetros, la semilla y
los datos de entrada. Dos corridas con la misma huella deben dar las mismas métricas, y
`comprobar_determinismo` lo comprueba contra lo ya registrado en lugar de confiar.

Se registran también las versiones de las bibliotecas. Un cambio de versión puede mover la cuarta
cifra decimal de un modelo con la misma semilla, y sin esa información la diferencia parece un
error del código.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import logging
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("modelado.registro")

#: Bibliotecas cuya versión se registra, porque pueden mover los resultados.
BIBLIOTECAS = ("pandas", "numpy", "sklearn", "statsmodels", "xgboost")


def versiones() -> dict:
    v = {"python": sys.version.split()[0], "plataforma": platform.platform()}
    for nombre in BIBLIOTECAS:
        try:
            v[nombre] = __import__(nombre).__version__
        except Exception:  # noqa: BLE001 - xgboost puede estar sin libomp
            v[nombre] = "no disponible"
    return v


def _canonico(obj) -> str:
    """Serialización estable: sin ella, el mismo diccionario daría huellas distintas."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))


def huella(cfg_sha: str, modelo: str, hiperparametros: dict, semilla: int,
           datos: dict | None = None) -> str:
    """Identifica una corrida por lo que determina su resultado, no por cuándo se lanzó."""
    material = _canonico({"config": cfg_sha, "modelo": modelo,
                          "hiperparametros": hiperparametros, "semilla": semilla,
                          "datos": datos or {}})
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


@dataclass
class Registro:
    """Escribe y lee las corridas de una carpeta."""

    carpeta: Path
    indice: str = "experimentos.csv"

    @property
    def ruta_indice(self) -> Path:
        return self.carpeta / self.indice

    @property
    def corridas(self) -> Path:
        return self.carpeta / "corridas"

    def escribir(self, entrada: dict) -> Path:
        self.corridas.mkdir(parents=True, exist_ok=True)
        destino = self.corridas / f"{entrada['huella']}.json"
        destino.write_text(json.dumps(entrada, ensure_ascii=False, indent=2, default=str),
                           encoding="utf-8")
        self._anexar_indice(entrada)
        return destino

    def _anexar_indice(self, entrada: dict) -> None:
        fila = {"huella": entrada["huella"], "momento": entrada["momento"],
                "modelo": entrada["modelo"], "semilla": entrada["semilla"],
                "config_sha256": entrada.get("config", {}).get("config_sha256", "")}
        fila.update({k: v for k, v in (entrada.get("metricas") or {}).items()})
        existentes = self.leer_indice()
        # Una corrida con la misma huella sustituye a la anterior en lugar de duplicarla.
        existentes = [f for f in existentes if f.get("huella") != fila["huella"]] + [fila]
        campos: list[str] = []
        for f in existentes:
            for k in f:
                if k not in campos:
                    campos.append(k)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        with self.ruta_indice.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(existentes)

    def leer_indice(self) -> list[dict]:
        if not self.ruta_indice.is_file():
            return []
        with self.ruta_indice.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def leer(self, huella_: str) -> dict | None:
        p = self.corridas / f"{huella_}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def registrar(cfg, modelo: str, hiperparametros: dict, metricas: dict,
              datos: dict | None = None, extra: dict | None = None) -> dict:
    """Registra una corrida y devuelve la entrada escrita.

    Si ya existe una corrida con la misma huella y métricas distintas, **falla**: significa que algo
    que debería ser determinista no lo es, y seguir adelante registraría dos verdades.
    """
    reg = Registro(cfg.carpeta_registro, cfg.indice_registro)
    h = huella(cfg.sha256, modelo, hiperparametros, cfg.semilla, datos)
    previa = reg.leer(h)
    if previa is not None:
        iguales = _canonico(previa.get("metricas")) == _canonico(metricas)
        if not iguales:
            raise RuntimeError(
                f"la corrida {h} ya existe con otras métricas: antes {previa.get('metricas')}, "
                f"ahora {metricas}. Con la misma configuración, modelo, hiperparámetros y semilla "
                f"el resultado debería ser idéntico. Revise si algún estimador no recibe "
                f"random_state o si cambió una versión (antes {previa.get('versiones')}).")
        log.info("corrida %s ya registrada con las mismas métricas", h)

    entrada = {
        "huella": h,
        "momento": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "modelo": modelo,
        "hiperparametros": hiperparametros,
        "semilla": cfg.semilla,
        "config": cfg.resumen(),
        "datos": datos or {},
        "metricas": metricas,
        "versiones": versiones(),
    }
    if extra:
        entrada["extra"] = extra
    reg.escribir(entrada)
    return entrada


def comprobar_determinismo(cfg, modelo: str, hiperparametros: dict, metricas: dict,
                           datos: dict | None = None) -> bool:
    """¿Coinciden estas métricas con las ya registradas para la misma huella?

    Devuelve True si coinciden o si no había registro previo. Devuelve False si difieren, sin
    lanzar, para que quien llama decida qué hacer.
    """
    reg = Registro(cfg.carpeta_registro, cfg.indice_registro)
    previa = reg.leer(huella(cfg.sha256, modelo, hiperparametros, cfg.semilla, datos))
    if previa is None:
        return True
    return _canonico(previa.get("metricas")) == _canonico(metricas)
