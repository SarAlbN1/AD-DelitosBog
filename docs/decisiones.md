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
- Los notebooks de la segunda entrega deben pasar a la serie del registro 2020–2025; queda en un issue aparte.
- Hay que verificar la caída de noviembre y diciembre de 2025 antes de usar esos meses para evaluar modelos; queda en un issue aparte.
