# Evidencia preliminar: Procesos Fiscalía V3 (consulta a la API)

> **Estado: PRELIMINAR.** Son conteos devueltos por la API pública de datos.gov.co. **No sustituyen** la auditoría sobre un archivo congelado con SHA-256 (issues E1-3 y E1-8) y no deben citarse en el informe como cifra final.

- Recurso: <https://www.datos.gov.co/d/dbdv-iihs> (endpoint `https://www.datos.gov.co/resource/dbdv-iihs.json`)
- Fecha de consulta: 2026-11-11
- `fecha_corte_datos` informada por el dataset: 31/10/2026
- Esquema confirmado (29 columnas): `proceso_anonimizado`, `proceso_conexado`, `proceso_con_conexidad`, `es_ruptura`, `estado`, `etapa`, `ley`, `tipo_noticia`, `procedimiento_abreviado`, `pais_hecho`, `departamento_hecho`, `municipio_hecho`, `cod_dane_hecho`, `dir_hecho_rural_urbana`, `seccional`, `a_o_hecho`, `mes_hecho`, `trimestre_hecho`, `a_o_creacion_proceso`, `mes_creacion_proceso`, `trimestre_creacion`, `tipo_delito`, `deli_id`, `delito`, `titulo_delito`, `capitulo_delito`, `grado_delito`, `delito_querellable` y `fecha_corte_datos` (todas de tipo texto).

## Consulta

```text
$where = cod_dane_hecho='11001'
         AND capitulo_delito='Del Hurto'
         AND a_o_hecho in ('2018','2019','2020','2021','2022','2023','2024','2025')
$select = a_o_hecho, count(*) AS filas, count(distinct proceso_anonimizado) AS procesos
$group  = a_o_hecho
```

## Resultado

| Año del hecho | Filas | Procesos únicos (en el año) |
|---|---:|---:|
| 2018 | 144.111 | 143.542 |
| 2019 | 165.121 | 164.614 |
| 2020 | 112.771 | 112.363 |
| 2021 | 141.828 | 141.477 |
| 2022 | 173.856 | 173.505 |
| 2023 | 204.930 | 204.487 |
| 2024 | 172.114 | 171.688 |
| 2025 | 185.972 | 185.366 |
| **Total 2018–2025** | **1.300.703** | **1.297.042** (consulta global `count(distinct)`) |

Conteos complementarios de la API (`$select=count(*)`, 2026-11-11):

| Filtro | Filas |
|---|---:|
| `cod_dane_hecho='11001'` (Bogotá, todos los delitos y años) | 5.701.020 |
| `cod_dane_hecho='11001' AND capitulo_delito='Del Hurto'` (todos los años) | 2.002.177 |

El conteo del dataset nacional completo no pudo obtenerse porque la consulta supera el tiempo límite de la API.

Una consulta adicional con `$group=delito` sobre el mismo filtro devolvió 114 valores distintos de `delito`. Los principales son:

| `delito` | Filas |
|---|---:|
| Hurto. Art. 239 C.P. | 938.566 |
| Hurto Art. 239 C.P. Menor Cuantia | 107.498 |
| Hurto. Art. 239 C.P. Agravado Cuando Lo Hurtado Son Medios Motorizados… Art. 241 C.P. N.6 | 50.017 |
| Hurto Menor Cuantia. Art. 239 C.P. Agravado Por Establecimiento Publico Art. 241 C.P. N.11 | 27.368 |
| Hurto Calificado Art. 240 C.P. Menor Cuantia | 24.952 |

## Implicaciones metodológicas (a discutir en E1-9 y E1-10)

1. Si el archivo congelado lo confirma, esta fuente **por sí sola** supera los 500.000 registros, tanto en filas como en procesos únicos.
2. La unidad es la **fila proceso–delito (noticia criminal)**, no la víctima ni el hecho policial.
3. El capítulo «Del Hurto» agrupa **todas las modalidades**: hurto común, calificado, agravado, de automotores y abigeato (26 filas con `Abigeato`). Fiscalía **no identifica explícitamente el hurto a personas**, por lo que la población es «hurto (todas las modalidades)». Hay que decidir si se excluyen automotores y abigeato y documentar el criterio.
4. La granularidad temporal es año y mes del hecho. No hay fecha diaria ni localidad (solo municipio).
