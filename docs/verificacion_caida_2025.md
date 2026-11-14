# La caída de noviembre y diciembre de 2025 es un artefacto (#86)

Fecha de verificación: 2026-11-13. Reproducible con `python scripts/verificar_caida_2025.py`.
Salidas en `outputs/verificacion_caida_2025/`.

## Conclusión

**Los dos últimos meses del registro de la Policía están incompletos. La caída no es del fenómeno.**

El registro muestra en noviembre y diciembre de 2025 algo más de la mitad de las víctimas de los
meses anteriores. **Línea 123, que es una fuente independiente, no cae.** Si el hurto hubiera bajado
a la mitad en Bogotá, las llamadas al 123 lo habrían reflejado.

**La serie objetivo se corta en 2025-10-31.** Noviembre y diciembre de 2025 no se usan para entrenar
ni para evaluar, y la serie pasa de 2.192 a **2.131 días**.

## Por qué Línea 123 y no el agregado de MinDefensa

El agregado diario **no sirve** como contraste: ya está demostrado que es la agregación del mismo
registro, así que repite el mismo sesgo. Y así ocurre: sus cifras de 2025 son idénticas a las del
registro **mes a mes, incluidos los dos meses caídos**.

Línea 123 sí es independiente: son llamadas al 123 tramitadas por el C4, con otro circuito de
captura y otra entidad.

## La evidencia

| Mes | Registro Policía | Agregado MinDefensa | Línea 123 (incidentes) |
|---|---:|---:|---:|
| 2025/01 | 9.790 | 9.790 | 10.494 |
| 2025/02 | 11.287 | 11.287 | 11.313 |
| 2025/03 | 11.653 | 11.653 | 12.142 |
| 2025/04 | 11.677 | 11.677 | 11.837 |
| 2025/05 | 9.789 | 9.789 | 12.194 |
| 2025/06 | 10.777 | 10.777 | 12.112 |
| 2025/07 | 11.869 | 11.869 | 12.702 |
| 2025/08 | 11.274 | 11.274 | 13.219 |
| 2025/09 | 11.557 | 11.557 | 13.106 |
| 2025/10 | 12.228 | 12.228 | 12.750 |
| **2025/11** | **5.416** | **5.416** | **12.314** |
| **2025/12** | **5.700** | **5.700** | **11.529** |

Frente a la media de los diez primeros meses:

| Mes | Registro | Línea 123 |
|---|---:|---:|
| 2025/11 | **−51,6 %** | +1,0 % |
| 2025/12 | **−49,1 %** | −5,4 % |

Línea 123 se mantiene plano. El registro se parte por la mitad. Las dos fuentes solo pueden
discrepar así si el problema está en una de ellas, y la que cambia de comportamiento es el registro.

## No es un corte seco, es carga parcial

Noviembre tiene datos **los 30 días** y diciembre **los 31**. No hay un día a partir del cual el
archivo se vacía: todos los días están, pero a la mitad del nivel.

| Fecha | Víctimas |
|---|---:|
| 2025/10/28 | 331 |
| 2025/10/29 | 272 |
| 2025/10/30 | 290 |
| 2025/10/31 | 314 |
| 2025/11/01 | 287 |
| 2025/11/02 | 159 |
| 2025/11/03 | 133 |
| 2025/11/04 | 217 |

El nivel pasa de 270–330 diarios a 130–240 a partir del 2 de noviembre. Eso descarta un truncado
del archivo y apunta a que los registros de esos meses **se siguen consolidando**: llegan con
retraso al momento del corte de publicación.

## Afecta a todo el archivo, no solo a Bogotá

Contando **todos los delitos del país**, el mismo archivo cae:

| Mes | Registros nacionales |
|---|---:|
| 2025/10 | 72.896 |
| 2025/11 | 60.288 |
| 2025/12 | 48.125 |

La caída nacional es del 17 % en noviembre y del 34 % en diciembre, menor que el 50 % del hurto en
Bogotá, pero en la misma dirección. Es un patrón de consolidación incompleta de todo el archivo, no
un problema de la ciudad ni del delito.

## Consecuencias

1. **La serie objetivo termina el 2025-10-31**, con 2.131 días en lugar de 2.192. Hay que
   actualizarlo en D-01 y en `outputs/serie_objetivo/`.
2. **Ningún modelo se entrena ni se evalúa con noviembre o diciembre de 2025.** Son justo los meses
   que caerían en el conjunto de evaluación de una validación temporal, así que incluirlos haría
   que cualquier modelo pareciera bueno prediciendo una caída que no existió.
3. **El informe no puede describir una caída del hurto a finales de 2025.** Si el texto la menciona
   como hecho, hay que corregirlo. La cifra anual de 2025 (123.017) está incompleta por la misma
   razón y debe citarse como tal.
4. Al redescargar el archivo de 2025 más adelante, conviene **repetir esta comprobación**: si los
   meses se completaron, el corte puede moverse.

## Límite de esta verificación

Queda sin comprobar con Fiscalía, que sería un tercer contraste independiente, porque su CSV no
está en esta copia local. No cambia la conclusión: basta con que una fuente independiente no caiga
para descartar que el fenómeno lo hiciera.
