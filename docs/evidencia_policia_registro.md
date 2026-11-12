# Evidencia: archivos de Policía Nacional a nivel de registro (#10, #15, #17)

Fecha de verificación: 2026-11-11. Este documento sustenta la decisión sobre qué recurso usar como fuente «Policía». No declara cumplido el requisito de 500.000 registros, que sigue en el issue #17.

## 1. Hay dos recursos distintos

| | A. Policía Nacional — registro | B. MinDefensa — HURTO PERSONAS |
|---|---|---|
| Ubicación | https://www.policia.gov.co/estadistica-delictiva | https://www.datos.gov.co/resource/4rxi-8m8d |
| Formato | Un archivo `.xlsx` por año con **todos** los delitos (2022 y 2023 vienen en `.zip`) | Un único CSV continuo |
| Unidad | Una fila por registro, con `CANTIDAD = 1` | Una fila por día y municipio, con `cantidad` = conteo |
| Variables | `ARMAS MEDIOS`, `DEPARTAMENTO`, `MUNICIPIO`, `FECHA HECHO`, `GENERO`, `*AGRUPA EDAD PERSONA*`, `CODIGO DANE`, `DELITOS`, `MES`, `CANTIDAD`, `ICCS` | `fecha_hecho`, `cod_depto`, `departamento`, `cod_muni`, `municipio`, `cantidad` |
| Años publicados | 2020–2026. **2018 y 2019 no aparecen** en la página actual | 2018–2025 y siguientes |

El recurso autorizado en el planteamiento es A: los «archivos anuales de policia.gov.co». El archivo que tiene Sara es B.

## 2. Inspección del archivo 2024 (recurso A)

- **Archivo:** `INFORMACIÓN_DE_DELITOS_A_NIVEL_DE_REGISTRO_AÑO_2024_3.xlsx`.
  - Tamaño: 40.514.443 bytes.
  - SHA-256: `e472b63bc021d08b442affcde589262e8377d196e9764a41bfa0f99b0cc179ba`.
  - Copia local, ignorada por git: `data/raw/policia_registro/delitos_registro_2024.xlsx`.
- **Estructura:** una sola hoja (`Hoja1`) con 11 filas de membrete y el encabezado en la fila 12.
  - Al final hay filas vacías y notas («Fecha de entrega: 20 de agosto de 2026»).
  - Una de esas notas advierte que **género y edad no tienen calidad validada en completitud**.
  - Por eso, en la lectura hay que saltar 11 filas y descartar las filas sin `DELITOS`.
- **Volumen nacional:** 832.475 filas de datos, todas con `CANTIDAD = 1`. Hay 18 categorías de delito con prefijo ICCS, por ejemplo `(05022) Hurto a personas`.
- **Hurto a personas en Bogotá** (`CODIGO DANE = 11001` y `DELITOS = (05022) Hurto a personas`):
  - **130.503 filas**, que suman 130.503 en `CANTIDAD`.
  - Fechas del 2024/01/01 al 2024/12/31, con los 12 meses presentes.
  - Arma o medio: sin empleo de armas 88.328, arma blanca 23.508, arma de fuego 10.879, contundentes 3.809, no reportado 3.024, escopolamina 950.
  - Género: masculino 75.487, femenino 54.898, nulo 118.
  - Edad: «18 y más» 128.819.
- **Unidad de observación:** cada fila trae género y edad de una persona, así que la fila representa a **una víctima** de un hecho. Esto se confirmará con la ficha metodológica en #15.

## 3. Concordancia con el agregado de MinDefensa (recurso B)

Consulta: `$where cod_muni='11001'`, agrupada por año, con `sum(cantidad)`.

| Año | Suma `cantidad` (B) | Filas (B) | Filas registro (A) |
|---|---:|---:|---:|
| 2018 | 105.964 | 365 | no publicado en A |
| 2019 | 127.842 | 365 | no publicado en A |
| 2020 | 83.136 | 366 | pendiente |
| 2021 | 109.428 | 365 | pendiente |
| 2022 | 137.157 | 365 | pendiente |
| 2023 | 158.745 | 365 | pendiente |
| 2024 | 130.504 | 366 | **130.503** |
| 2025 | 123.017 | 365 | pendiente |
| **Total** | **975.793** | **2.922** | |

En 2024, A y B difieren en una sola unidad.

**Rastreo de la diferencia, día a día:** se compararon los 366 días de 2024.
- 359 días coinciden exactamente.
- 7 días de marzo difieren en ±1:

| Día | A | B |
|---|---:|---:|
| 01/03 | 462 | 463 |
| 02/03 | 422 | 421 |
| 04/03 | 329 | 330 |
| 07/03 | 358 | 357 |
| 08/03 | 475 | 476 |
| 25/03 | 177 | 176 |
| 26/03 | 233 | 234 |

La diferencia neta es +1 en B.

Descartes:
- No hay filas de hurto a personas en A con fecha nula.
- No hay filas con municipio Bogotá y código DANE distinto de 11001.

La explicación más probable es que A y B son **cortes distintos** de la misma base. A tiene «Fecha de entrega: 20 de agosto de 2026»; B se actualiza en otra fecha. Entre un corte y otro, unos pocos registros cambiaron de fecha de hecho y uno se añadió o se retiró.

Formulación sugerida para el informe: «B es la agregación diaria de A; en 2024 coinciden en 359 de 366 días y en el total anual difieren en un registro (0,0008 %), atribuible a la diferencia de fecha de corte».

Así se evita afirmar una igualdad exacta.

## 4. Implicaciones (por verificar, no son resultados)

- Si el resto de años se comporta como 2024, A aportaría alrededor de **742.000 filas de hurto a personas en Bogotá para 2020–2025** (la suma de B en esos años). Esa cifra superaría el mínimo con la población exacta del proyecto.
  - Es una **proyección**. Solo cuenta como evidencia cuando la auditoría (`scripts/auditoria_datasets.py`) se ejecute sobre los archivos descargados.
- B, en cambio, aporta 2.922 filas. Sirve como control de consistencia y como serie diaria, no para el requisito de volumen.
- **2018–2019:** A no los publica actualmente. Las opciones son:
  1. Buscar versiones anteriores de los archivos.
  2. Usar B para esos dos años, solo en análisis agregados.
  3. Restringir el periodo de A a 2020–2025.

  Esta decisión va en #18.
- **Script de auditoría (PR #63):**
  - Ya lee `.xlsx`, y con `"lectura": {"fila_encabezado": 11}` salta el membrete.
  - Desde el commit `e669553` descarta las notas del final y las registra en `anomalias.csv` como `pie_de_archivo_descartado`.
  - El `.zip` sigue admitiendo solo un CSV dentro, así que los años 2022 y 2023 se descomprimen antes de auditar.

## 5. Entrada de manifiesto verificada (#15)

Se probó con el archivo 2024. La auditoría dio:
- 832.475 filas originales;
- 11 filas de pie descartadas;
- 247.778 filas de Bogotá;
- **130.503 filas de hurto a personas**, que suman 130.503 en `CANTIDAD`.

La entrada sale de la propuesta de Sara, con tres correcciones contra el archivo real:
- la columna se llama **`DELITOS`**, no `DELITO`;
- la fecha viene como `AAAA/MM/DD`, así que se usa `formato_fecha` en lugar de `dayfirst`;
- la URL de la página de descarga es la de estadística delictiva.

```json
{
  "id": "policia_registro",
  "nombre": "Policía Nacional — Información de delitos a nivel de registro (filtrado: hurto a personas)",
  "url": "https://www.policia.gov.co/estadistica-delictiva",
  "fecha_extraccion": "AAAA-MM-DD",
  "unidad_observacion": "Una fila por víctima o registro (CANTIDAD = 1)",
  "archivos": ["data/raw/policia_registro/*.xlsx"],
  "lectura": {"hoja": 0, "fila_encabezado": 11},
  "columnas": {"fecha": "FECHA HECHO", "formato_fecha": "%Y/%m/%d", "cantidad": "CANTIDAD",
               "delito": "DELITOS", "localidad": "MUNICIPIO"},
  "filtros": {
    "bogota": {"columna": "CODIGO DANE", "patron": "^11001"},
    "hurto": {"columna": "DELITOS", "patron": "05022|HURTO A PERSONAS"}
  }
}
```

Los encabezados de 2020–2023 y 2025 todavía no se han comprobado. Si cambian, el script se detiene y lista las columnas disponibles; en ese caso se usa `renombrar`.
