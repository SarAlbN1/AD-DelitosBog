# Cruce entre el registro de Policía y el agregado de MinDefensa (#15, #17)

Fecha de ejecución: 2026-11-11. Fuente de las cifras: `outputs/auditoria_policia/`, producido por
`scripts/auditoria_datasets.py` sobre los seis archivos descargados, y conteos directos sobre los
CSV convertidos.

Este documento convierte en evidencia la proyección de `docs/evidencia_policia_registro.md`.

## 1. Archivos auditados

Descargados de <https://www.policia.gov.co/estadistica-delictiva> el 2026-11-11.

| Año | Archivo | Bytes | SHA-256 | Filas nacionales |
|---|---|---:|---|---:|
| 2020 | `delitos_registro_2020.xlsx` | 33.190.915 | `f6a91917394d173f16383c67ae3306c4edd94a6fa7ec61830a0b92b10d2cf982` | 651.206 |
| 2021 | `delitos_registro_2021.xlsx` | 39.945.525 | `e04e27c1f11c1215c6a9291813da4aa7a48c91d88399dc9783bd30014a58ec60` | 792.244 |
| 2022 | `delitos_registro_2022.zip` | 40.742.004 | `654e55a1e9233644cc0f209f690293a0268fb5e2acd195f3a772700f09d070be` | 862.451 |
| 2023 | `delitos_registro_2023.zip` | 39.323.967 | `67e910092e773447106c41cfdd54b02bb9800c073a97b135befa866b927585dc` | 917.544 |
| 2024 | `delitos_registro_2024.xlsx` | 40.514.443 | `e472b63bc021d08b442affcde589262e8377d196e9764a41bfa0f99b0cc179ba` | 832.475 |
| 2025 | `delitos_registro_2025.xlsx` | 37.561.586 | `be262d7bff7ae7236dad729379e584d8febbbae1c4127ff4d0382bddbcb71252` | 773.950 |

El SHA-256 de 2024 coincide con el publicado en `docs/evidencia_policia_registro.md`, así que la
inspección previa de ese archivo es reproducible.

Se descartaron 25.207 filas de pie de archivo en total (notas, «Fecha de entrega» y filas en
blanco), registradas por archivo en `data/raw/policia_registro/csv/conversion.json`.

## 2. El esquema cambia entre años

| Año | Fila del encabezado | Columna de arma | ¿Trae `ICCS`? |
|---|---:|---|---|
| 2020 | 12 | `ARMAS MEDIOS` | sí |
| 2021 | **13** | **`ARMA MEDIO`** | sí |
| 2022 | **13** | `ARMAS MEDIOS` | sí |
| 2023 | 12 | `ARMAS MEDIOS` | **no** |
| 2024 | 12 | `ARMAS MEDIOS` | sí |
| 2025 | 12 | `ARMAS MEDIOS` | sí |

Consecuencias para el manifiesto: el nombre del arma se unifica con `renombrar`, el encabezado se
detecta en vez de fijarse, y el filtro de hurto usa `DELITOS` y no `ICCS`, porque `DELITOS` existe
en los seis años con la etiqueta idéntica `(05022) Hurto a personas`.

## 3. Embudo del registro

| Etapa | Filas |
|---|---:|
| Original, los seis archivos | 4.829.870 |
| Bogotá (`CODIGO DANE` = 11001) | 1.406.157 |
| 2018–2025 | 1.406.157 |
| Hurto a personas `(05022)` | **741.986** |

Las 741.986 filas **superan el mínimo de 500.000** en una única unidad de observación: una fila por
víctima, con `CANTIDAD = 1`. El periodo real que cubren es 2020–2025.

## 4. Concordancia con el agregado diario

| Año | Suma del agregado | Filas del registro | Diferencia |
|---|---:|---:|---:|
| 2020 | 83.136 | 83.136 | 0 |
| 2021 | 109.428 | 109.428 | 0 |
| 2022 | 137.157 | 137.157 | 0 |
| 2023 | 158.745 | 158.745 | 0 |
| 2024 | 130.504 | 130.503 | **−1** |
| 2025 | 123.017 | 123.017 | 0 |
| **2020–2025** | **741.987** | **741.986** | **−1** |

**Cinco de los seis años coinciden exactamente.** La diferencia total es de una fila.

### De dónde sale esa fila

Comparando día a día dentro de 2024, el descuadre no está en un solo día: son siete días de marzo
de 2024 que se compensan entre sí.

| Día | Agregado | Registro | Diferencia |
|---|---:|---:|---:|
| 2024/03/01 | 463 | 462 | −1 |
| 2024/03/02 | 421 | 422 | +1 |
| 2024/03/04 | 330 | 329 | −1 |
| 2024/03/07 | 357 | 358 | +1 |
| 2024/03/08 | 476 | 475 | −1 |
| 2024/03/25 | 176 | 177 | +1 |
| 2024/03/26 | 234 | 233 | −1 |

Cuatro días con una unidad menos en el registro y tres con una más: neto −1. El patrón es
compatible con que unos pocos registros cambiaran de fecha entre el corte que alimenta la API y el
que se publicó en el archivo anual. No es un error sistemático: afecta a 7 de los 366 días de 2024
y a 0,0008 % de las filas del año.

**Enunciado defendible para el informe:** el agregado diario de MinDefensa es la agregación por día
del registro de la Policía Nacional. La correspondencia es exacta en 2020, 2021, 2022, 2023 y 2025,
y en 2024 difiere en una unidad por siete días de marzo que se compensan.

## 5. Calidad del registro

Valores nulos sobre las 4.829.870 filas nacionales:

| Columna | Nulos | % |
|---|---:|---:|
| `GENERO` | 255.192 | 5,28 % |
| `*AGRUPA EDAD PERSONA*` | 17.470 | 0,36 % |
| `MUNICIPIO` | 26 | 0,0005 % |
| El resto | 0 | 0 % |

Coincide con la advertencia que el propio archivo trae en su pie: género y edad no tienen calidad
validada en completitud. No deben usarse como variables del modelo sin tratar esa limitación.

### Los duplicados exactos no se pueden eliminar

| Etapa | Filas | Filas distintas | Repetidas | Máximo de repeticiones |
|---|---:|---:|---:|---:|
| Original | 4.829.870 | 2.315.623 | 2.514.247 | 302 |
| Hurto en Bogotá | 741.986 | **28.642** | 713.344 | 302 |

Esto **no es un defecto de los datos**. Una fila describe arma o medio, departamento, municipio,
fecha, género, grupo de edad, código DANE, delito, mes y `CANTIDAD = 1`. Dos víctimas con el mismo
perfil el mismo día en la misma ciudad producen filas idénticas, y son dos víctimas distintas.

**Advertencia para el preprocesamiento (#30, #32):** aplicar una deduplicación por fila exacta sobre
esta fuente reduce 741.986 filas a 28.642 y destruye el conteo, además de hacer caer el requisito de
500.000. El archivo no trae identificador de víctima ni de hecho, así que no hay forma de distinguir
un duplicado real de dos víctimas indistinguibles. La deduplicación exacta queda prohibida aquí, y
el control de consistencia es el agregado diario, no la unicidad de filas.

## 6. Lo que sigue abierto

- **2018 y 2019 no existen a nivel de registro.** El periodo del registro es 2020–2025. Mezclarlo
  con el agregado para cubrir 2018–2019 rompe la unidad de observación única que exige el mínimo, y
  esos dos años solo podrían entrar en análisis agregados, fuera del conteo de filas. Decisión en
  #18.
- El informe, el `README.md` y los notebooks dicen 2018–2025 en todas partes. Si el periodo
  principal queda en 2020–2025, hay que actualizarlos (#27 y la segunda entrega).
- La auditoría conjunta de las cuatro fuentes en un solo reporte necesita el CSV de Fiscalía en
  local, que hoy no está en esta copia del repositorio. Las cifras de Fiscalía y Línea 123 siguen
  siendo las de `outputs/auditoria/`.
