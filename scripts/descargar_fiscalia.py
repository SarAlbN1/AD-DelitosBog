#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Descarga reproducible de Procesos Fiscalía V3 (datos.gov.co, recurso dbdv-iihs) vía API Socrata.

Descarga por páginas ordenadas por el identificador interno (:id) para que la paginación sea
estable, verifica que el total de filas descargadas coincida con count(*) de la MISMA consulta
y deja un archivo de metadatos (consulta, fechas, conteos, SHA-256) junto al CSV.

    python scripts/descargar_fiscalia.py
    python scripts/descargar_fiscalia.py --where "cod_dane_hecho='11001'" --salida data/raw/fiscalia

Solo usa la biblioteca estándar. Si se interrumpe, al volver a ejecutarlo reanuda desde las
páginas ya descargadas (carpeta _paginas/), siempre que la consulta sea la misma.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://www.datos.gov.co/resource/dbdv-iihs"
WHERE_DEFECTO = "cod_dane_hecho='11001' AND capitulo_delito='Del Hurto'"
USER_AGENT = "AD-DelitosBog-auditoria/1.0 (proyecto academico)"


def pedir(url, intentos=6, timeout=900):
    for k in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            espera = 15 * 2 ** k
            print(f"  intento {k + 1}/{intentos} falló ({e}); reintento en {espera}s", flush=True)
            time.sleep(espera)
    sys.exit(f"No se pudo completar la petición tras {intentos} intentos: {url}")


def url(ext, **params):
    return f"{BASE}.{ext}?" + urllib.parse.urlencode({f"${k}": v for k, v in params.items()})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--where", default=WHERE_DEFECTO, help=f"Filtro SoQL (por defecto: {WHERE_DEFECTO})")
    ap.add_argument("--salida", default="data/raw/fiscalia")
    ap.add_argument("--nombre", default="fiscalia_v3_bogota_hurto.csv")
    ap.add_argument("--pagina", type=int, default=100_000, help="Filas por página")
    a = ap.parse_args()

    salida = Path(a.salida)
    paginas = salida / "_paginas"
    paginas.mkdir(parents=True, exist_ok=True)
    clave = hashlib.sha256(a.where.encode()).hexdigest()[:12]
    inicio = dt.datetime.now().astimezone()

    print("Consultando count(*) de la consulta…", flush=True)
    esperado = int(json.loads(pedir(url("json", select="count(*) as n", where=a.where)))[0]["n"])
    print(f"Filas esperadas: {esperado:,}", flush=True)

    total, n_pag = 0, (esperado + a.pagina - 1) // a.pagina
    for i in range(n_pag):
        p = paginas / f"{clave}_{i:04d}.csv"
        if not p.exists():
            t = time.time()
            datos = pedir(url("csv", where=a.where, order=":id", limit=a.pagina, offset=i * a.pagina))
            p.with_suffix(".tmp").write_bytes(datos)
            p.with_suffix(".tmp").replace(p)
            print(f"  página {i + 1}/{n_pag} ({time.time() - t:.0f}s)", flush=True)
        with open(p, encoding="utf-8", newline="") as f:
            total += sum(1 for _ in csv.reader(f)) - 1
    if total != esperado:
        sys.exit(f"ERROR: se descargaron {total:,} filas pero count(*) = {esperado:,}. "
                 f"El dataset pudo actualizarse durante la descarga; borre {paginas} y repita.")

    destino = salida / a.nombre
    h = hashlib.sha256()
    with open(destino, "w", encoding="utf-8", newline="") as out:
        for i in range(n_pag):
            texto = (paginas / f"{clave}_{i:04d}.csv").read_text(encoding="utf-8")
            if i:
                texto = texto.split("\n", 1)[1] if "\n" in texto else ""
            out.write(texto)
    with open(destino, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)

    corte = json.loads(pedir(url("json", select="fecha_corte_datos,count(*) as n", where=a.where,
                                 group="fecha_corte_datos")))
    meta = {
        "fuente": "Fiscalía General de la Nación — Procesos Fiscalía V3",
        "url_dataset": "https://www.datos.gov.co/d/dbdv-iihs",
        "endpoint": f"{BASE}.csv",
        "consulta": {"$where": a.where, "$order": ":id", "pagina": a.pagina},
        "fecha_extraccion": inicio.date().isoformat(),
        "inicio": inicio.isoformat(timespec="seconds"),
        "fin": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "filas_count_api": esperado,
        "filas_descargadas": total,
        "fecha_corte_datos": corte,
        "archivo": destino.name,
        "tamano_bytes": destino.stat().st_size,
        "sha256": h.hexdigest(),
    }
    (salida / (destino.stem + ".metadatos.json")).write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                                             encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print("\nPuede borrar la carpeta _paginas/ cuando haya verificado el archivo final.")


if __name__ == "__main__":
    main()
