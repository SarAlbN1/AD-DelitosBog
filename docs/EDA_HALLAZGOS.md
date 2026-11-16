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
| Lunes laborable | 323,9 | 242 |
| **Diferencia** | **−37,8 %** | |

El efecto se sostiene al controlar el día de la semana: **en un lunes festivo se registran un 38 %
menos de víctimas que en un lunes laborable.** El festivo debe ser una predictora del modelo, y el
calendario de festivos se conoce de antemano, así que no introduce fuga.

Hay 103 festivos en el periodo, y 304 lunes: 62 festivos y 242 laborables. El script emite esos conteos para que no se escriban a mano.

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
contando filas, y acotado a **2020–2025** para que coincida con el periodo de la serie objetivo y
con la tabla de la sección 4. Los porcentajes se calculan sobre el total del periodo, 821.304
incidentes, incluidos los que no tienen localidad.

### Por conteo

| Localidad | Incidentes | % |
|---|---:|---:|
| Kennedy | 99.525 | 12,12 % |
| Engativá | 93.654 | 11,40 % |
| Suba | 93.132 | 11,34 % |
| Bosa | 52.210 | 6,36 % |
| Ciudad Bolívar | 48.636 | 5,92 % |

Los incidentes **sin localidad asignada** son 5.683, el **0,69 %**. Se separan porque «SIN
LOCALIZACION» no es una localidad y porque no tienen población con la que calcular una tasa.

### Por tasa, que es otra historia

Tasa de **llamadas tramitadas por 100.000 habitantes**, con la población de cada año (proyecciones
de la SDP, marzo de 2025).

| Localidad | Incidentes | Puesto por conteo | Tasa por 100.000 | Puesto por tasa | Cambio |
|---|---:|---:|---:|---:|---:|
| Los Mártires | 29.033 | 14 | **5.736** | **1** | +13 |
| Antonio Nariño | 19.521 | 17 | 4.036 | 2 | +15 |
| Santa Fe | 25.991 | 15 | 3.896 | 3 | +12 |
| Barrios Unidos | 30.974 | 13 | 3.675 | 4 | +9 |
| Teusaquillo | 33.702 | 11 | 3.578 | 5 | +6 |
| Chapinero | 33.584 | 12 | 3.379 | 6 | +6 |

Y las que caen al normalizar:

| Localidad | Incidentes | Puesto por conteo | Tasa por 100.000 | Puesto por tasa |
|---|---:|---:|---:|---:|
| Kennedy | 99.525 | **1** | 1.552 | **12** |
| Engativá | 93.654 | 2 | 1.891 | 8 |
| Suba | 93.132 | 3 | 1.255 | 15 |
| Bosa | 52.210 | 4 | 1.164 | 17 |
| Ciudad Bolívar | 48.636 | 6 | 1.223 | 16 |

**El orden se da la vuelta.** Kennedy pasa del puesto 1 por conteo al 12 por tasa. Los Mártires,
que era el 14 por conteo, es el **primero** por tasa, con una tasa 3,7 veces la de Kennedy. Antonio
Nariño sube 15 puestos.

Esto confirma lo que el conteo no podía decir: **el conteo mide tamaño de población, no intensidad
del fenómeno.** Si el informe hubiera presentado el orden por conteo como un ranking, habría
señalado a las localidades más pobladas y habría pasado por alto las que concentran más llamadas
por habitante.

### Lo que esta tasa no es, y hay que decirlo

1. **No es una tasa de hurtos.** Línea 123 cuenta llamadas tramitadas, así que la tasa mide
   **demanda de atención** por habitante, no victimización.
2. **No capta la población flotante.** Los Mártires, Santa Fe, La Candelaria, Chapinero y
   Teusaquillo reciben cada día a mucha gente que no vive allí: trabajo, comercio, transporte. Su
   tasa por residente sale inflada, y es muy probable que eso explique buena parte de que encabecen
   la tabla. **Sin una medida de población flotante esa parte no se puede separar.**
3. **Sumapaz es inestable.** Es rural, tiene la menor población de la ciudad y muy pocas llamadas en
   todo el periodo, así que su tasa de 213 por 100.000 se mueve mucho con pocos casos.
4. **El orden cambia, pero no es un ranking de peligrosidad.** Ni por conteo ni por tasa. Las dos
   medidas describen dónde se pide atención, con sesgos distintos.

Se presentan **las dos cosas**, conteo y tasa, precisamente para que se vea cuánto cambia el orden
al normalizar.

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
6. **Las comparaciones entre localidades se hacen por tasa, no por conteo.** El orden cambia por
   completo al normalizar: Kennedy pasa del puesto 1 al 12. Y ni siquiera la tasa es un ranking de
   peligrosidad, porque no capta la población flotante.
