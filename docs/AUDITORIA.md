# Auditoría reproducible de datasets

Script: [`scripts/auditoria_datasets.py`](../scripts/auditoria_datasets.py) · Pruebas: [`tests/test_auditoria_datasets.py`](../tests/test_auditoria_datasets.py) · Issues: E1-4, E1-5 y E1-9.

## Objetivo

Producir evidencia **calculada sobre los archivos originales efectivamente descargados** para la sección 4 del informe y para verificar el requisito de **500.000 registros**. El script nunca estima ni simula cifras. Si un archivo no existe, se detiene con un error.

## Instalación

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest -q tests          # 14 pruebas con datos sintéticos
```

## Preparar los datos

1. Descargue los archivos sin modificarlos en `data/raw/<fuente>/` (carpeta ignorada por Git).
2. Copie `config/fuentes_auditoria.example.json` como `config/fuentes_auditoria.json`.
3. Complete `fecha_extraccion` (AAAA-MM-DD) y la `url` exacta de cada recurso.
4. Abra el primer archivo de cada fuente y reemplace los nombres marcados `VERIFICAR`. Los nombres se comparan **normalizados**: minúsculas, sin tildes y con `_` en lugar de espacios (`FECHA HECHO` → `fecha_hecho`).
5. Para Policía, los encabezados **sí** cambian entre años: unifíquelos con `renombrar`. Si el Excel trae filas de título, indique `lectura.fila_encabezado`. Los detalles están más abajo.

### Policía Nacional a nivel de registro

Los archivos anuales de <https://www.policia.gov.co/estadistica-delictiva> traen todos los delitos
juntos, una fila por víctima con `CANTIDAD = 1`. Están publicados 2020–2025; **2018 y 2019 no
existen a este nivel**. Los de 2022 y 2023 se publican en `.zip`, y el lector solo admite un CSV
dentro de un `.zip`, así que hay que descomprimirlos antes.

No se auditan los `.xlsx` directamente: la rama de Excel de `iterar_bloques()` carga el archivo
completo en memoria antes de trocearlo, y son del orden de 800.000 filas por año. Se convierten
primero a CSV, en streaming y con memoria constante:

```bash
unzip -j data/raw/policia_registro/delitos_registro_2022.zip -d data/raw/policia_registro
python scripts/policia_registro_a_csv.py \
  --entrada data/raw/policia_registro --salida data/raw/policia_registro/csv
```

El conversor detecta la fila del encabezado, descarta el pie del archivo y escribe
`data/raw/policia_registro/csv/conversion.json` con el SHA-256 del `.xlsx` de origen y del CSV
producido, para poder demostrar de qué archivo descargado sale cada CSV auditado.

**El esquema cambia entre años** y conviene no darlo por fijo:

| Año | Fila del encabezado | Columna de arma | ¿Trae `ICCS`? |
|---|---:|---|---|
| 2020 | 12 | `ARMAS MEDIOS` | sí |
| 2021 | **13** | **`ARMA MEDIO`** | sí |
| 2022 | **13** | `ARMAS MEDIOS` | sí |
| 2023 | 12 | `ARMAS MEDIOS` | **no** |
| 2024 | 12 | `ARMAS MEDIOS` | sí |
| 2025 | 12 | `ARMAS MEDIOS` | sí |

Por eso el manifiesto unifica el nombre del arma con `renombrar` y filtra el hurto por `DELITOS`,
que existe en los seis años con la etiqueta `(05022) Hurto a personas`, y no por `ICCS`, que falta
en 2023.

Fiscalía (descarga del subconjunto de Bogotá con la API Socrata; documente la consulta y la fecha):

```bash
curl -G "https://www.datos.gov.co/resource/dbdv-iihs.csv" \
  --data-urlencode "\$where=cod_dane_hecho='11001'" \
  --data-urlencode '$limit=50000' --data-urlencode '$offset=0' \
  --data-urlencode '$order=:id' -o data/raw/fiscalia/fiscalia_bogota_p000.csv
# repetir incrementando $offset hasta que el archivo llegue vacío y comparar con $select=count(*)
```

## Ejecutar

```bash
# Todas las fuentes del manifiesto
python scripts/auditoria_datasets.py --config config/fuentes_auditoria.json

# Una sola fuente del manifiesto
python scripts/auditoria_datasets.py --config config/fuentes_auditoria.json --fuentes fiscalia

# Archivo suelto sin manifiesto
python scripts/auditoria_datasets.py --archivo "data/raw/policia/*.xlsx" --fuente-id policia \
  --fecha-extraccion 2026-11-11 --col-fecha fecha_hecho --dayfirst --col-cantidad cantidad \
  --filtro-bogota "municipio=BOGOTA"
```

Opciones útiles: `--chunksize 100000` (memoria), `--salida outputs/auditoria`, `--sin-figuras`, `--minimo 500000` y `-v`.

**`--fuentes` y la carpeta de salida.** Cada ejecución reescribe todas las salidas de `--salida`. Si esa carpeta ya tiene resultados de fuentes que no están en `--fuentes`, el script se detiene con el código `2` en lugar de borrarlos. Use otra `--salida`, incluya esas fuentes o, si quiere sustituirlos a propósito, añada `--forzar`.

Códigos de salida: `0` correcto · `2` error de configuración o de datos (el mensaje indica qué corregir) · `3` archivo inaccesible.

## Salidas (`outputs/auditoria/`)

| Archivo | Contenido |
|---|---|
| `resumen_fuentes.csv` | **Tabla del requisito**: filas originales, Bogotá, periodo y hurto; suma de cantidad; IDs únicos; unidad de observación |
| `resumen_archivos.csv` | Archivo, ruta, tamaño, **SHA-256**, codificación, separador, filas y columnas |
| `embudo_filtros.csv` | Filas y suma de cantidad antes y después de cada filtro acumulado |
| `diccionario_variables.csv` | Nombre normalizado y original, tipo inferido, valores únicos, presencia por archivo y ejemplo |
| `valores_nulos.csv` | Número y porcentaje de nulos por columna |
| `duplicados.csv` | Duplicados exactos y por identificador (población original y final) |
| `cobertura_temporal.csv` | Filas y suma de cantidad por año y mes (original y final) |
| `distribuciones_categoricas.csv` | Top 50 por variable categórica (original y final) |
| `estadisticas_numericas.csv` | n, suma, mínimo, máximo, media, desviación, cuantiles, negativos y ceros |
| `anomalias.csv` | Fechas o años inválidos, fuera de periodo, cantidades negativas, cero o no numéricas, IDs nulos, filas casi vacías |
| `auditoria.json` | Todo lo anterior más metadatos: fecha de ejecución, comando, SHA-256 del manifiesto y versiones |
| `reporte_auditoria.md` | Reporte legible, con la tabla de 500.000 registros |
| `figuras/*.png, *.pdf` | Embudo, serie mensual o anual, nulos y localidad (PDF vectorial para Overleaf) |

## Reglas metodológicas implementadas

- Los filtros son **acumulativos**: original → Bogotá → periodo → hurto. Un filtro sin configurar figura como «no aplica» y no excluye filas.
- **Filas ≠ suma de cantidad ≠ IDs únicos.** Se reportan por separado y nunca se suman entre fuentes.
- `filas_hurto_>=_500000` se evalúa **por fuente**. Que una fuente lo cumpla no decide por sí solo la validez metodológica (issue E1-10).
- Los textos se comparan en mayúsculas y sin tildes. Los patrones son expresiones regulares.
- Se consideran nulos el vacío y los tokens `NULL`, `NAN`, `NONE`, `N/A`, `NA`, `#N/A` y `NAT`. «Sin información» **no** cuenta como nulo: aparece en las distribuciones y, si es un año, como anomalía.
- Los duplicados exactos se detectan con un hash de 64 bits por fila (la probabilidad de colisión es despreciable para millones de filas).
- El procesamiento es por bloques y los resultados no dependen del tamaño de bloque (hay una prueba que lo comprueba). Los Excel se cargan completos.
- La auditoría es determinista. La semilla (42) se fija y se registra por consistencia con el resto del proyecto.
