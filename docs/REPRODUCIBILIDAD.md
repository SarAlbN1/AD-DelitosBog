# Guía de reproducción

Versión de la Entrega 1: obtención de las fuentes y auditoría. Se actualizará con el preprocesamiento (Entrega 2) y el modelado (Entrega 3). Issue: #6.

> **Antes de empezar: dos tipos de reproducción.**
>
> Las tres fuentes son conjuntos **vivos**: se actualizan con nuevos meses y con correcciones. Por eso hay dos formas de reproducir:
>
> | Modo | Qué se reproduce | Qué debe coincidir |
> |---|---|---|
> | **A. Copia congelada** (la del informe) | La auditoría sobre los mismos archivos que usó el equipo, compartidos por un canal privado (no GitHub) | SHA-256 de cada archivo **y** todas las cifras de `outputs/auditoria/` |
> | **B. Descarga nueva** | El procedimiento completo, con datos del día | Solo la estructura (columnas, filtros, embudo). Los hashes y las cifras **cambiarán** y eso no es un error |
>
> Las cifras del informe corresponden al modo A.

## 1. Entorno

Requisitos:
- Python 3.10 o superior. El equipo usó Python 3.14.5 en Windows 11.
- Git.
- Unos 2 GB libres en disco.

```bash
git clone https://github.com/SarAlbN1/AD-DelitosBog.git
cd AD-DelitosBog
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux / macOS:          source .venv/bin/activate
pip install -r requirements.txt
pytest -q tests
```

`pytest` debe terminar en `15 passed`. Las pruebas usan datos sintéticos y solo validan el código.

Los datos van en `data/raw/<fuente>/`. Esa carpeta está en `.gitignore`: **nunca** se suben datos a GitHub.

## 2. Obtención de las fuentes

### 2.1 Línea 123: incidentes tramitados C4 (SDSCJ)

- **Página del dataset:** https://datosabiertos.bogota.gov.co/dataset/incidentes
- **Recurso principal:** `30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef`, «Llamadas Tramitadas C4 Bogotá NUSE Línea 123 enero 2015 – septiembre 2026». Su última modificación en el portal fue el 2026-10-22.
- **Descarga usada:** 2026-11-11.

```bash
mkdir -p data/raw/linea123 && cd data/raw/linea123
B=https://datosabiertos.bogota.gov.co/dataset/9bdf518e-b756-4865-983f-0521111fbcd1/resource
curl -LO "$B/30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef/download/datos-abiertllamadastramitadas-c4-bogota_numerounicodeseguridadyemergencias-nuse_linea-123os-nus.csv"
# Documentación (solo consulta; definicioncampos.csv está desactualizado):
curl -LO "$B/93eb31c6-be3b-43ed-a633-a47ed3c7c5e7/download/definicioncampos.csv"
curl -LO "$B/fa426f3f-b2b0-491b-8287-dfeca438f558/download/guiatipificacionincidentes.csv"
curl -LO "$B/76a0e207-87fb-4802-b3da-188a3f64dcaf/download/metadatos.csv"
cd ../../..
```

Para saber si el recurso cambió desde la descarga, consulte su fecha de modificación:

```bash
curl -s "https://datosabiertos.bogota.gov.co/api/3/action/package_show?id=incidentes"
```

Busque `last_modified` del recurso `30d65a8b…`.

### 2.2 Fiscalía: Procesos Fiscalía V3 (datos.gov.co, `dbdv-iihs`)

El archivo completo es nacional y muy pesado, así que se descarga solo el subconjunto de Bogotá y capítulo «Del Hurto» por la API Socrata:

```bash
python scripts/descargar_fiscalia.py
# equivale a: --where "cod_dane_hecho='11001' AND capitulo_delito='Del Hurto'" --salida data/raw/fiscalia
```

Cómo funciona el script:
- Pide páginas de 100.000 filas ordenadas por `:id`, para que la paginación sea estable.
- Compara el total descargado con `count(*)` de la misma consulta.
- Deja `data/raw/fiscalia/fiscalia_v3_bogota_hurto.metadatos.json` con la consulta, las fechas, los conteos, la `fecha_corte_datos` y el SHA-256.
- Si se interrumpe, al volver a ejecutarlo reanuda desde `data/raw/fiscalia/_paginas/`. Esa carpeta puede borrarse cuando termina.

La descarga usada en el informe tiene `fecha_corte_datos = 31/10/2026` y `count(*) = 2.002.177`. Tardó en total unos 50 minutos, en varias sesiones.

### 2.3 Policía Nacional: delitos a nivel de registro

**Estado: en curso (#10, #15).** La población principal depende de la decisión D-01 (`docs/decisiones.md`).

1. Desde https://www.policia.gov.co/estadistica-delictiva descargue los archivos «Información de delitos a nivel de registro» de los años del periodo. Hoy están publicados 2020–2026; 2018 y 2019 no aparecen.
2. Guárdelos sin modificarlos en `data/raw/policia_registro/`.
3. Los años 2022 y 2023 vienen en `.zip`: descomprímalos en la misma carpeta, porque el script solo lee un CSV dentro de un `.zip`.
4. Agregue al manifiesto la entrada verificada de `docs/evidencia_policia_registro.md`, §5.

Cada archivo trae todos los delitos del país. El filtro de la auditoría se queda con `CODIGO DANE` = 11001 y `DELITOS` = «(05022) Hurto a personas».

## 3. Verificación de integridad (SHA-256)

Calcule el hash de cada archivo y compárelo con la columna `sha256` de `outputs/auditoria/resumen_archivos.csv`:

```bash
# Linux / macOS / Git Bash
sha256sum data/raw/linea123/*.csv data/raw/fiscalia/*.csv data/raw/policia_registro/*.xlsx
```

```powershell
# PowerShell
Get-FileHash data\raw\linea123\*.csv, data\raw\fiscalia\*.csv -Algorithm SHA256 | Format-List
```

| Fuente | Archivo | Bytes | SHA-256 |
|---|---|---:|---|
| Línea 123 | `datos-abiertllamadastramitadas-c4-…-nus.csv` | 116.322.990 | `ceeee37729c83adaae6907272457998cc5a60eaf57c14a5ead17c6db2d3a4d61` |
| Fiscalía | `fiscalia_v3_bogota_hurto.csv` | 856.092.926 | `e2f30087b82544e448d0c3f9f04eabd760012b2143e2ab2af632e1d81ff8f2ae` |
| Policía | `INFORMACIÓN_DE_DELITOS_A_NIVEL_DE_REGISTRO_AÑO_2024_3.xlsx` (copia local `delitos_registro_2024.xlsx`) | 40.514.443 | `e472b63bc021d08b442affcde589262e8377d196e9764a41bfa0f99b0cc179ba` (solo inspección; aún no está en la auditoría oficial) |

- **Modo A:** si un hash no coincide, el archivo no es la copia congelada. No continúe con ese archivo.
- **Modo B:** se espera que los hashes difieran. Registre los nuevos en el PR.

## 4. Auditoría

```bash
python scripts/auditoria_datasets.py --config config/fuentes_auditoria.json
```

- **Ejecute siempre todas las fuentes juntas.** Con `--fuentes`, el script reescribe `outputs/auditoria/` solo con la fuente pedida y se pierden las demás.
- **Tiempo:** con Línea 123 y Fiscalía tardó 106 s (Windows 11, Python 3.14, 2026-11-11).
- **Memoria:** si se queda corta, use `--chunksize 50000`.
- **Códigos de salida:** `0` correcto · `2` error de configuración o de datos (el mensaje dice qué corregir) · `3` archivo inaccesible.

### Cifras esperadas (modo A)

Fuente: `outputs/auditoria/resumen_fuentes.csv`.

| Fuente | Filas originales | Filas 2018–2025 | Filas de hurto | Suma de cantidad | IDs únicos (hurto) |
|---|---:|---:|---:|---:|---:|
| Línea 123 | 1.117.394 | 763.074 | 25.144 | 1.094.313 incidentes | 24.978 |
| Fiscalía | 2.002.177 | 1.300.703 | 1.300.703 | — | 1.297.042 procesos |

Estas cifras están en unidades distintas y **no se suman entre fuentes**. El detalle está en `docs/AUDITORIA.md` y en el issue #22.

En el modo A, la reproducción es correcta si `resumen_fuentes.csv`, `embudo_filtros.csv` y `duplicados.csv` coinciden **exactamente** con los del repositorio. Para comprobarlo, sin modificar los archivos versionados:

```bash
python scripts/auditoria_datasets.py --config config/fuentes_auditoria.json --salida /tmp/aud_repro --sin-figuras
diff outputs/auditoria/resumen_fuentes.csv /tmp/aud_repro/resumen_fuentes.csv
diff outputs/auditoria/embudo_filtros.csv  /tmp/aud_repro/embudo_filtros.csv
```

`diff` sin salida significa que las cifras coinciden. El autor de la guía hizo esta comprobación el 2026-11-11: las tres tablas fueron idénticas. Para cerrar #6 falta que la repita otra persona.

## 5. Registro de la reproducción

Para cerrar #6, quien reproduce (distinto del autor) comenta en el issue:
- el modo (A o B) y la fecha;
- el sistema operativo y la versión de Python;
- los hashes obtenidos y si coinciden;
- el resultado de `pytest`;
- la salida de los `diff` de la sección 4;
- los pasos de esta guía que no funcionaron o no estaban claros, para corregirla.
