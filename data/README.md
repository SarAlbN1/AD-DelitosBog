# Fuentes de datos

El proyecto usa **tres** fuentes de delito: Línea 123, Policía y Fiscalía. Cada una tiene su propia unidad de observación y **no se suman entre sí**.

Policía aparece en dos recursos distintos que no hay que confundir: el **registro** anual de policia.gov.co, que es microdato y la fuente principal propuesta, y el **agregado diario** de MinDefensa en datos.gov.co, que se conserva como control de consistencia y como única vía para cubrir 2018–2019.

| Fuente | Cobertura utilizada | Descarga | Filas | Unidad de observación |
|---|---|---|---|---|
| [Línea 123 · Incidentes tramitados C4 Bogotá NUSE](https://datosabiertos.bogota.gov.co/dataset/incidentes) | Archivo histórico 2015–2026. Análisis de 2018–2025 | 2026-11-09 | 1.117.394 en total; 763.074 en 2018–2025; **25.144** con `HURTO` en `TIPO_DETALLE` dentro de 2018–2025 (36.142 si se cuentan todos los años del archivo) | Agregado año × mes × localidad × UPZ × tipo de incidente. `CANT_INCIDENTES` suma las llamadas tramitadas, no los hechos. |
| [Policía Nacional · Hurto a personas, a nivel de registro](https://www.policia.gov.co/delitos-de-impacto/hurto-personas) — **fuente principal propuesta** | Bogotá, `CODIGO DANE` 11001, delito `(05022) Hurto a personas`. Publicados 2020–2025; **2018 y 2019 no existen a este nivel** | pendiente (#10) | 130.503 en 2024; unas 742.000 proyectadas para 2020–2025, **sin auditar** | Una fila por víctima o registro, con `CANTIDAD = 1`. Trae arma o medio, género y edad. |
| [MinDefensa `4rxi-8m8d` · Hurto a personas](https://www.datos.gov.co/d/4rxi-8m8d) — **control de consistencia** | Bogotá, `cod_muni` 11001, 2018-01-01 a 2025-12-31 | 2026-11-09 | **2.922** | Agregado fecha × municipio. `cantidad` es el número de hurtos registrados ese día, no una fila por hecho ni por víctima. Es la agregación diaria del recurso anterior: en 2024 suma 130.504 frente a sus 130.503 filas. |
| [Fiscalía · Procesos Fiscalía V3](https://www.datos.gov.co/d/dbdv-iihs) | Bogotá, `cod_dane_hecho` 11001, capítulo `Del Hurto` | 2026-11-11 | 2.002.177 descargadas | Fila proceso–delito (noticia criminal). Un proceso puede repetirse en varias filas. |

Capa de apoyo, no es una fuente de delito: las geometrías de las localidades se toman del [FeatureServer de la Secretaría Distrital de Seguridad](https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/FeatureServer/0) y se usan solo para los mapas.

`data/raw/`, `data/processed/` y `DataSet/` están excluidos de Git. Los notebooks buscan cada archivo primero en `DataSet/` y después en `data/raw/`.

## Cómo leer estas cifras

- **Filas y conteos no son lo mismo.** Línea 123 y Policía vienen agregadas: una fila es un conteo. La suma de `cantidad` en Policía da 975.793 hurtos en 2018–2025, de los cuales 123.017 son de 2025, pero el archivo tiene 2.922 filas. Usar esa suma como número de registros sobreestima el tamaño del dataset.
- **El mínimo de 500.000 registros se mide en filas**, dentro de una sola unidad de observación. Con los archivos auditados hasta hoy, ni Línea 123 (25.144 filas de hurto en 2018–2025) ni el agregado de MinDefensa (2.922 filas) lo alcanzan. Lo sostienen Fiscalía, ya auditada, y el registro de Policía, cuyas ~742.000 filas son todavía una proyección sin auditar. La población que se usará se decide en el #18.
- **El registro de Policía no cubre 2018–2019.** Si se elige como población principal, el periodo principal queda en 2020–2025, o esos dos años entran solo como agregado de MinDefensa y fuera del conteo de filas, porque mezclar microdato con agregado rompe la unidad de observación única que exige el mínimo.
- **Los recursos se actualizan.** Anote la fecha de descarga y conserve el archivo usado si necesita reproducir exactamente las cifras de una entrega.

## Descarga desde la raíz del repositorio

```sh
mkdir -p data/raw

# Policía / MinDefensa — hurto a personas, Bogotá 2018–2025
curl -fLSsG 'https://www.datos.gov.co/resource/4rxi-8m8d.csv' \
  --data-urlencode "\$where=cod_muni='11001' AND fecha_hecho >= '2018-01-01T00:00:00' AND fecha_hecho < '2026-01-01T00:00:00'" \
  --data-urlencode '$limit=50000' -o data/raw/hurto_bogota.csv

# Informativo: número de filas del recurso nacional completo
curl -fLSs 'https://www.datos.gov.co/resource/4rxi-8m8d.json?$select=count(*)' \
  -o data/raw/hurto_nacional_filas.json

# Capa de localidades para los mapas
curl -fLSsG 'https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/FeatureServer/0/query' \
  --data-urlencode 'where=1=1' --data-urlencode 'outFields=*' \
  --data-urlencode 'outSR=4326' --data-urlencode 'f=geojson' -o data/raw/localidades.geojson
```

**Línea 123.** Descargue el [CSV oficial](https://datosabiertos.bogota.gov.co/dataset/incidentes/resource/30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef) y guárdelo como `data/raw/linea123.csv`. El separador es `;`. El recurso se actualiza y puede cambiar su corte histórico. La columna `ID` **no es única**: 2.633 identificadores se repiten en el archivo completo y 166 dentro de las filas de hurto de 2018–2025, así que no sirve como clave primaria.

**Fiscalía.** Se extrae por API con el filtro `cod_dane_hecho='11001' AND capitulo_delito='Del Hurto'`, paginando por `$order=:id`. El script de descarga llega con el #12.

El CSV de Policía es obligatorio. La consulta de filas nacionales es informativa. Línea 123, Fiscalía y la capa de localidades se procesan si sus archivos están disponibles.

## Pendientes

- `$limit=50000` basta hoy para Policía porque el recurso devuelve 2.922 filas, pero no es un límite seguro si cambia la granularidad. Convendría paginar.
- Faltan por descargar los archivos de registro de Policía 2020–2025 a `data/raw/policia_registro/` (#10). Los de 2022 y 2023 vienen en `.zip` y hay que descomprimirlos antes de auditarlos, porque el script solo acepta un CSV dentro de un `.zip`.
- Al auditarlos hay que usar `"lectura": {"fila_encabezado": 11}` y descartar las notas del final del archivo, que de lo contrario cuentan como filas (#15).
- El informe y los notebooks dicen 2018–2025 en todas partes. Si el periodo principal cambia a 2020–2025, hay que actualizarlos (#27 y la segunda entrega).
