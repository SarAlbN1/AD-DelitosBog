# Fuentes de datos

El proyecto usa **tres** fuentes de delito: Línea 123, Policía y Fiscalía. Cada una tiene su propia unidad de observación y **no se suman entre sí**.

Policía aparece en dos recursos distintos que no hay que confundir: el **registro** anual de policia.gov.co, que es microdato y la fuente principal (D-01), y el **agregado diario** de MinDefensa en datos.gov.co, que se conserva como control de consistencia y como única vía para cubrir 2018–2019.

| Fuente | Cobertura utilizada | Descarga | Filas | Unidad de observación |
|---|---|---|---|---|
| [Línea 123 · Incidentes tramitados C4 Bogotá NUSE](https://datosabiertos.bogota.gov.co/dataset/incidentes) | Archivo histórico 2015–2026. Análisis de 2018–2025 | 2026-11-09 | 1.117.394 en total; 763.074 en 2018–2025; **25.144** con `HURTO` en `TIPO_DETALLE` dentro de 2018–2025 (36.142 si se cuentan todos los años del archivo) | Agregado año × mes × localidad × UPZ × tipo de incidente. `CANT_INCIDENTES` suma las llamadas tramitadas, no los hechos. |
| [Policía Nacional · Hurto a personas, a nivel de registro](https://www.policia.gov.co/estadistica-delictiva) — **fuente principal (D-01)** | Bogotá, `CODIGO DANE` 11001, delito `(05022) Hurto a personas`. Publicados 2020–2025; **2018 y 2019 no existen a este nivel** | 2026-11-11 | **741.986** de hurto a personas en Bogotá, 2020–2025, ya auditadas | Una fila por víctima o registro, con `CANTIDAD = 1`. Trae arma o medio, género y edad. |
| [MinDefensa `4rxi-8m8d` · Hurto a personas](https://www.datos.gov.co/d/4rxi-8m8d) — **control de consistencia** | Bogotá, `cod_muni` 11001, 2018-01-01 a 2025-12-31 | 2026-11-09 | **2.922** | Agregado fecha × municipio. `cantidad` es el número de hurtos registrados ese día, no una fila por hecho ni por víctima. Es la agregación diaria del recurso anterior: la correspondencia es exacta en 2020, 2021, 2022, 2023 y 2025, y en 2024 difiere en una unidad. |
| [Fiscalía · Procesos Fiscalía V3](https://www.datos.gov.co/d/dbdv-iihs) | Bogotá, `cod_dane_hecho` 11001, capítulo `Del Hurto` | 2026-11-11 | 2.002.177 descargadas | Fila proceso–delito (noticia criminal). Un proceso puede repetirse en varias filas. |

Capas de apoyo, que no son fuentes de delito:

- **Geometrías de las localidades.** Se toman del [FeatureServer de la Secretaría Distrital de Seguridad](https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/FeatureServer/0) y se usan solo para los mapas.
- **Población por localidad.** Se usa como denominador de las tasas de llamadas de la Línea 123 por 100.000 habitantes. Sin ella, el orden de las localidades refleja su tamaño y no su riesgo.

| Capa | Recurso | Descarga | Filas | Unidad de observación |
|---|---|---|---|---|
| [SDP · Proyecciones y retroproyecciones de población (2005–2035)](https://datosabiertos.bogota.gov.co/dataset/proyecciones-y-retroproyecciones-de-poblacion-2005-2035) | Recurso por localidad, versión de marzo de 2025 (`202503_localidad_proyeccion_retroproyeccion_poblacion_2005_2035.ods`), publicado en el portal el 2025-05-14. Licencia CC BY 4.0 | 2026-11-16 | 837: 20 localidades × 31 años (2005–2035), separadas en cabecera municipal y centro poblado y rural disperso | Localidad × año × área, con la población por sexo y edad simple (0 a «100 y más») y una columna `Total`. Es población **residente proyectada**, no población flotante |

SHA-256 del `.ods` usado: `f02e6d9b2d571a7bdc77fd3c2f5e3a0160b0c3a9a5c36925e14ad3579f851225`.

[`scripts/poblacion_localidad.py`](../scripts/poblacion_localidad.py) suma las dos áreas y deja una fila por localidad y año en `outputs/poblacion/poblacion_localidad_2020_2025.csv`:
- comprueba en cada fila que `Total` sea la suma de hombres y mujeres y la de las 101 edades;
- la columna `clave` cruza con la Línea 123 (mayúsculas, sin tildes, y «CANDELARIA» sin artículo). Las 20 localidades cruzan; «SIN LOCALIZACION» no tiene población y queda fuera de las tasas.

Bogotá suma 7.732.161 habitantes en 2020 y 7.937.898 en 2025 (`outputs/poblacion/resumen_poblacion.json`).

`data/raw/`, `data/processed/` y `DataSet/` están excluidos de Git. Los notebooks buscan cada archivo primero en `DataSet/` y después en `data/raw/`.

## Cómo leer estas cifras

- **Filas y conteos no son lo mismo.** Línea 123 y el agregado de MinDefensa vienen agregados: una fila es un conteo. El registro de Policía no: cada fila vale 1. La suma de `cantidad` en MinDefensa da 975.793 hurtos en 2018–2025, de los cuales 123.017 son de 2025, pero el archivo tiene 2.922 filas. Usar esa suma como número de registros sobreestima el tamaño del dataset.
- **El mínimo de 500.000 registros se mide en filas**, dentro de una sola unidad de observación. Con los archivos auditados hasta hoy, ni Línea 123 (25.144 filas de hurto en 2018–2025) ni el agregado de MinDefensa (2.922 filas) lo alcanzan. Lo superan Fiscalía (1.300.703 filas) y el registro de Policía (741.986 filas), las dos auditadas. Por D-01 ([docs/decisiones.md](../docs/decisiones.md)), **el requisito se sostiene con el registro de Policía**: es hurto a personas, una víctima por fila. Fiscalía es complementaria y se cita siempre como «hurto en todas sus modalidades», nunca como hurto a personas.
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

**Fiscalía.** Se extrae por API con el filtro `cod_dane_hecho='11001' AND capitulo_delito='Del Hurto'`, paginando por `$order=:id`. La descarga se reproduce con [`scripts/descargar_fiscalia.py`](../scripts/descargar_fiscalia.py).

**Población por localidad.** Se descarga el `.ods` oficial y se agrega por localidad y año:

```sh
mkdir -p data/raw/poblacion
curl -fLSs -o data/raw/poblacion/202503_localidad_proyeccion_retroproyeccion_poblacion_2005_2035.ods \
  'https://datosabiertos.bogota.gov.co/dataset/0f1fb76a-1595-43d5-9257-0abcc3db908a/resource/5669484f-dc1d-4457-b1d1-de0a3825b41c/download/202503_localidad_proyeccion_retroproyeccion_poblacion_2005_2035.ods'
python scripts/poblacion_localidad.py
```

La SDP actualiza estas proyecciones. Si el portal publica una versión nueva, cambian el nombre del archivo, la huella y las cifras: anote la versión usada.

El CSV de Policía es obligatorio. La consulta de filas nacionales es informativa. Línea 123, Fiscalía y la capa de localidades se procesan si sus archivos están disponibles.

## Pendientes

- `$limit=50000` basta hoy para Policía porque el recurso devuelve 2.922 filas, pero no es un límite seguro si cambia la granularidad. Convendría paginar.
- El esquema del registro **cambia entre años**: el encabezado está en la fila 12 en 2020, 2023, 2024 y 2025 y en la 13 en 2021 y 2022; la columna del arma es `ARMAS MEDIOS` salvo en 2021, que usa `ARMA MEDIO`; y 2023 no trae la columna `ICCS`. El detalle y su tratamiento están en [docs/cruce_policia_registro_agregado.md](../docs/cruce_policia_registro_agregado.md).
- **No deduplique el registro por fila exacta.** 713.344 de las 741.986 filas son duplicados exactos, porque dos víctimas del mismo perfil el mismo día producen filas idénticas y el archivo no trae identificador. Un `drop_duplicates()` dejaría 28.642 filas y tumbaría el requisito de 500.000.
- Por D-01 el periodo principal es 2020–2025. El informe ya está actualizado. Los notebooks de la segunda entrega aún usan el agregado 2018–2025 y se adaptan en #87.
- Noviembre y diciembre de 2025 caen a menos de la mitad en el registro, en el agregado y en los cuadros validados de la Policía. La causa está pendiente en #86.
