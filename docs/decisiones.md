# Registro de decisiones metodológicas

Cada decisión registra el contexto, las opciones, la evidencia, la decisión tomada y quién la aprobó. Una decisión en estado «Propuesta» todavía no está aprobada.

---

## D-01 · Población que sustenta el mínimo de 500.000 registros (#17, #18)

**Estado:** Propuesta. Pendiente de la respuesta del profesor.
**Fecha:** 2026-11-11.

### Contexto
El enunciado exige trabajar con al menos 500.000 registros. Las tres fuentes autorizadas usan unidades de observación distintas, así que sus filas **no se suman entre sí**.

### Evidencia disponible

| Fuente | Unidad de la fila | Filas de hurto, Bogotá, 2018–2025 | Origen de la cifra |
|---|---|---:|---|
| Línea 123 | Conteo de incidentes por mes × localidad × UPZ × tipo | 25.144 (suman 1.094.313 incidentes) | Auditoría (`outputs/auditoria/`) |
| Fiscalía V3 | Proceso × delito; incluye todas las modalidades de hurto | 1.300.703 (1.297.042 procesos únicos) | Auditoría (`outputs/auditoria/`) |
| Policía Nacional, registro | Víctima o registro (`CANTIDAD = 1`), solo «Hurto a personas» | 130.503 en 2024; unas 742.000 proyectadas para 2020–2025 | Solo se inspeccionó 2024. El resto es una **proyección** con el agregado de MinDefensa (`docs/evidencia_policia_registro.md`) |
| MinDefensa 4rxi-8m8d | Conteo por día y municipio | 2.922 (suman 975.793 hurtos) | API de datos.gov.co |

### Opciones
- **(a) Policía Nacional a nivel de registro, 2020–2025, como población principal.** Es exactamente el fenómeno del proyecto (hurto a personas) y trae variables de víctima y medio.
  - En contra: 2018–2019 no están publicados a nivel de registro, y la nota del archivo advierte que género y edad no tienen calidad validada.
  - El periodo quedaría en 2020–2025, o en 2018–2025 usando el agregado de MinDefensa para 2018–2019, solo en análisis agregados.
- **(b) Fiscalía como población principal.** Supera el mínimo con cifras ya auditadas.
  - En contra: la unidad es el proceso penal, no el hecho; incluye otras modalidades de hurto (automotores, residencias…), y la fecha refleja la denuncia en el sistema judicial.
  - Habría que restringir a la modalidad «a personas» si los campos lo permiten, y volver a contar.
- **(c) Ambas fuentes en paralelo, sin sumarlas.**
  - Policía (a) como fuente del fenómeno y de la variable objetivo.
  - Fiscalía (b) como fuente complementaria de la respuesta institucional.
  - Línea 123 como señal de demanda ciudadana, agregada por localidad y mes.
  - Cada fuente debe sostener el mínimo por sí sola o declararse complementaria.

### Recomendación del equipo (propuesta)
Opción **(c)**, con Policía (a) como población principal **si su auditoría confirma ≥ 500.000 filas para el periodo elegido**.

Esto **no se declara cumplido** hasta ejecutar `scripts/auditoria_datasets.py` sobre los archivos 2020–2025 (#15).

### Preguntas al profesor
1. ¿Basta con que **una** de las fuentes alcance 500.000 registros, o el mínimo se refiere al conjunto integrado?
2. ¿Es aceptable acotar el periodo principal a **2020–2025**, ya que la Policía no publica 2018–2019 a nivel de registro? ¿O prefiere completar esos años con el agregado diario de MinDefensa?
3. ¿Considera válido el **proceso penal de Fiscalía** como unidad de análisis complementaria, aunque no equivalga a un hecho?
4. Si se eligiera Fiscalía como población, ¿habría que restringirla a la modalidad **«a personas»** para que sea comparable con Policía, o se acepta el capítulo completo de hurto? Hoy incluye automotores y residencias, y eso cambia el fenómeno que se modela.

### Condiciones acordadas por el equipo
Las propuso Sara el 2026-11-11 y quedan pendientes de la respuesta del profesor:
- **Una sola unidad en el conteo.** Si el registro de Policía es la población principal, hay dos salidas para 2018–2019:
  - el periodo principal pasa a 2020–2025; o
  - esos dos años entran solo como agregado y **fuera** del conteo de filas.

  Microdato y agregado no se mezclan en el conteo del mínimo.
- **Coherencia del periodo.** Si el periodo cambia a 2020–2025, se actualizan el informe, `README`, `data/README.md` y los notebooks de la segunda entrega (#27). Se decide antes de redactar la sección 4.
- **Concordancia A–B.** La diferencia de una fila en 2024 se rastreó día a día; el detalle está en `docs/evidencia_policia_registro.md`, §3.

### Decisión
_Pendiente._ Al recibir la respuesta, registrar aquí:
- la fecha;
- el texto o el resumen de la respuesta;
- la opción elegida;
- los cambios de alcance en #10, #15, #17 y en el informe.

---

## D-02 · Serie objetivo del pronóstico diario (#8, #27)

**Estado:** Decidida por Sara Albarracín. **Pendiente de confirmación de Juan Diego Rojas.** No está acordada con el equipo.
**Fecha:** 2026-11-12.

### Contexto

D-01 y esta decisión responden preguntas distintas y conviene no confundirlas:

- **El mínimo de 500.000 se mide en filas de una población**, dentro de una única unidad de observación (decisión 10 de la bitácora). Eso es D-01 y se sigue midiendo sobre el **registro** de Policía Nacional.
- **El pronóstico necesita una serie diaria**, es decir una observación por fecha. Eso es D-02.

Una fuente puede servir para lo segundo sin entrar en lo primero. D-01, opción (a), ya lo admite: 2018 y 2019 «solo podrían entrar en **análisis agregados**, fuera del conteo de filas». Un pronóstico diario es un análisis agregado.

El conflicto que obligó a decidir: `data/README.md` asigna el agregado de MinDefensa al «pronóstico diario … entre 2018 y 2025», mientras que la opción (c) de D-01 —la recomendación del equipo— propone «Policía (a) como fuente del fenómeno **y de la variable objetivo**».

### Opciones

**(a) Agregado diario de MinDefensa, 2018–2025.** Una fila por fecha para el municipio 11001.

- A favor: **2.922 observaciones diarias**, cobertura continua y el tramo prepandemia completo.
- En contra: no aporta variables de víctima ni de medio, y no cuenta para el mínimo de 500.000.

**(b) Registro de Policía Nacional agregado a día, 2020–2025.**

- A favor: es la fuente principal del fenómeno (decisión 9 de la bitácora) y trae atributos de víctima.
- En contra: **2.192 observaciones diarias**, 730 menos que (a), un 25 % de la serie. Pierde 2018 y 2019, el único tramo prepandemia.

### Evidencia medida

Verificada el 2026-11-12 sobre `data/raw/hurto_bogota.csv` con la librería estándar de Python:

| Comprobación | Resultado |
|---|---|
| Filas | 2.922 |
| Fechas únicas | 2.922 |
| Rango | 2018-01-01 a 2025-12-31 |
| Días faltantes en el rango | 0 |
| Suma de `cantidad` | 975.793 |
| Códigos de municipio presentes | solo `11001` |

Las cifras descriptivas que publica la segunda entrega reproducen de forma exacta sobre ese archivo: media diaria 333,95; mediana 334,5; máximo 718 el 2022-09-23; mes mayor octubre de 2022 con 16.098; mes menor abril de 2020 con 2.574; viernes el día de mayor promedio con 398,04 y domingo el menor con 230,96; percentil 99 de 2018–2024 en 587,44, con 26 días por encima.

**Concordancia entre las dos opciones:** exacta en 2020, 2021, 2022, 2023 y 2025, y de una unidad en 2024, rastreada día a día (`docs/cruce_policia_registro_agregado.md`, §3). Donde se solapan son la misma serie, así que el único coste real de (b) frente a (a) es la pérdida de 2018–2019.

### Coste de cada opción

| | (a) Agregado 2018–2025 | (b) Registro 2020–2025 |
|---|---:|---:|
| Observaciones diarias | 2.922 | 2.192 |
| Diferencia | — | −730 (−25 %) |
| Tramo prepandemia | Sí | No |
| Reescritura del informe, los dos `README` y los dos notebooks | No | Sí (#27) |
| Rehacer el protocolo de validación, que hoy entrena desde 2018 con bloques 2022, 2023 y 2024 | No | Sí |

### Decisión

Se usa el **agregado diario de MinDefensa, 2018–2025, con 2.922 observaciones**, como serie objetivo del pronóstico diario.

Motivos:

1. Conserva el tramo prepandemia: 730 observaciones más que (b), y con ellas el contraste con abril de 2020, que es el mínimo de toda la serie.
2. La concordancia registro↔agregado está verificada por las dos personas del equipo, así que elegir (a) no introduce una fuente distinta donde ambas se solapan.
3. No compromete D-01: el agregado **no entra** en el conteo del mínimo de 500.000, que se sigue midiendo sobre el registro.

### Qué no decide esto

**D-02 es independiente de la pregunta 2 al profesor.** Esa pregunta es si el periodo **principal** del proyecto se acota a 2020–2025 por la cobertura del registro, y afecta al conteo del mínimo. D-02 solo fija de qué serie se toma la variable objetivo del pronóstico. Si el profesor acota el periodo principal, hay que revisar si la serie del pronóstico lo acompaña, y esa revisión se registra aquí como una decisión nueva, no modificando esta.

D-01 sigue **abierta** y el issue #18 sigue **abierto**, a la espera de la respuesta del profesor.
