# Reporte de auditoría de datasets

- Ejecución: 2026-11-11T21:47:32-05:00  
- Script: `scripts/auditoria_datasets.py` v0.1.0  
- Configuración: `config/fuentes_auditoria.json` (SHA-256 `28697f71d25b6bc0dec8545986694bf1d6379ea3243bd5f1d0dfa390efc4ca29`)  
- Periodo: 2018–2025 · Bloque: 200.000 filas · Semilla: 42  
- Versiones: python 3.9.6, pandas 2.3.3, numpy 2.0.2, script 0.1.0, matplotlib 3.9.4, openpyxl 3.1.5, xlrd no instalado

> Todas las cifras se calcularon leyendo los archivos listados abajo. **Las fuentes no se suman entre sí**: Línea 123, Policía y Fiscalía tienen unidades de observación distintas.

## Archivos procesados

| Fuente | Archivo | Bytes | SHA-256 | Filas | Columnas |
|---|---|---:|---|---:|---:|
| policia_registro | `delitos_registro_2020.csv` | 89.761.340 | `aa2f39e87d899929…` | 651.206 | 11 |
| policia_registro | `delitos_registro_2021.csv` | 108.736.152 | `952334b45f2c1ae8…` | 792.244 | 11 |
| policia_registro | `delitos_registro_2022.csv` | 116.927.234 | `8e22e2d1f40a3eed…` | 862.451 | 11 |
| policia_registro | `delitos_registro_2023.csv` | 119.693.738 | `d5d34adc3e3f9be7…` | 917.544 | 10 |
| policia_registro | `delitos_registro_2024.csv` | 115.517.990 | `621a8cd32b6d9194…` | 832.475 | 11 |
| policia_registro | `delitos_registro_2025.csv` | 107.524.820 | `e8c80f134bc26069…` | 773.950 | 11 |
| policia_agregado | `hurto_bogota.csv` | 213.332 | `32cda715025fc89c…` | 2.922 | 6 |

## Requisito de 500.000 registros

| Fuente | Filas originales | Filas Bogotá | Filas periodo | Filas relacionadas con hurto | Suma cantidad (hurto) | IDs únicos (hurto) | Unidad de observación |
|---|---:|---:|---:|---:|---:|---:|---|
| policia_registro | 4.829.870 | 1.406.157 | 1.406.157 | 741.986 | 741.986 | — | Una fila por víctima o registro, con CANTIDAD = 1 |
| policia_agregado | 2.922 | 2.922 | 2.922 | 2.922 (filtro no aplica) | 975.793 | — | Agregado fecha × municipio; cantidad = hurtos registrados ese día |

Lectura de la tabla:

- *Filas* = registros del archivo; *suma cantidad* = suma de la variable de conteo (p. ej. `CANT_INCIDENTES`); *IDs únicos* = identificadores distintos (p. ej. procesos). No son intercambiables.
- Una fuente cumple el umbral solo si sus **filas relacionadas con hurto**, en una única unidad de observación, son ≥ 500.000. La validez de esa población para el proyecto debe acordarse (issue de decisión metodológica).

## Embudo de filtros

| Fuente | Etapa | ¿Aplica? | Filas | Excluidas | Suma cantidad |
|---|---|---|---:|---:|---:|
| policia_registro | Original | sí | 4.829.870 | — | 4.829.870 |
| policia_registro | Bogotá | sí | 1.406.157 | 3.423.713 | 1.406.157 |
| policia_registro | 2018–2025 | sí | 1.406.157 | 0 | 1.406.157 |
| policia_registro | Hurto | sí | 741.986 | 664.171 | 741.986 |
| policia_agregado | Original | sí | 2.922 | — | 975.793 |
| policia_agregado | Bogotá | sí | 2.922 | 0 | 975.793 |
| policia_agregado | 2018–2025 | sí | 2.922 | 0 | 975.793 |
| policia_agregado | Hurto | no | 2.922 | 0 | 975.793 |

## Anomalías detectadas

No se detectaron anomalías con las reglas configuradas.

Detalle completo en los CSV de esta carpeta y en `auditoria.json`.
