# Registro de decisiones metodológicas

Cada decisión registra el contexto, las opciones, la evidencia, la decisión tomada y quién la aprobó. Una decisión en estado «Propuesta» todavía no está aprobada.

---

## D-01 · Población que sustenta el mínimo de 500.000 registros (#17, #18)

**Estado:** Decidida por el equipo el 2026-11-12, sin consulta al profesor. Ver [Decisión](#decisión).
**Fecha:** propuesta el 2026-11-11; decidida el 2026-11-12.

### Contexto
El enunciado exige trabajar con al menos 500.000 registros. Las tres fuentes autorizadas usan unidades de observación distintas, así que sus filas **no se suman entre sí**.

### Evidencia disponible

| Fuente | Unidad de la fila | Filas de hurto, Bogotá, 2018–2025 | Origen de la cifra |
|---|---|---:|---|
| Línea 123 | Conteo de incidentes por mes × localidad × UPZ × tipo | 25.144 (suman 1.094.313 incidentes) | Auditoría (`outputs/auditoria/`) |
| Fiscalía V3 | Proceso × delito; incluye todas las modalidades de hurto | 1.300.703 (1.297.042 procesos únicos) | Auditoría (`outputs/auditoria/`) |
| Policía Nacional, registro | Víctima o registro (`CANTIDAD = 1`), solo «Hurto a personas» | **741.986** en 2020–2025 (no hay archivos de registro de 2018–2019) | Auditoría de los seis archivos anuales (`outputs/auditoria_policia/`, `docs/cruce_policia_registro_agregado.md`) |
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

### Preguntas al profesor (retiradas)
Se retiraron el 2026-11-12: el equipo tomó la decisión sin consultarlas. Se conservan como registro de lo que se valoró.

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
**Fecha:** 2026-11-12. **Decidida por:** Juan Diego (`Juandi48`). **Revisión:** Sara (`SarAlbN1`), en el PR que registra esta decisión.
**Respuesta del profesor:** no se consultó. El equipo decidió no hacerlo, porque las cuatro preguntas se pueden resolver con los datos auditados.
**Opción elegida:** (c), con la Policía (a) como población principal. La auditoría confirmó la condición que exigía la recomendación.

1. **Fuente principal: Policía Nacional, registro.** Son 741.986 filas de hurto a personas en Bogotá, 2020–2025, cada una una víctima (`CANTIDAD = 1`). La fuente cumple por sí sola el mínimo de 500.000. No se combina con otras fuentes para alcanzarlo.
   - Evidencia: `outputs/auditoria_policia/`.
   - Reproducida de forma independiente el 2026-11-12 con una segunda descarga de los seis archivos: mismos SHA-256, mismo embudo (4.829.870 → 1.406.157 → 741.986), mismos nulos y duplicados.
   - Concordancia con el agregado de MinDefensa: 741.987, una fila de diferencia (`docs/cruce_policia_registro_agregado.md`).
2. **Periodo principal: 2020–2025.** Son los años con registro individual.
   - 2018 y 2019 solo entran como contexto histórico, con el agregado diario de MinDefensa.
   - Ese agregado no forma parte del conteo del mínimo ni de la serie objetivo. Agregado y registro no se mezclan para aumentar observaciones.
3. **Fiscalía: fuente complementaria.** Se usan las 1.300.703 filas proceso–delito del capítulo «Del Hurto», 2018–2025 (991.471 en 2020–2025), para:
   - comparar tendencias;
   - analizar la evolución de las noticias criminales;
   - estudiar distribuciones por tipo penal;
   - examinar diferencias con el registro policial.

   Sus filas no son víctimas ni hechos únicos.
4. **Fiscalía no se restringe a «hurto a personas», porque no es posible.** `delito` codifica el tipo penal, no la víctima (`scripts/fiscalia_modalidades.py`, `outputs/informe/fiscalia_modalidades_resumen.csv`).
   - Solo se pueden excluir 123.506 filas de modalidades nombradas: vehículos, establecimientos y otras.
   - De las 1.177.197 restantes, 1.108.399 (94,2 %) son tipos genéricos.

   Por eso Fiscalía se describe siempre como «hurto en todas sus modalidades», sus artículos y categorías quedan documentados, y no se compara en magnitud con la Policía.
5. **Línea 123: fuente complementaria.** Se usa para:
   - tendencias mensuales;
   - la distribución por localidad y UPZ, sumando `CANT_INCIDENTES`;
   - comparar tendencias con la Policía.

   Sus variables solo entran al modelo con justificación metodológica y con el rezago con que estarían disponibles al pronosticar.
6. **Variable objetivo: número diario de víctimas de hurto a personas registradas en Bogotá** (Policía, 2020–2025).
   - Conjunto original: 741.986 filas. Conjunto de modelamiento: serie diaria de 2.192 días, sin días vacíos (`scripts/serie_objetivo_policia.py`, `outputs/serie_objetivo/`). Las dos cantidades se documentan por separado.
   - Un pronóstico por localidad no es viable con esta fuente, porque el registro no identifica la localidad.
   - El horizonte del pronóstico queda abierto en #37.

**Relación con otras decisiones abiertas:**
- **D-02 (PR #84).** Proponía el agregado de MinDefensa 2018–2025 como serie objetivo. Esta decisión fija en su lugar el registro 2020–2025. Como las dos fuentes coinciden día a día salvo en siete días de marzo de 2024, la serie de 2020–2025 es la misma; lo que cambia es el periodo de entrenamiento.
- **D-03 (PR #79).** Partía de que `delito` permitía filtrar «a personas». El punto 4 la resuelve.

**Cambios de alcance:**
- El informe usa 2020–2025 en el título, el alcance, los objetivos y la sección 4.
- Los notebooks de la segunda entrega deben pasar a la serie del registro 2020–2025 (#87).
- Hay que verificar la caída de noviembre y diciembre de 2025 antes de usar esos meses para evaluar modelos (#86).

---

## D-04 · Horizonte, comparadores y protocolo de evaluación (#37)

**Estado:** Aprobada por el equipo. Propuesta por Sara el 2026-11-13, aprobada por Juan Diego el
2026-11-14 con un cambio en la barra a batir.
**Fecha:** 2026-11-14.

### Contexto
D-01 fijó la variable objetivo y la unidad: víctimas de hurto a personas registradas por día en
Bogotá, del registro de la Policía. Faltaban el horizonte, la barra a batir, las métricas y la
partición.

### Decisiones

| Tema | Decisión |
|---|---|
| **Horizonte** | Un día: se predice `t+1`. Es lo que plantea la pregunta de investigación y el único horizonte en el que todas las predictoras están disponibles sin supuestos adicionales |
| **Barra a batir** | El **mejor de los cuatro comparadores triviales sobre el mismo conjunto de evaluación del modelo**. No se fija un comparador a priori |
| **Métricas** | MAE principal, RMSE secundaria, MAPE informativa |
| **Partición** | Entrenamiento 2020-01-01 → 2025-04-30 (1.947 días); evaluación 2025-05-01 → 2025-10-31 (184 días). Validación de origen móvil dentro del entrenamiento |
| **2020** | Se conserva, con un indicador explícito de año atípico, y se comprueba la sensibilidad entrenando también sin él |

### Por qué la barra es «el mejor de los cuatro» y no un comparador fijo

La propuesta inicial fijaba la persistencia `t-1` como barra, a partir de una tabla calculada sobre
los últimos 365 días. Juan Diego señaló que la ventana de evaluación es otra, y que **el orden de
los comparadores cambia con la ventana**:

| Comparador | Últimos 365 días | Ventana de evaluación (2025-05-01 → 2025-10-31) |
|---|---|---|
| Persistencia `t-1` | MAE **55,2** · RMSE 72,3 | MAE 52,9 · RMSE 68,4 |
| Mismo día semana anterior `t-7` | MAE 57,5 · RMSE 77,1 | MAE **49,0** · RMSE **61,4** |
| Media previa de 7 días | MAE 56,0 · RMSE **70,5** | MAE 49,4 · RMSE 61,9 |
| Media previa de 28 días | MAE 64,8 · RMSE 82,9 | MAE 55,8 · RMSE 70,7 |

En los últimos 365 días gana la persistencia; en la ventana de evaluación gana el rezago 7. Fijar un
comparador a priori habría puesto la barra en el sitio equivocado, así que **la barra se calcula
sobre el mismo conjunto en el que se evalúa el modelo**. Con la partición acordada, eso significa
batir el rezago 7: MAE 49,0 y RMSE 61,4.

Se reportan los cuatro comparadores, no solo el ganador. La media de la serie en la ventana de
evaluación es 366,8 víctimas al día; la de toda la serie es 343,0.

### Un comparador débil no sirve como barra
La pregunta del `README` propone batir «el mismo día de la semana anterior». Sobre los últimos 365
días ese comparador es **peor** que la persistencia simple, así que superarlo no habría demostrado
nada. De ahí la regla: la barra es el mejor de los triviales, no el que la pregunta mencione.

### El corte de la serie es parte de esta decisión
La serie termina el **2025-10-31** y no el 31 de diciembre, porque noviembre y diciembre de 2025 no
son comparables (#86, `docs/verificacion_caida_2025.md`). Importa aquí: esos dos meses habrían caído
en el conjunto de evaluación de cualquier partición considerada, y habrían hecho que cualquier
modelo pareciera acertar un descenso que no ocurrió.

### Evidencia
Cifras calculadas sobre `data/processed/serie_objetivo_diaria.csv` (2.131 días), verificadas de
forma independiente por las dos personas del equipo.
