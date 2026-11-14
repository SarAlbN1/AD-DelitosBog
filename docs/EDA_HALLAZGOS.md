# Análisis exploratorio: hallazgos (#34)

Reproducible con `python scripts/eda.py`. Cifras en `outputs/eda/`, figuras en
`outputs/eda/figuras/`. Serie objetivo: 2.131 días, 2020-01-01 a 2025-10-31, media 343,0
víctimas al día.

## 1. Evolución anual

| Año | Víctimas | Media diaria | Días | ¿Año completo? |
|---|---:|---:|---:|---|
| 2020 | 83.136 | **227,1** | 366 | sí |
| 2021 | 109.428 | 299,8 | 365 | sí |
| 2022 | 137.157 | 375,8 | 365 | sí |
| 2023 | 158.745 | **434,9** | 365 | sí |
| 2024 | 130.503 | 356,6 | 366 | sí |
| 2025 | 111.901 | 368,1 | **304** | **no** |

**2020 no es un año típico.** Con 227,1 víctimas diarias está un 48 % por debajo del máximo de
2023. Coincide con las restricciones de movilidad, así que no se puede leer como el punto de
partida de una tendencia.

**El total de 2025 no es comparable y su media diaria sí.** Son 304 días y no 365, porque la serie
se corta el 2025-10-31 (#86). Mirando el total parece una caída; mirando la media diaria, **2025
está por encima de 2024**: 368,1 frente a 356,6. Es un ejemplo de por qué el informe debe comparar
medias diarias y no totales mientras el último año esté truncado.

## 2. Perfil semanal

| Día | Víctimas por día (media) |
|---|---:|
| Lunes | 299,0 |
| Martes | 351,1 |
| Miércoles | 365,0 |
| Jueves | 364,8 |
| **Viernes** | **403,1** |
| Sábado | 372,5 |
| **Domingo** | **245,0** |

El viernes tiene un 64 % más de víctimas que el domingo. Es la señal más fuerte y limpia de la
serie, y justifica que el día de la semana sea una predictora y que cualquier comparador ingenuo
razonable use el rezago 7 en lugar del rezago 1.

## 3. Efecto de los festivos

En un festivo la media es **203,6** frente a 350,1 en un día no festivo. Pero esa comparación
engaña: la Ley Emiliani traslada los festivos al lunes, así que compararlos con «todos los días»
mezcla el efecto del festivo con el del día de la semana.

Comparando lunes con lunes, que es la comparación correcta:

| | Media | n |
|---|---:|---:|
| Lunes festivo | **201,5** | 62 |
| Lunes laborable | 323,9 | 243 |
| **Diferencia** | **−37,8 %** | |

El efecto se sostiene al controlar el día de la semana: **en un lunes festivo se registran un 38 %
menos de víctimas que en un lunes laborable.** El festivo debe ser una predictora del modelo, y el
calendario de festivos se conoce de antemano, así que no introduce fuga.

Hay 103 festivos en el periodo.

## 4. Estacionalidad mensual

| Mes | ene | feb | mar | abr | may | jun | jul | ago | sep | oct | nov | dic |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Media diaria | 325,9 | 355,0 | 336,8 | **312,7** | 315,2 | 316,6 | 327,5 | 345,8 | 374,2 | **386,9** | 382,1 | 344,9 |

El rango es estrecho: de 312,7 en abril a 386,9 en octubre, un 24 % entre el mínimo y el máximo,
frente al 64 % del perfil semanal. **La estacionalidad mensual existe pero es mucho más débil que
la semanal**, lo que sugiere que un modelo con rezagos semanales y calendario captará la mayor
parte de la estructura.

Nota: noviembre aparece alto (382,1) pese a que los noviembres de 2025 están excluidos. Es el
promedio de los noviembres de 2020 a 2024.

## 5. Distribución territorial

Solo Línea 123 tiene resolución dentro de la ciudad. Medido **sumando `CANT_INCIDENTES`**, no
contando filas.

| Localidad | Incidentes | % |
|---|---:|---:|
| Kennedy | 133.250 | 12,25 % |
| Suba | 125.987 | 11,58 % |
| Engativá | 121.838 | 11,20 % |
| Usaquén | 71.743 | 6,59 % |
| Bosa | 69.953 | 6,43 % |

Las tres primeras concentran el 35 % de los incidentes. Los incidentes **sin localidad asignada**
son 6.427, el **0,59 %** del total: un peso bajo, pero se separan igualmente porque «SIN
LOCALIZACION» no es una localidad.

### Lo que estos conteos no dicen

**No hay tasas por población, así que estos números no miden riesgo.** Kennedy, Suba y Engativá
son también de las localidades más pobladas de Bogotá, de modo que un conteo alto es lo esperable
antes de mirar nada más. Presentar este orden como un ranking de peligrosidad sería una lectura
estigmatizante y no se sostiene con los datos que hay.

Falta una fuente de población por localidad. El geojson de localidades que usamos trae conteos de
delitos y geometría, pero no población. `scripts/eda.py` acepta `--poblacion` con un CSV de
`localidad,habitantes` y calcula la tasa por 100.000 en cuanto exista esa fuente. **Hasta
entonces, el informe no debe comparar localidades entre sí.**

## 6. Relación entre las tres fuentes

En mes × Bogotá, la única resolución común. 70 meses, de 2020-01 a 2025-10. Las fuentes **no se
suman**: se comparan sus series.

Correlación de Pearson:

| | Policía | Línea 123 | Fiscalía |
|---|---:|---:|---:|
| **Policía** | 1,000 | 0,601 | **0,962** |
| **Línea 123** | 0,601 | 1,000 | 0,633 |
| **Fiscalía** | 0,962 | 0,633 | 1,000 |

**Este es el hallazgo más informativo del bloque.** Las dos fuentes de **registro**, Policía y
Fiscalía, se mueven casi idénticamente (0,962), mientras que **Línea 123 solo correlaciona
moderadamente con ambas** (0,60 y 0,63).

No es casualidad ni ruido. Policía y Fiscalía miden actividad administrativa sobre hechos
denunciados y comparten dinámicas institucionales; Línea 123 mide llamadas ciudadanas, que
dependen de la decisión de llamar y no de que el caso entre a un sistema. Dicho de otro modo:
**las dos fuentes que más se parecen entre sí son las que comparten el mismo sesgo.**

Esto respalda dos decisiones ya tomadas:

- Que Línea 123 sea la fuente de contraste en #86: es la única que no comparte el mecanismo de
  registro, y por eso su comportamiento en noviembre de 2025 dice algo que las otras dos no pueden
  decir.
- Que las fuentes se traten como complementarias y no intercambiables (D-01).

## 7. Qué se lleva el modelado

1. **El día de la semana es la señal dominante**: 64 % entre viernes y domingo.
2. **El festivo pesa −38 %** incluso controlando el día de la semana, y se conoce de antemano.
3. **La estacionalidad mensual es débil** frente a la semanal.
4. **2020 debe entrar marcado**, no como un año más.
5. **Comparar medias diarias, no totales**, mientras 2025 esté truncado.
6. **Nada de comparaciones entre localidades** hasta tener población.
