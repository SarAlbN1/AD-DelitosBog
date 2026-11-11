#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Auditoría reproducible de los datasets del proyecto AD-DelitosBog.

Genera evidencia verificable (hash, filas, columnas, nulos, duplicados, cobertura
temporal, distribuciones, anomalías y embudo de filtros) a partir de los archivos
originales efectivamente procesados. No inventa ni estima cifras: todo lo que
escribe proviene de leer los archivos indicados.

Uso principal (manifiesto JSON, recomendado para reproducibilidad):

    python scripts/auditoria_datasets.py --config config/fuentes_auditoria.json

Uso puntual (un solo archivo o fuente):

    python scripts/auditoria_datasets.py --archivo data/raw/fiscalia/fiscalia_bogota.csv \
        --fuente-id fiscalia --fecha-extraccion 2026-11-11 \
        --col-anio a_o_hecho --col-mes mes_hecho --col-id proceso_anonimizado \
        --col-delito delito --filtro-bogota "cod_dane_hecho=^11001" \
        --filtro-hurto "capitulo_delito=^DEL HURTO$"

Formatos soportados: .csv, .txt, .tsv, .zip (con un único CSV dentro), .xlsx, .xls.
Ver docs/AUDITORIA.md para la documentación completa.
"""
from __future__ import annotations

import argparse
import codecs
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import logging
import os
import platform
import re
import sys
import unicodedata
import zipfile
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd

__version__ = "0.1.0"
SEMILLA = 42
MINIMO_REGISTROS = 500_000
TOKENS_NULOS = {"", "NULL", "NAN", "NONE", "N/A", "NA", "#N/A", "NAT"}
EXT_TEXTO = {".csv", ".txt", ".tsv"}
EXT_EXCEL = {".xlsx", ".xlsm", ".xls"}
MAX_UNICOS = 200_000          # tope de valores únicos rastreados por columna
MAX_CATEGORIAS_AUTO = 200     # columnas con <= este nº de valores en el primer bloque se tratan como categóricas
MAX_VALORES_NUMERICOS = 5_000_000  # tope de valores guardados para cuantiles exactos
TOP_CATEGORIAS = 50

log = logging.getLogger("auditoria")


class ErrorAuditoria(Exception):
    """Error de configuración o de lectura con mensaje explicativo para el usuario."""


# --------------------------------------------------------------------------- utilidades
def normalizar_nombre(nombre: str) -> str:
    """'FECHA HECHO ' -> 'fecha_hecho'; 'Año' -> 'ano'. Hace comparables encabezados de distintos años."""
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^0-9a-zA-Z]+", "_", s.strip().lower()).strip("_")
    return s or "columna_sin_nombre"


def quitar_tildes_serie(s: pd.Series) -> pd.Series:
    return s.str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii").str.upper().str.strip()


def mascara_nulos(s: pd.Series) -> pd.Series:
    txt = s.astype("string")
    return s.isna() | txt.str.strip().str.upper().isin(TOKENS_NULOS).fillna(True)


def ruta_relativa(p: Path) -> str:
    try:
        return p.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def versiones() -> dict:
    v = {"python": sys.version.split()[0], "plataforma": platform.platform(),
         "pandas": pd.__version__, "numpy": np.__version__, "script": __version__}
    for mod in ("matplotlib", "openpyxl", "xlrd"):
        try:
            v[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001 - dependencia opcional
            v[mod] = "no instalado"
    return v


def sha256_archivo(path: Path, bloque: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(bloque), b""):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------------- lectura
def _abrir_binario(path: Path):
    """Devuelve (stream binario, nombre interno). Para .zip abre el único CSV interno."""
    if path.suffix.lower() == ".zip":
        z = zipfile.ZipFile(path)
        miembros = [m for m in z.namelist() if Path(m).suffix.lower() in EXT_TEXTO]
        if len(miembros) != 1:
            raise ErrorAuditoria(f"{path}: el .zip debe contener exactamente un CSV/TXT (encontrados: {miembros}).")
        return z.open(miembros[0]), miembros[0]
    return open(path, "rb"), path.name


def detectar_codificacion(path: Path, preferida: str = "auto") -> str:
    if preferida and preferida != "auto":
        return preferida
    for cod in ("utf-8-sig", "cp1252"):
        dec = codecs.getincrementaldecoder(cod)()
        f, _ = _abrir_binario(path)
        try:
            with f:
                for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
                    dec.decode(b)
                dec.decode(b"", final=True)
            return cod
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detectar_separador(path: Path, codificacion: str, preferido: str = "auto", fila_encabezado: int = 0) -> str:
    if preferido and preferido != "auto":
        return "\t" if preferido in ("\\t", "tab") else preferido
    f, _ = _abrir_binario(path)
    with f:
        texto = io.TextIOWrapper(f, encoding=codificacion, errors="replace", newline="")
        lineas = [texto.readline() for _ in range(fila_encabezado + 20)]
    muestra = "".join(lineas[fila_encabezado:])
    try:
        return csv.Sniffer().sniff(muestra, delimiters=",;|\t").delimiter
    except csv.Error:
        conteos = {d: muestra.count(d) for d in (",", ";", "|", "\t")}
        return max(conteos, key=conteos.get)


def iterar_bloques(path: Path, lectura: dict, chunksize: int):
    """Genera DataFrames de texto (dtype=str) por bloques y devuelve metadatos de lectura."""
    ext = path.suffix.lower()
    fila_enc = int(lectura.get("fila_encabezado", 0) or 0)
    meta = {"formato": ext.lstrip(".")}
    if ext in EXT_TEXTO or ext == ".zip":
        cod = detectar_codificacion(path, lectura.get("encoding", "auto"))
        sep = detectar_separador(path, cod, lectura.get("sep", "auto"), fila_enc)
        meta.update(codificacion=cod, separador=sep)
        f, _ = _abrir_binario(path)
        try:
            lector = pd.read_csv(f, sep=sep, encoding=cod, dtype=str, keep_default_na=False,
                                 header=fila_enc, chunksize=chunksize, low_memory=False)
            return meta, _proteger(lector, path, f)
        except Exception:
            f.close()
            raise
    if ext in EXT_EXCEL:
        hoja = lectura.get("hoja", 0)
        try:
            df = pd.read_excel(path, sheet_name=hoja if hoja is not None else 0, header=fila_enc, dtype=str)
        except ImportError as e:
            raise ErrorAuditoria(f"{path}: falta el motor de Excel ({e}). Instale openpyxl (xlsx) o xlrd (xls).") from e
        meta.update(codificacion="(excel)", separador="(excel)", hoja=str(hoja))
        return meta, (df.iloc[i:i + chunksize] for i in range(0, max(len(df), 1), chunksize))
    raise ErrorAuditoria(f"{path}: formato no soportado '{ext}'. Use CSV, TXT, TSV, ZIP (con un CSV), XLSX o XLS.")


def _proteger(lector, path, f):
    try:
        with f:
            yield from lector
    except pd.errors.ParserError as e:
        raise ErrorAuditoria(f"{path}: error de lectura CSV ({e}). Revise 'sep', 'encoding' o 'fila_encabezado' "
                             f"en el manifiesto.") from e


# --------------------------------------------------------------------------- acumuladores
class EstadisticaColumna:
    def __init__(self):
        self.no_nulos = 0
        self.nulos = 0
        self.nombres_originales: set[str] = set()
        self.archivos: set[str] = set()
        self.tipo = None
        self.unicos: set | None = set()
        self.ejemplo = None


class EstadisticaNumerica:
    def __init__(self):
        self.n = 0
        self.no_numericos = 0
        self.suma = 0.0
        self.min = np.inf
        self.max = -np.inf
        self.negativos = 0
        self.ceros = 0
        self.valores: list[np.ndarray] = []
        self.n_guardados = 0
        self.truncado = False

    def agregar(self, crudo: pd.Series, nulos: pd.Series):
        v = pd.to_numeric(crudo.where(~nulos).astype("string").str.strip().str.replace(",", ".", regex=False),
                          errors="coerce")
        validos = v.dropna().to_numpy(dtype="float64")
        self.no_numericos += int((~nulos).sum() - len(validos))
        if len(validos):
            self.n += len(validos)
            self.suma += float(validos.sum())
            self.min = min(self.min, float(validos.min()))
            self.max = max(self.max, float(validos.max()))
            self.negativos += int((validos < 0).sum())
            self.ceros += int((validos == 0).sum())
            if self.n_guardados + len(validos) <= MAX_VALORES_NUMERICOS:
                self.valores.append(validos)
                self.n_guardados += len(validos)
            else:
                self.truncado = True
        return v

    def resumen(self) -> dict:
        r = {"n_validos": self.n, "no_numericos": self.no_numericos, "suma": self.suma if self.n else None,
             "min": self.min if self.n else None, "max": self.max if self.n else None,
             "media": self.suma / self.n if self.n else None, "negativos": self.negativos, "ceros": self.ceros}
        if self.n and not self.truncado:
            arr = np.concatenate(self.valores)
            r.update(desv_est=float(arr.std(ddof=1)) if len(arr) > 1 else None,
                     p25=float(np.quantile(arr, .25)), mediana=float(np.median(arr)),
                     p75=float(np.quantile(arr, .75)), p99=float(np.quantile(arr, .99)))
        else:
            r.update(desv_est=None, p25=None, mediana=None, p75=None, p99=None)
        r["cuantiles_exactos"] = bool(self.n and not self.truncado)
        return r


def inferir_tipo(s: pd.Series, nulos: pd.Series) -> str:
    v = s[~nulos].astype(str).str.strip()
    if v.empty:
        return "vacia"
    muestra = v.head(2000)
    num = pd.to_numeric(muestra.str.replace(",", ".", regex=False), errors="coerce")
    if num.notna().mean() >= 0.99:
        return "entero" if (num.dropna() % 1 == 0).all() else "decimal"
    if muestra.str.contains(r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}", regex=True).mean() >= 0.95:
        return "fecha"
    return "texto"


class AuditorFuente:
    """Acumula todas las métricas de una fuente (uno o varios archivos) bloque a bloque."""

    def __init__(self, cfg: dict, periodo: tuple[int, int]):
        self.cfg = cfg
        self.id = cfg["id"]
        self.anio_min, self.anio_max = periodo
        cols = {k: (normalizar_nombre(v) if isinstance(v, str) and v else None)
                for k, v in (cfg.get("columnas") or {}).items() if k not in ("formato_fecha", "dayfirst")}
        self.col = cols
        self.formato_fecha = (cfg.get("columnas") or {}).get("formato_fecha")
        self.dayfirst = bool((cfg.get("columnas") or {}).get("dayfirst", False))
        self.renombrar = {normalizar_nombre(k): normalizar_nombre(v) for k, v in (cfg.get("renombrar") or {}).items()}
        self.filtros = {}
        for nombre in ("bogota", "hurto"):
            f = (cfg.get("filtros") or {}).get(nombre)
            if f:
                self.filtros[nombre] = (normalizar_nombre(f["columna"]), re.compile(f["patron"], re.IGNORECASE),
                                        re.compile(f["excluir"], re.IGNORECASE) if f.get("excluir") else None)
        self.categoricas_cfg = [normalizar_nombre(c) for c in cfg.get("categoricas", [])]
        self.n = 0
        self.columnas: "OrderedDict[str, EstadisticaColumna]" = OrderedDict()
        self.numericas: dict[str, EstadisticaNumerica] = {}
        self.categoricas: dict[str, dict[str, Counter]] = {}
        self.hash_filas = {"original": [], "final": []}
        self.hash_ids = {"original": [], "final": []}
        self.embudo = Counter()
        self.suma_embudo = Counter()
        self.temporal = {"original": Counter(), "final": Counter()}
        self.temporal_suma = {"original": Counter(), "final": Counter()}
        self.localidad = {"original": Counter(), "final": Counter()}
        self.fechas = {"min": None, "max": None, "invalidas": 0, "fuera_periodo": 0, "validas": 0}
        self.anomalias: list[dict] = []
        self.archivos: list[dict] = []
        self.columnas_por_archivo: dict[str, list[str]] = {}
        self._tipos_definidos = False

    # ---- utilidades internas
    def _anomalia(self, archivo, tipo, columna, n, ejemplo=None, detalle=""):
        if n:
            self.anomalias.append({"fuente": self.id, "archivo": archivo, "tipo": tipo, "columna": columna,
                                   "filas": int(n), "ejemplo": None if ejemplo is None else str(ejemplo)[:200],
                                   "detalle": detalle})

    def _verificar_columnas(self, df: pd.DataFrame, archivo: str):
        faltan = [f"{k}={v}" for k, v in self.col.items() if v and v not in df.columns]
        faltan += [f"filtro {k}={c}" for k, (c, _, _) in self.filtros.items() if c not in df.columns]
        if faltan:
            raise ErrorAuditoria(
                f"[{self.id}] {archivo}: columnas configuradas que no existen tras normalizar: {faltan}.\n"
                f"Columnas disponibles: {list(df.columns)}\n"
                f"Ajuste 'columnas', 'filtros' o 'renombrar' en el manifiesto.")

    def _preparar(self, df: pd.DataFrame, archivo: str) -> pd.DataFrame:
        originales = list(df.columns)
        nuevos, vistos = [], Counter()
        for c in originales:
            n = normalizar_nombre(c)
            n = self.renombrar.get(n, n)
            vistos[n] += 1
            nuevos.append(n if vistos[n] == 1 else f"{n}_{vistos[n]}")
        df = df.copy()
        df.columns = nuevos
        for o, n in zip(originales, nuevos):
            est = self.columnas.setdefault(n, EstadisticaColumna())
            est.nombres_originales.add(str(o))
            est.archivos.add(archivo)
        self.columnas_por_archivo.setdefault(archivo, nuevos)
        return df

    # ---- procesamiento de un bloque
    def procesar_bloque(self, df: pd.DataFrame, archivo: str, primero: bool):
        df = self._preparar(df, archivo)
        if primero:
            self._verificar_columnas(df, archivo)
        n = len(df)
        if n == 0:
            return 0
        self.n += n
        nulos = {c: mascara_nulos(df[c]) for c in df.columns}

        if not self._tipos_definidos:
            for c in df.columns:
                self.columnas[c].tipo = inferir_tipo(df[c], nulos[c])
                if self.columnas[c].tipo in ("entero", "decimal") and c != self.col.get("id"):
                    self.numericas.setdefault(c, EstadisticaNumerica())
                k = df[c][~nulos[c]].nunique()
                if (c in self.categoricas_cfg or (k <= MAX_CATEGORIAS_AUTO and self.columnas[c].tipo == "texto")
                        or c in (self.col.get("localidad"), self.col.get("delito"))):
                    self.categoricas.setdefault(c, {"original": Counter(), "final": Counter()})
            if self.col.get("cantidad"):
                self.numericas.setdefault(self.col["cantidad"], EstadisticaNumerica())
            self._tipos_definidos = True
        for c in df.columns:  # columnas que aparecen en archivos posteriores
            if self.columnas[c].tipo is None:
                self.columnas[c].tipo = inferir_tipo(df[c], nulos[c])

        # nulos, únicos, ejemplo
        for c in df.columns:
            est = self.columnas[c]
            nn = int(nulos[c].sum())
            est.nulos += nn
            est.no_nulos += n - nn
            if est.ejemplo is None and n - nn:
                est.ejemplo = df[c][~nulos[c]].iloc[0]
            if est.unicos is not None:
                est.unicos.update(pd.util.hash_array(df[c][~nulos[c]].astype(str).to_numpy()).tolist())
                if len(est.unicos) > MAX_UNICOS:
                    est.unicos = None
        # filas con casi todo vacío (típico de filas de notas o totales en Excel)
        frac_nulos = pd.concat(nulos, axis=1).mean(axis=1)
        vacias = frac_nulos >= 0.8
        self._anomalia(archivo, "fila_casi_vacia(>=80% nulos)", "*", vacias.sum(),
                       df[vacias].iloc[0].to_dict() if vacias.any() else None,
                       "Posibles filas de notas, títulos o totales; revisar antes de contarlas como registros.")

        # numéricas
        cantidad = None
        for c, est in self.numericas.items():
            if c in df.columns:
                v = est.agregar(df[c], nulos[c])
                if c == self.col.get("cantidad"):
                    cantidad = v
        if cantidad is not None:
            c = self.col["cantidad"]
            self._anomalia(archivo, "cantidad_negativa", c, (cantidad < 0).sum(), cantidad[cantidad < 0].head(1).tolist())
            self._anomalia(archivo, "cantidad_cero", c, (cantidad == 0).sum())
            nonum = (~nulos[c]) & cantidad.isna()
            self._anomalia(archivo, "cantidad_no_numerica", c, nonum.sum(), df[c][nonum].head(1).tolist())
            self._anomalia(archivo, "cantidad_nula", c, nulos[c].sum())
            cant = cantidad.fillna(0)
        else:
            cant = pd.Series(0.0, index=df.index)

        # fechas / año-mes
        anio, mes = self._anio_mes(df, nulos, archivo)

        # máscaras de filtros (acumulativas)
        m_bog = self._mascara_filtro("bogota", df)
        m_per = anio.between(self.anio_min, self.anio_max).fillna(False) if anio is not None else pd.Series(True, index=df.index)
        m_hur = self._mascara_filtro("hurto", df)
        etapas = OrderedDict([("1_original", pd.Series(True, index=df.index)), ("2_bogota", m_bog),
                              ("3_periodo", m_bog & m_per), ("4_hurto", m_bog & m_per & m_hur)])
        for k, m in etapas.items():
            self.embudo[k] += int(m.sum())
            self.suma_embudo[k] += float(cant[m].sum())
        final = etapas["4_hurto"]

        # duplicados
        hashes = pd.util.hash_pandas_object(df[sorted(df.columns)], index=False).to_numpy()
        self.hash_filas["original"].append(hashes)
        self.hash_filas["final"].append(hashes[final.to_numpy()])
        if self.col.get("id"):
            idc = self.col["id"]
            hid = pd.util.hash_array(df[idc].astype(str).to_numpy())
            validos = (~nulos[idc]).to_numpy()
            self.hash_ids["original"].append(hid[validos])
            self.hash_ids["final"].append(hid[validos & final.to_numpy()])
            self._anomalia(archivo, "id_nulo", idc, nulos[idc].sum())

        # cobertura temporal y localidad
        for etapa, m in (("original", pd.Series(True, index=df.index)), ("final", final)):
            if anio is not None:
                clave = pd.DataFrame({"a": anio[m], "m": mes[m] if mes is not None else pd.NA, "c": cant[m]})
                clave = clave.fillna({"a": -1, "m": -1})
                g = clave.groupby(["a", "m"], dropna=False)["c"].agg(["size", "sum"])
                for (a, mm), fila in g.iterrows():
                    self.temporal[etapa][(int(a), int(mm))] += int(fila["size"])
                    self.temporal_suma[etapa][(int(a), int(mm))] += float(fila["sum"])
            if self.col.get("localidad"):
                loc = df[self.col["localidad"]].where(~nulos[self.col["localidad"]], "(nulo)")
                self.localidad[etapa].update(loc[m].astype(str).str.strip().str.upper().value_counts().to_dict())
            for c, cont in self.categoricas.items():
                if c in df.columns:
                    vals = df[c].where(~nulos[c], "(nulo)").astype(str).str.strip()
                    cont[etapa].update(vals[m].value_counts().to_dict())
        return n

    def _mascara_filtro(self, nombre, df):
        if nombre not in self.filtros:
            return pd.Series(True, index=df.index)
        col, patron, excluir = self.filtros[nombre]
        v = quitar_tildes_serie(df[col].astype("string").fillna(""))
        m = v.str.contains(patron, regex=True).fillna(False)
        if excluir is not None:
            m &= ~v.str.contains(excluir, regex=True).fillna(False)
        return m.astype(bool)

    def _anio_mes(self, df, nulos, archivo):
        cf, ca, cm = self.col.get("fecha"), self.col.get("anio"), self.col.get("mes")
        if cf:
            crudo = df[cf]
            f = pd.to_datetime(crudo.where(~nulos[cf]), format=self.formato_fecha, dayfirst=self.dayfirst,
                               errors="coerce")
            inval = (~nulos[cf]) & f.isna()
            self._anomalia(archivo, "fecha_invalida", cf, inval.sum(), crudo[inval].head(1).tolist())
            self._anomalia(archivo, "fecha_nula", cf, nulos[cf].sum())
            self.fechas["invalidas"] += int(inval.sum())
            validas = f.dropna()
            self.fechas["validas"] += len(validas)
            if len(validas):
                mn, mx = validas.min(), validas.max()
                self.fechas["min"] = mn if self.fechas["min"] is None else min(self.fechas["min"], mn)
                self.fechas["max"] = mx if self.fechas["max"] is None else max(self.fechas["max"], mx)
            anio, mes = f.dt.year, f.dt.month
        elif ca:
            anio = pd.to_numeric(df[ca], errors="coerce")
            mes = pd.to_numeric(df[cm], errors="coerce") if cm else None
            inval = (~nulos[ca]) & (anio.isna() | ~anio.between(1900, dt.date.today().year))
            self._anomalia(archivo, "anio_invalido", ca, inval.sum(), df[ca][inval].head(1).tolist())
            self.fechas["invalidas"] += int(inval.sum())
            if mes is not None:
                minv = (~nulos[cm]) & (mes.isna() | ~mes.between(1, 12))
                self._anomalia(archivo, "mes_invalido", cm, minv.sum(), df[cm][minv].head(1).tolist())
            ok = anio[~inval].dropna()
            self.fechas["validas"] += len(ok)
            if len(ok):
                self.fechas["min"] = int(ok.min()) if self.fechas["min"] is None else min(self.fechas["min"], int(ok.min()))
                self.fechas["max"] = int(ok.max()) if self.fechas["max"] is None else max(self.fechas["max"], int(ok.max()))
            anio = anio.where(~inval)
        else:
            return None, None
        fuera = anio.notna() & ~anio.between(self.anio_min, self.anio_max)
        self.fechas["fuera_periodo"] += int(fuera.sum())
        self._anomalia(archivo, f"fuera_de_periodo_{self.anio_min}_{self.anio_max}", cf or ca, fuera.sum(),
                       detalle="No es un error: se excluyen en el filtro de periodo.")
        return anio, mes

    # ---- resultados
    @staticmethod
    def _dups(lista):
        if not lista or not sum(len(x) for x in lista):
            return {"filas": 0, "unicos": 0, "repetidas": 0, "valores_repetidos": 0, "max_repeticiones": 0}
        _, cuentas = np.unique(np.concatenate(lista), return_counts=True)
        return {"filas": int(cuentas.sum()), "unicos": int(len(cuentas)),
                "repetidas": int(cuentas.sum() - len(cuentas)),
                "valores_repetidos": int((cuentas > 1).sum()), "max_repeticiones": int(cuentas.max())}

    def resultados(self) -> dict:
        dup = {f"exactos_{e}": self._dups(v) for e, v in self.hash_filas.items()}
        if self.col.get("id"):
            dup.update({f"id_{e}": self._dups(v) for e, v in self.hash_ids.items()})
        fmin, fmax = self.fechas["min"], self.fechas["max"]
        return {
            "id": self.id,
            "embudo": dict(self.embudo), "suma_cantidad_embudo": dict(self.suma_embudo),
            "duplicados": dup,
            "fechas": {**self.fechas, "min": None if fmin is None else str(fmin), "max": None if fmax is None else str(fmax)},
            "numericas": {c: e.resumen() for c, e in self.numericas.items()},
        }


# --------------------------------------------------------------------------- orquestación
def resolver_archivos(patrones: list[str], base: Path) -> list[Path]:
    archivos = []
    for p in patrones:
        ruta = p if os.path.isabs(p) else str(base / p)
        encontrados = sorted(glob.glob(ruta))
        if not encontrados:
            raise ErrorAuditoria(f"No se encontró ningún archivo para '{p}' (buscado en {ruta}). "
                                 f"Descargue el archivo o corrija la ruta en el manifiesto.")
        archivos += [Path(x) for x in encontrados]
    return archivos


def validar_fecha_extraccion(fuente: dict):
    fe = fuente.get("fecha_extraccion")
    try:
        dt.date.fromisoformat(str(fe))
    except ValueError:
        raise ErrorAuditoria(f"[{fuente.get('id')}] 'fecha_extraccion' debe indicarse en formato AAAA-MM-DD "
                             f"(valor actual: {fe!r}). Es la fecha en que se descargó el archivo.") from None


def auditar_fuente(fuente: dict, periodo, chunksize: int, base: Path) -> AuditorFuente:
    for k in ("id", "archivos"):
        if not fuente.get(k):
            raise ErrorAuditoria(f"Cada fuente del manifiesto necesita '{k}'.")
    validar_fecha_extraccion(fuente)
    aud = AuditorFuente(fuente, periodo)
    for path in resolver_archivos(fuente["archivos"], base):
        log.info("[%s] %s: calculando SHA-256…", aud.id, path.name)
        info = {"fuente": aud.id, "archivo": path.name, "ruta": ruta_relativa(path),
                "tamano_bytes": path.stat().st_size, "sha256": sha256_archivo(path)}
        meta, bloques = iterar_bloques(path, fuente.get("lectura") or {}, chunksize)
        filas = 0
        for i, bloque in enumerate(bloques):
            filas += aud.procesar_bloque(bloque, path.name, primero=(i == 0))
            log.info("[%s] %s: %s filas procesadas", aud.id, path.name, f"{filas:,}")
        info.update(meta, filas=filas, columnas=len(aud.columnas_por_archivo.get(path.name, [])))
        aud.archivos.append(info)
    return aud


def escribir_salidas(auditores: list[AuditorFuente], fuentes: dict, salida: Path, meta: dict, figuras: bool, minimo: int):
    salida.mkdir(parents=True, exist_ok=True)
    resumen, dicc, nulos, dups, temp, cats, nums, anom, emb, arch = ([] for _ in range(10))
    res_json = {}
    for a in auditores:
        f = fuentes[a.id]
        r = a.resultados()
        res_json[a.id] = r
        arch += a.archivos
        nombres_etapa = {"1_original": "Original", "2_bogota": "Bogotá", "3_periodo": f"{a.anio_min}–{a.anio_max}",
                         "4_hurto": "Hurto"}
        aplica = {"2_bogota": "bogota" in a.filtros, "3_periodo": bool(a.col.get("fecha") or a.col.get("anio")),
                  "4_hurto": "hurto" in a.filtros}
        prev = None
        for k in nombres_etapa:
            n = r["embudo"].get(k, 0)
            emb.append({"fuente": a.id, "etapa": k, "descripcion": nombres_etapa[k],
                        "filtro_aplicado": aplica.get(k, True), "filas": n,
                        "filas_excluidas": None if prev is None else prev - n,
                        "suma_cantidad": r["suma_cantidad_embudo"].get(k) if a.col.get("cantidad") else None})
            prev = n
        idf = r["duplicados"].get("id_final", {})
        filas_final = r["embudo"].get("4_hurto", 0)
        resumen.append({
            "fuente": a.id, "nombre": f.get("nombre", ""), "url": f.get("url", ""),
            "fecha_extraccion": f.get("fecha_extraccion"), "unidad_observacion": f.get("unidad_observacion", ""),
            "n_archivos": len(a.archivos),
            "filas_originales": r["embudo"].get("1_original", 0), "filas_bogota": r["embudo"].get("2_bogota", 0),
            "filas_periodo": r["embudo"].get("3_periodo", 0), "filas_hurto": filas_final,
            "filtro_bogota_aplicado": aplica["2_bogota"], "filtro_hurto_aplicado": aplica["4_hurto"],
            "columna_cantidad": a.col.get("cantidad") or "",
            "suma_cantidad_hurto": r["suma_cantidad_embudo"].get("4_hurto") if a.col.get("cantidad") else None,
            "columna_id": a.col.get("id") or "", "ids_unicos_hurto": idf.get("unicos") if a.col.get("id") else None,
            "duplicados_exactos_hurto": r["duplicados"]["exactos_final"]["repetidas"],
            f"filas_hurto_>=_{minimo}": filas_final >= minimo,
            "estado": "verificado: calculado sobre los archivos listados en resumen_archivos.csv",
        })
        for c, e in a.columnas.items():
            total = e.nulos + e.no_nulos
            dicc.append({"fuente": a.id, "columna": c, "nombres_originales": " | ".join(sorted(e.nombres_originales)),
                         "archivos_con_columna": len(e.archivos), "archivos_totales": len(a.archivos),
                         "tipo_inferido": e.tipo, "valores_unicos": len(e.unicos) if e.unicos is not None else f">{MAX_UNICOS}",
                         "ejemplo": None if e.ejemplo is None else str(e.ejemplo)[:80]})
            nulos.append({"fuente": a.id, "columna": c, "filas_evaluadas": total, "nulos": e.nulos,
                          "pct_nulos": round(100 * e.nulos / total, 4) if total else None,
                          "nota": "" if len(e.archivos) == len(a.archivos) else
                          "columna ausente en algunos archivos: solo se cuentan filas de archivos que la contienen"})
        for k, d in r["duplicados"].items():
            tipo, etapa = k.split("_", 1)
            dups.append({"fuente": a.id, "tipo": "fila_exacta" if tipo == "exactos" else f"id:{a.col.get('id')}",
                         "etapa": etapa, **d})
        for etapa in ("original", "final"):
            for (an, me), n in sorted(a.temporal[etapa].items()):
                temp.append({"fuente": a.id, "etapa": etapa, "anio": an if an != -1 else None,
                             "mes": me if me != -1 else None, "filas": n,
                             "suma_cantidad": a.temporal_suma[etapa][(an, me)] if a.col.get("cantidad") else None})
            for c, cont in a.categoricas.items():
                tot = sum(cont[etapa].values())
                top = cont[etapa].most_common(TOP_CATEGORIAS)
                for v, n in top:
                    cats.append({"fuente": a.id, "etapa": etapa, "columna": c, "valor": v, "filas": n,
                                 "pct": round(100 * n / tot, 4) if tot else None, "categorias_distintas": len(cont[etapa])})
                resto = tot - sum(n for _, n in top)
                if resto:
                    cats.append({"fuente": a.id, "etapa": etapa, "columna": c, "valor": "(otras categorías)", "filas": resto,
                                 "pct": round(100 * resto / tot, 4), "categorias_distintas": len(cont[etapa])})
        for c, s in r["numericas"].items():
            nums.append({"fuente": a.id, "columna": c, **s})
        anom += a.anomalias
        r["localidad"] = {e: dict(a.localidad[e].most_common()) for e in a.localidad}

    def csv_(nombre, filas):
        pd.DataFrame(filas).to_csv(salida / nombre, index=False, encoding="utf-8")

    csv_("resumen_fuentes.csv", resumen)
    csv_("resumen_archivos.csv", arch)
    csv_("embudo_filtros.csv", emb)
    csv_("diccionario_variables.csv", dicc)
    csv_("valores_nulos.csv", nulos)
    csv_("duplicados.csv", dups)
    csv_("cobertura_temporal.csv", temp)
    csv_("distribuciones_categoricas.csv", cats)
    csv_("estadisticas_numericas.csv", nums)
    anom_df = pd.DataFrame(anom, columns=["fuente", "archivo", "tipo", "columna", "filas", "ejemplo", "detalle"])
    if not anom_df.empty:
        anom_df = anom_df.groupby(["fuente", "archivo", "tipo", "columna", "detalle"], dropna=False, as_index=False) \
            .agg(filas=("filas", "sum"), ejemplo=("ejemplo", "first"))
    anom_df.to_csv(salida / "anomalias.csv", index=False, encoding="utf-8")

    doc = {"metadatos": meta, "resumen_fuentes": resumen, "archivos": arch, "embudo": emb, "detalle": res_json}
    (salida / "auditoria.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (salida / "reporte_auditoria.md").write_text(reporte_md(doc, minimo, anom_df), encoding="utf-8")
    if figuras:
        generar_figuras(auditores, salida / "figuras")


def _miles(x) -> str:
    """Formato con punto de miles (convención en español): 1234567 -> '1.234.567'."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:,.0f}".replace(",", ".")


def reporte_md(doc: dict, minimo: int, anom: pd.DataFrame) -> str:
    m = doc["metadatos"]
    fmt = _miles
    L = [f"# Reporte de auditoría de datasets", "",
         f"- Ejecución: {m['fecha_ejecucion']}  ", f"- Script: `scripts/auditoria_datasets.py` v{m['versiones']['script']}  ",
         f"- Configuración: `{m['config']}` (SHA-256 `{m.get('config_sha256', '')}`)  ",
         f"- Periodo: {m['periodo'][0]}–{m['periodo'][1]} · Bloque: {_miles(m['chunksize'])} filas · Semilla: {m['semilla']}  ",
         f"- Versiones: " + ", ".join(f"{k} {v}" for k, v in m["versiones"].items() if k != "plataforma"), "",
         "> Todas las cifras se calcularon leyendo los archivos listados abajo. **Las fuentes no se suman entre sí**: "
         "Línea 123, Policía y Fiscalía tienen unidades de observación distintas.", "",
         "## Archivos procesados", "", "| Fuente | Archivo | Bytes | SHA-256 | Filas | Columnas |", "|---|---|---:|---|---:|---:|"]
    for a in doc["archivos"]:
        L.append(f"| {a['fuente']} | `{a['archivo']}` | {_miles(a['tamano_bytes'])} | `{a['sha256'][:16]}…` | {_miles(a['filas'])} | {a['columnas']} |")
    L += ["", f"## Requisito de {_miles(minimo)} registros", "",
          "| Fuente | Filas originales | Filas Bogotá | Filas periodo | Filas relacionadas con hurto | Suma cantidad (hurto) | IDs únicos (hurto) | Unidad de observación |",
          "|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in doc["resumen_fuentes"]:
        nb = "" if r["filtro_bogota_aplicado"] else " (filtro no aplica)"
        nh = "" if r["filtro_hurto_aplicado"] else " (filtro no aplica)"
        L.append(f"| {r['fuente']} | {fmt(r['filas_originales'])} | {fmt(r['filas_bogota'])}{nb} | {fmt(r['filas_periodo'])} | "
                 f"{fmt(r['filas_hurto'])}{nh} | {fmt(r['suma_cantidad_hurto'])} | {fmt(r['ids_unicos_hurto'])} | {r['unidad_observacion']} |")
    L += ["", "Lectura de la tabla:", "",
          "- *Filas* = registros del archivo; *suma cantidad* = suma de la variable de conteo (p. ej. `CANT_INCIDENTES`); "
          "*IDs únicos* = identificadores distintos (p. ej. procesos). No son intercambiables.",
          f"- Una fuente cumple el umbral solo si sus **filas relacionadas con hurto**, en una única unidad de observación, "
          f"son ≥ {_miles(minimo)}. La validez de esa población para el proyecto debe acordarse (issue de decisión metodológica).", "",
          "## Embudo de filtros", "", "| Fuente | Etapa | ¿Aplica? | Filas | Excluidas | Suma cantidad |", "|---|---|---|---:|---:|---:|"]
    for e in doc["embudo"]:
        L.append(f"| {e['fuente']} | {e['descripcion']} | {'sí' if e['filtro_aplicado'] else 'no'} | {fmt(e['filas'])} | "
                 f"{fmt(e['filas_excluidas'])} | {fmt(e['suma_cantidad'])} |")
    L += ["", "## Anomalías detectadas", ""]
    if anom.empty:
        L.append("No se detectaron anomalías con las reglas configuradas.")
    else:
        L += ["| Fuente | Archivo | Tipo | Columna | Filas |", "|---|---|---|---|---:|"]
        for _, x in anom.iterrows():
            L.append(f"| {x['fuente']} | `{x['archivo']}` | {x['tipo']} | {x['columna']} | {_miles(int(x['filas']))} |")
    L += ["", "Detalle completo en los CSV de esta carpeta y en `auditoria.json`.", ""]
    return "\n".join(L)


def generar_figuras(auditores: list[AuditorFuente], carpeta: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    carpeta.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 200, "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})

    def guardar(fig, nombre):
        fig.tight_layout()
        for ext in ("png", "pdf"):
            fig.savefig(carpeta / f"{nombre}.{ext}", bbox_inches="tight")
        plt.close(fig)

    for a in auditores:
        r = a.resultados()
        # 1. embudo
        etapas = ["1_original", "2_bogota", "3_periodo", "4_hurto"]
        etiquetas = ["Original", "Bogotá", f"{a.anio_min}–{a.anio_max}", "Hurto"]
        vals = [r["embudo"].get(e, 0) for e in etapas]
        fig, ax = plt.subplots(figsize=(6.5, 3.2))
        ax.barh(etiquetas[::-1], vals[::-1], color="#174778")
        for i, v in enumerate(vals[::-1]):
            ax.text(v, i, " " + _miles(v), va="center", fontsize=9)
        ax.set_xlabel("Filas")
        ax.set_title(f"{a.id}: filas tras cada filtro acumulado")
        ax.set_xlim(0, max(vals) * 1.22 if max(vals) else 1)
        guardar(fig, f"{a.id}_embudo")
        # 2. serie mensual (población final)
        serie = {k: v for k, v in a.temporal["final"].items() if k[0] != -1}
        if serie:
            df = pd.DataFrame([(an, me, n, a.temporal_suma["final"][(an, me)]) for (an, me), n in serie.items()],
                              columns=["anio", "mes", "filas", "suma"]).sort_values(["anio", "mes"])
            if (df["mes"] > 0).all():
                x = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))
                titulo = "mensual"
            else:
                df = df.groupby("anio", as_index=False)[["filas", "suma"]].sum()
                x = df["anio"].astype(int)
                titulo = "anual"
            fig, ax = plt.subplots(figsize=(7.5, 3.4))
            ax.plot(x, df["filas"], color="#174778", lw=1.6, label="Filas")
            if a.col.get("cantidad"):
                ax2 = ax.twinx()
                ax2.plot(x, df["suma"], color="#c0504d", lw=1.2, ls="--", label=f"Suma {a.col['cantidad']}")
                ax2.set_ylabel(f"Suma {a.col['cantidad']}")
                ax2.spines["top"].set_visible(False)
                fig.legend(loc="upper left", bbox_to_anchor=(0.08, 0.95), frameon=False, fontsize=8)
            ax.set_ylabel("Filas")
            ax.set_title(f"{a.id}: registros de la población final ({titulo})")
            guardar(fig, f"{a.id}_serie_{titulo}")
        # 3. nulos
        nn = sorted(((c, 100 * e.nulos / (e.nulos + e.no_nulos)) for c, e in a.columnas.items()
                     if e.nulos + e.no_nulos), key=lambda t: t[1], reverse=True)[:15]
        if nn and nn[0][1] > 0:
            fig, ax = plt.subplots(figsize=(6.5, 0.3 * len(nn) + 1.2))
            ax.barh([c for c, _ in nn][::-1], [p for _, p in nn][::-1], color="#7f7f7f")
            ax.set_xlabel("% de valores nulos")
            ax.set_title(f"{a.id}: columnas con más valores nulos")
            guardar(fig, f"{a.id}_nulos")
        # 4. localidad
        loc = a.localidad["final"].most_common(25)
        if loc:
            fig, ax = plt.subplots(figsize=(6.5, 0.28 * len(loc) + 1.2))
            ax.barh([k for k, _ in loc][::-1], [v for _, v in loc][::-1], color="#174778")
            ax.set_xlabel("Filas")
            ax.set_title(f"{a.id}: población final por localidad")
            guardar(fig, f"{a.id}_localidad")


# --------------------------------------------------------------------------- CLI
def _filtro_cli(texto: str | None):
    if not texto:
        return None
    if "=" not in texto:
        raise ErrorAuditoria(f"Filtro '{texto}' inválido: use COLUMNA=REGEX, p. ej. cod_dane_hecho=^11001")
    c, p = texto.split("=", 1)
    return {"columna": c, "patron": p}


def config_desde_cli(a) -> dict:
    return {"periodo": {"anio_min": a.anio_min, "anio_max": a.anio_max}, "fuentes": [{
        "id": a.fuente_id, "nombre": a.nombre or a.fuente_id, "url": a.url or "", "fecha_extraccion": a.fecha_extraccion,
        "unidad_observacion": a.unidad or "", "archivos": a.archivo,
        "lectura": {"encoding": a.encoding, "sep": a.sep, "hoja": a.hoja, "fila_encabezado": a.fila_encabezado},
        "columnas": {"fecha": a.col_fecha, "formato_fecha": a.formato_fecha, "dayfirst": a.dayfirst, "anio": a.col_anio,
                     "mes": a.col_mes, "id": a.col_id, "cantidad": a.col_cantidad, "localidad": a.col_localidad,
                     "delito": a.col_delito},
        "filtros": {"bogota": _filtro_cli(a.filtro_bogota), "hurto": _filtro_cli(a.filtro_hurto)},
    }]}


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Auditoría reproducible de datasets (AD-DelitosBog).",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso principal")[1])
    g = p.add_argument_group("modo manifiesto")
    g.add_argument("--config", help="Manifiesto JSON con las fuentes (ver config/fuentes_auditoria.example.json).")
    g.add_argument("--fuentes", nargs="+", help="Auditar solo estas fuentes (por id) del manifiesto.")
    c = p.add_argument_group("modo archivo individual")
    c.add_argument("--archivo", action="append", help="Ruta o patrón glob. Repetible.")
    c.add_argument("--fuente-id", default="fuente")
    c.add_argument("--nombre"); c.add_argument("--url"); c.add_argument("--unidad", help="Unidad de observación.")
    c.add_argument("--fecha-extraccion", help="Fecha de descarga del archivo, AAAA-MM-DD (obligatoria).")
    c.add_argument("--encoding", default="auto"); c.add_argument("--sep", default="auto")
    c.add_argument("--hoja", default=0); c.add_argument("--fila-encabezado", type=int, default=0)
    for col in ("fecha", "anio", "mes", "id", "cantidad", "localidad", "delito"):
        c.add_argument(f"--col-{col}")
    c.add_argument("--formato-fecha", help="Formato strftime, p. ej. %%Y-%%m-%%d o %%d/%%m/%%Y.")
    c.add_argument("--dayfirst", action="store_true", help="Interpretar fechas ambiguas como día/mes.")
    c.add_argument("--filtro-bogota", help="COLUMNA=REGEX (sobre texto en mayúsculas y sin tildes).")
    c.add_argument("--filtro-hurto", help="COLUMNA=REGEX (sobre texto en mayúsculas y sin tildes).")
    c.add_argument("--anio-min", type=int, default=2018); c.add_argument("--anio-max", type=int, default=2025)
    o = p.add_argument_group("salida")
    o.add_argument("--salida", default="outputs/auditoria")
    o.add_argument("--chunksize", type=int, default=200_000, help="Filas por bloque (por defecto 200000).")
    o.add_argument("--minimo", type=int, default=MINIMO_REGISTROS)
    o.add_argument("--sin-figuras", action="store_true")
    o.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv=None) -> int:
    args = construir_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    np.random.seed(SEMILLA)  # la auditoría es determinista; se fija por consistencia del proyecto
    try:
        if args.config:
            ruta_cfg = Path(args.config)
            if not ruta_cfg.exists():
                raise ErrorAuditoria(f"No existe el manifiesto {ruta_cfg}. Copie config/fuentes_auditoria.example.json.")
            try:
                cfg = json.loads(ruta_cfg.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise ErrorAuditoria(f"{ruta_cfg}: JSON inválido ({e}).") from e
            base = ruta_cfg.resolve().parent.parent if ruta_cfg.resolve().parent.name == "config" else Path.cwd()
            cfg_sha = sha256_archivo(ruta_cfg)
        elif args.archivo:
            cfg, base, ruta_cfg, cfg_sha = config_desde_cli(args), Path.cwd(), Path("(línea de comandos)"), ""
        else:
            raise ErrorAuditoria("Indique --config MANIFIESTO.json o al menos un --archivo.")
        periodo = (int(cfg.get("periodo", {}).get("anio_min", 2018)), int(cfg.get("periodo", {}).get("anio_max", 2025)))
        fuentes = [f for f in cfg.get("fuentes", []) if not args.fuentes or f.get("id") in args.fuentes]
        if not fuentes:
            raise ErrorAuditoria("El manifiesto no contiene fuentes (o ninguna coincide con --fuentes).")
        ids = [f.get("id") for f in fuentes]
        if len(set(ids)) != len(ids):
            raise ErrorAuditoria(f"Hay ids de fuente repetidos: {ids}")
        if args.chunksize < 1:
            raise ErrorAuditoria("--chunksize debe ser positivo.")
        auditores = [auditar_fuente(f, periodo, args.chunksize, base) for f in fuentes]
        meta = {"fecha_ejecucion": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "comando": " ".join(["python", "scripts/auditoria_datasets.py", *(argv if argv is not None else sys.argv[1:])]),
                "config": ruta_relativa(ruta_cfg) if ruta_cfg.exists() else str(ruta_cfg), "config_sha256": cfg_sha,
                "periodo": periodo, "chunksize": args.chunksize, "semilla": SEMILLA, "minimo_registros": args.minimo,
                "versiones": versiones()}
        escribir_salidas(auditores, {f["id"]: f for f in fuentes}, Path(args.salida), meta, not args.sin_figuras, args.minimo)
        log.info("Auditoría completada. Resultados en %s", args.salida)
        return 0
    except ErrorAuditoria as e:
        log.error("%s", e)
        return 2
    except (FileNotFoundError, PermissionError) as e:
        log.error("No se pudo abrir un archivo: %s", e)
        return 3


if __name__ == "__main__":
    sys.exit(main())
