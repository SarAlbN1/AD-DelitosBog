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
5. Para Policía, si los encabezados cambian entre años, unifíquelos con `renombrar`. Si el Excel trae filas de título, indique `lectura.fila_encabezado` (base 0).

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
