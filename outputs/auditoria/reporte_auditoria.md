# Reporte de auditoría de datasets

- Ejecución: 2026-11-11T14:36:38-05:00  
- Script: `scripts/auditoria_datasets.py` v0.1.0  
- Configuración: `config/fuentes_auditoria.json` (SHA-256 `a27c64e06285f838857f2f2fd5fd2aa6a69c30960af3347649dbfa0a7a329d3c`)  
- Periodo: 2018–2025 · Bloque: 100.000 filas · Semilla: 42  
- Versiones: python 3.14.5, pandas 3.1.1, numpy 2.5.4, script 0.1.0, matplotlib 3.11.2, openpyxl 3.1.5, xlrd 2.0.2

> Todas las cifras se calcularon leyendo los archivos listados abajo. **Las fuentes no se suman entre sí**: Línea 123, Policía y Fiscalía tienen unidades de observación distintas.

## Archivos procesados

| Fuente | Archivo | Bytes | SHA-256 | Filas | Columnas |
|---|---|---:|---|---:|---:|
| fiscalia | `fiscalia_v3_bogota_hurto.csv` | 856.092.926 | `e2f30087b82544e4…` | 2.002.177 | 29 |

## Requisito de 500.000 registros

| Fuente | Filas originales | Filas Bogotá | Filas periodo | Filas relacionadas con hurto | Suma cantidad (hurto) | IDs únicos (hurto) | Unidad de observación |
|---|---:|---:|---:|---:|---:|---:|---|
| fiscalia | 2.002.177 | 2.002.177 | 1.300.703 | 1.300.703 | — | 1.297.042 | Fila proceso–delito (noticia criminal); un proceso puede repetirse |

Lectura de la tabla:

- *Filas* = registros del archivo; *suma cantidad* = suma de la variable de conteo (p. ej. `CANT_INCIDENTES`); *IDs únicos* = identificadores distintos (p. ej. procesos). No son intercambiables.
- Una fuente cumple el umbral solo si sus **filas relacionadas con hurto**, en una única unidad de observación, son ≥ 500.000. La validez de esa población para el proyecto debe acordarse (issue de decisión metodológica).

## Embudo de filtros

| Fuente | Etapa | ¿Aplica? | Filas | Excluidas | Suma cantidad |
|---|---|---|---:|---:|---:|
| fiscalia | Original | sí | 2.002.177 | — | — |
| fiscalia | Bogotá | sí | 2.002.177 | 0 | — |
| fiscalia | 2018–2025 | sí | 1.300.703 | 701.474 | — |
| fiscalia | Hurto | sí | 1.300.703 | 0 | — |

## Anomalías detectadas

| Fuente | Archivo | Tipo | Columna | Filas |
|---|---|---|---|---:|
| fiscalia | `fiscalia_v3_bogota_hurto.csv` | anio_invalido | a_o_hecho | 767 |
| fiscalia | `fiscalia_v3_bogota_hurto.csv` | fuera_de_periodo_2018_2025 | a_o_hecho | 700.707 |
| fiscalia | `fiscalia_v3_bogota_hurto.csv` | mes_invalido | mes_hecho | 767 |

Detalle completo en los CSV de esta carpeta y en `auditoria.json`.
