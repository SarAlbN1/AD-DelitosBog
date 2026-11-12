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
