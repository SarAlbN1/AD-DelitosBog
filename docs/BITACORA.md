# Bitácora de la Entrega 1

Registro de qué se hizo, a qué hora, qué se decidió y con qué evidencia. Sirve para reconstruir el
trabajo sin releer los PR y para que el informe cite la procedencia de cada cifra.

Horas en hora local de Bogotá (UTC−05:00). Jornada registrada: **2026-11-11**.
Responsables: Sara Albarracín (`SarAlbN1`) y Juan Diego (`Juandi48`).

---

## 1. Cronología

### Tarde: herramienta y primeras auditorías

| Hora | Quién | Qué | Evidencia |
|---|---|---|---|
| 12:31 | Juan | Primera versión de `scripts/auditoria_datasets.py` | `5c7a0a2` |
| 12:32 | Juan | Abre el PR #63 con el script de auditoría | PR #63 |
| 12:42 | Juan | Script para crear y vincular el tablero Kanban | `37d227a`, PR #64 |
| 14:37 | Juan | Descarga y auditoría de Procesos Fiscalía V3: 2.002.177 filas | `180e18f` |
| 14:47 | Juan | Auditoría de Línea 123: 1.117.394 filas | `1483477` |
| 15:10 | Juan | Verificación de las 8 referencias de la bibliografía | `85cb6f0`, PR #65 |

### Tarde: tablero y reglas de trabajo

| Hora | Quién | Qué | Evidencia |
|---|---|---|---|
| ~16:00 | Sara | Añade el estado **Blocked** al campo `Status` del tablero, asigna estado a los 62 items a partir del grafo de dependencias, asigna las épicas #58–#62 a ambos y renombra el proyecto a «AD-DelitosBog — Backlog» | [Proyecto 11](https://github.com/users/SarAlbN1/projects/11) |
| 16:24 | Sara | Publica el avance local de la segunda entrega en `sara/entrega2` | `3dcf0c3` |
| 16:34 | Sara | `CLAUDE.md` y `CONTRIBUTING.md` adaptados al proyecto | `1734fbc`, PR #66 |
| 16:35 | Sara | Abre el PR #66 con las reglas de trabajo | PR #66 |
| 16:39 | Sara | Abre el PR #67 con el avance de la segunda entrega | PR #67 |
| 16:55 | Sara | Alinea `README.md` y `data/README.md` con las tres fuentes | `f05b563` |
| 16:57 | Sara | Abre el PR #68 | PR #68 |
| 17:11 | Sara | Elimina el estado `Ready` del tablero: el backlog es `To-do` y no hay estado intermedio | `b9835d9` |

### Noche: Policía a nivel de registro

| Hora | Quién | Qué | Evidencia |
|---|---|---|---|
| 20:10 | Juan | Documenta que «Policía» son **dos recursos distintos** e inspecciona el archivo de 2024: 130.503 filas de hurto en Bogotá frente a 130.504 del agregado | `32529af`, PR #69 |
| 20:10 | Juan | Registra la decisión D-01 sobre la población del mínimo, con tres opciones y preguntas al profesor | `0d917da` |
| 20:36 | Sara | Ejecuta el script del PR #63 sobre Línea 123 y el agregado de MinDefensa. Corre sin errores | `outputs/auditoria/` |
| 20:38 | Sara | **Corrige una cifra propia:** las 36.142 filas de hurto de Línea 123 eran de todo el archivo (2015–2026); en 2018–2025 son **25.144** | `22d557a` |
| 20:39 | Sara | Separa en `data/README.md` el registro de Policía del agregado de MinDefensa | `c0ae329` |
| 20:54 | Juan | Implementa el descarte del pie de los archivos Excel y lo registra en `anomalias.csv` | `e669553` |
| 20:55 | Juan | Rastrea la diferencia A–B día a día en 2024 y añade la cuarta pregunta al profesor | `68e6f73` |
| 21:05 | Juan | Guía de reproducción de la Entrega 1 | `20bdf51`, PR #70 |
| 21:05 | Juan | Citas autor-año y referencias en APA 7 en el informe | `b4013a7`, PR #71 |
| 21:10 | Sara | **Aprueba y fusiona el PR #63** con squash, tras re-revisar el delta y correr las pruebas | `71d42fe` |
| 21:13 | Juan | Matriz comparativa de trabajos relacionados | PR #72 |
| 21:15 | Juan | Unidades de observación y posibilidades de integración | PR #73 |
| 21:47 | Sara | Cierra #9, #11, #12, #13, #14 y #16 con su evidencia | Issues cerradas |
| 22:03 | Sara | Descarga, convierte y audita los seis archivos de registro de Policía: **741.986 filas** de hurto a personas en Bogotá | `5125fcd` |
| 22:04 | Sara | Abre el PR #74 | PR #74 |
| 22:06 | Sara | Actualiza el PR #68 con las cifras ya auditadas | `99bde01` |

---

## 2. Decisiones tomadas

Las decisiones metodológicas formales viven en [`docs/decisiones.md`](decisiones.md). Aquí quedan las
decisiones de trabajo, con el motivo, porque explican por qué el repositorio está como está.

| # | Decisión | Motivo | Dónde |
|---|---|---|---|
| 1 | El tablero tiene cinco estados: `To-do`, `In progress`, `In review`, `Blocked`, `Done` | Se añadió `Blocked` porque 46 de 62 tareas tenían dependencias abiertas y no se distinguían del backlog. `Ready` se eliminó después: no aportaba nada frente a `To-do` | `CONTRIBUTING.md` |
| 2 | El estado `Blocked` se deriva de la sección `## Dependencias / bloqueos` del cuerpo de cada issue | Da una fuente única y recalculable, en lugar de un criterio manual | `CONTRIBUTING.md` |
| 3 | El autor no aprueba ni fusiona su propio PR. Siendo dos, el revisor es siempre el otro | Revisión cruzada real, sin excepciones por urgencia | `CONTRIBUTING.md` |
| 4 | Un asistente puede comunicar hallazgos, pero no vota, aprueba ni fusiona sin autorización expresa para esa acción y ese PR | Mantiene la responsabilidad en la persona que delega | `CONTRIBUTING.md` |
| 5 | Los commits, los PR y los comentarios no llevan menciones a asistentes, firmas de generación automática ni trailers `Co-authored-by` | Las declaraciones académicas sobre asistencia siguen las indicaciones del curso, no el historial de Git | `CLAUDE.md` |
| 6 | «MinDefensa» no se borra de `data/README.md`: **es** la fuente Policía y se renombra | Borrarla dejaba el proyecto sin esa fuente | PR #68 |
| 7 | La capa de la Secretaría Distrital de Seguridad sale de la tabla de fuentes y queda como capa de apoyo | Es la geometría de localidades que usan los mapas, no una fuente de delito | PR #68 |
| 8 | TransMilenio queda descartada de forma explícita | No existía en ningún archivo del repositorio; se buscó en todos los `.md`, `.tex` e `.ipynb` | Issue #1 |
| 9 | «Policía» son dos recursos: el **registro** anual (fuente principal) y el **agregado diario** de MinDefensa (control de consistencia) | Tienen unidades de observación distintas y uno es la agregación del otro | PR #69, PR #74 |
| 10 | El mínimo de 500.000 se mide en **filas**, dentro de una única unidad de observación, nunca por la suma de una columna de conteo | La suma de `cantidad` en el agregado da 975.793 con solo 2.922 filas. Confundirlas invalidaría el requisito | `reporte_auditoria.md` |
| 11 | Las fuentes **no se suman entre sí** | Una misma situación puede generar una llamada, un registro policial y un proceso | PR #73 |
| 12 | Se aprueba y fusiona el PR #63, reclasificando como **no bloqueante** la falta de la entrada de Policía en el manifiesto | Era una omisión, no un defecto, y se rellenó en el PR #74 | PR #63 |
| 13 | Los `.xlsx` de Policía **no se auditan directamente**: se convierten antes a CSV en streaming | La rama de Excel del script carga el archivo completo en memoria antes de trocearlo, y son ~800.000 filas por año | PR #74 |
| 14 | El filtro de hurto del registro usa `DELITOS`, no `ICCS` | `ICCS` no existe en el archivo de 2023 | PR #74 |
| 15 | La fila del encabezado se **detecta**, no se fija en el manifiesto | Está en la fila 12 en cuatro años y en la 13 en dos | PR #74 |
| 16 | **Prohibida la deduplicación por fila exacta en el registro de Policía** | 713.344 de 741.986 filas son duplicados exactos: dos víctimas del mismo perfil el mismo día son indistinguibles y no hay identificador | PR #74 |

### Decisión pendiente

**D-01, la población que sustenta el mínimo (#17, #18).** Está formulada en `docs/decisiones.md` con
tres opciones y cuatro preguntas al profesor. Depende de un hecho que ya está verificado: el registro
de Policía solo cubre 2020–2025. Mezclarlo con el agregado para cubrir 2018–2019 rompe la unidad de
observación única con la que se mide el mínimo.

---

## 3. Proceso de verificación aplicado

Lo que se hizo para que las cifras del informe sean defendibles, y no solo plausibles.

1. **Toda cifra sale de un script, no de una inspección manual.** `scripts/auditoria_datasets.py`
   produce `outputs/auditoria/` y `outputs/auditoria_policia/`, con el SHA-256 de cada archivo leído.
2. **Las descargas se congelan y se hashean.** Los seis archivos de Policía quedan con URL, fecha,
   bytes y SHA-256 en `docs/cruce_policia_registro_agregado.md`.
3. **Verificación cruzada entre las dos personas.** El SHA-256 del archivo de 2024 que descargó Sara
   coincide con el que publicó Juan, así que la inspección de ese archivo es reproducible. El rastreo
   de la diferencia A–B se hizo por separado y los siete días de marzo de 2024 salieron idénticos en
   ambos conteos.
4. **Las correcciones se registran, no se tapan.** La cifra de Línea 123 pasó de 36.142 a 25.144 al
   aplicar el filtro de periodo antes del de hurto, y el cambio quedó en su propio commit con el
   motivo.
5. **Se separa lo verificado de lo proyectado.** Las ~742.000 filas fueron una proyección etiquetada
   como tal hasta que la auditoría dio 741.986 sobre los archivos descargados.
6. **Lo que no se pudo comprobar queda escrito como pendiente**, en lugar de darse por bueno.

---

## 4. Estado al cierre de la jornada

**Cifras verificadas del requisito de 500.000 registros**

| Fuente | Unidad de la fila | Filas de hurto en Bogotá | Periodo | ¿Alcanza el mínimo? |
|---|---|---:|---|---|
| Policía Nacional, registro | Una víctima (`CANTIDAD` = 1) | **741.986** | 2020–2025 | Sí |
| Fiscalía V3 | Proceso × delito | 1.300.703 | 2018–2025 | Sí |
| Línea 123 | Conteo por mes × localidad × UPZ × tipo | 25.144 | 2018–2025 | No |
| MinDefensa, agregado diario | Conteo por día y municipio | 2.922 | 2018–2025 | No |

**Concordancia entre el registro y el agregado:** exacta en 2020, 2021, 2022, 2023 y 2025. En 2024
difieren en una unidad, repartida en siete días de marzo que se compensan entre sí.

**Tablero:** 6 Done, 10 In review, 3 In progress, 6 To-do, 37 Blocked, sobre 62 items.

**Issues cerradas:** #9, #11, #12, #13, #14, #16.

**Pull requests abiertos:** #64 a #74.

### Pendientes conocidos

- **D-01:** mandar las cuatro preguntas al profesor y registrar la respuesta (#18).
- Si el periodo principal queda en 2020–2025, hay que actualizar el informe, el `README.md` y los
  notebooks, que dicen 2018–2025 (#27 y la segunda entrega).
- #19, #20, #21 y #22 siguen bloqueados por #15, que está en revisión en el PR #74.
- La auditoría de las cuatro fuentes en un reporte único necesita el CSV de Fiscalía en la copia
  local donde se ejecuta.
- Crear la vista Board agrupada por `Status` en el tablero, que es un paso manual en la web.

---

## 5. Cómo mantener esta bitácora

Una fila por hecho con hora, autor y evidencia verificable (commit, PR o issue). Las decisiones se
añaden a la tabla de la sección 2 con su motivo; si una decisión se revierte, no se borra: se añade
la nueva con el motivo del cambio. Las cifras no se escriben a mano: se copian de las salidas de la
auditoría y se dice de qué archivo vienen.
