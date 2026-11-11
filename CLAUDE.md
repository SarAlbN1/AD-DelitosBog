# CLAUDE.md · Reglas de trabajo para AD-DelitosBog

Proyecto de análisis de datos sobre hurto en Bogotá, en tres entregas académicas. Lo llevan dos personas: Sara Albarracín (`SarAlbN1`) y Juan Diego (`Juandi48`). Lee [CONTRIBUTING](CONTRIBUTING.md) antes de modificar archivos. Las reglas de revisión, aprobación y fusión, incluida la actuación de un asistente en nombre de otro colaborador, están en la [política de integración](CONTRIBUTING.md#pull-requests-y-releases).

No hay wiki ni documentos de arquitectura. Las fuentes de verdad son estas, en este orden:

1. El **enunciado del laboratorio** fija las obligaciones académicas, entre ellas el mínimo de 500.000 registros. Si falta una fuente que confirme un requisito, registra la incertidumbre y pídela. No deduzcas el requisito a partir de los datos que haya a mano.
2. Las **issues y el tablero** definen el alcance, el responsable y las dependencias de cada tarea. El backlog está en [GitHub Projects](https://github.com/users/SarAlbN1/projects/11); las épicas son las issues #58 a #62.
3. **[data/README.md](data/README.md)** mantiene, por dataset, su URL, su filtro, su fecha de descarga y su unidad de observación. Ningún otro documento define esos datos.
4. Este archivo aplica las reglas del equipo al trabajo con asistentes. Ante discrepancias, señala la fuente afectada y propón la corrección donde se mantiene.
5. El **informe en LaTeX** presenta el trabajo. Contrasta sus afirmaciones con el enunciado, las issues y los resultados obtenidos. Coordina las correcciones con quien mantiene cada sección.

Los scripts, los notebooks ejecutados, los commits y los archivos de `outputs/` son la evidencia del estado real. Una cifra sin un script o un archivo que la produzca es un pendiente, no un resultado.

## Reparto entre las dos personas

| Responsable | Secciones y temas |
|---|---|
| Sara (`SarAlbN1`) | Preprocesamiento, análisis exploratorio, metodología, fuente Policía y modelado |
| Juan Diego (`Juandi48`) | Introducción, trabajos relacionados, descripción de fuentes y sección 4 |
| Ambos | Requisito de 500.000 registros, diccionario de datos, unidades de observación e integración, revisión cruzada y compilación final |

Antes de tocar una sección ajena, confírmalo con su responsable. Si encuentras un defecto fuera de tu alcance, repórtalo en la issue en vez de corregirlo por tu cuenta.

## Dónde está cada cosa

| Tarea | Fuentes |
|---|---|
| Alcance, responsable y dependencias | La issue vinculada y el [tablero](https://github.com/users/SarAlbN1/projects/11) |
| Fuentes de datos, URL, filtros y unidad de observación | [data/README.md](data/README.md) |
| Preparar y ejecutar el proyecto | [README.md](README.md) |
| Preprocesamiento, EDA y metodología | [docs/segunda_entrega.md](docs/segunda_entrega.md) y los notebooks de `notebooks/` |
| Auditoría de datasets y cifras de la sección 4 | `scripts/auditoria_datasets.py` y sus salidas en `outputs/auditoria/` |
| Ramas, commits y pull requests | [CONTRIBUTING](CONTRIBUTING.md#ramas-y-commits) |

## Datos

- No publiques datasets en Git. `data/raw/` y `data/processed/` están en `.gitignore` y así se quedan. Los datos se reproducen con las instrucciones de descarga de [data/README.md](data/README.md).
- Antes de usar una cifra, comprueba a qué corresponde. Varias fuentes vienen agregadas: una fila puede ser un conteo y no un hecho ni una víctima. Confundir el número de filas con la suma de una columna de cantidad invalida el conteo de registros.
- Si vuelves a descargar una fuente, anota la nueva fecha de corte. Los portales actualizan los recursos y las cifras cambian entre descargas.

## Trabajo con asistentes

- Confirma el alcance y los permisos antes de intervenir en trabajo ajeno o modificar GitHub. Aplica las [reglas de ramas y commits](CONTRIBUTING.md#ramas-y-commits) y la [política de integración](CONTRIBUTING.md#pull-requests-y-releases).
- Al iniciar una issue, abrir o preparar su PR para revisión, o verificar su cierre, actualiza su tarjeta en el tablero como parte de la misma tarea. Aplica los [estados del tablero](CONTRIBUTING.md#estados-del-tablero). Comprueba las dependencias antes de iniciar y verifica el estado guardado.
- Puedes revisar un PR y comunicar hallazgos sin emitir un voto. Si te piden aprobar o fusionar en nombre de un colaborador, aplica las condiciones de la [revisión delegada](CONTRIBUTING.md#revisión-delegada-a-un-asistente) y detente si la identidad, la autorización o el estado del PR no coinciden.
- No alteres una decisión metodológica, la definición de una fuente ni la unidad de observación sin pedir revisión. Esas decisiones viven en sus issues (#18, #22, #37).
- Informa en el chat de los cambios, las comprobaciones, los resultados y los pendientes. Consulta antes de crear documentos nuevos y actualiza la fuente que mantiene cada dato.

### Responsabilidad y autoría

- La persona que solicita el cambio conserva la responsabilidad sobre su alcance y su validación. El asistente documenta qué comprobó y qué queda pendiente, y preserva los datos sensibles.
- Para las declaraciones académicas sobre el uso de asistencia, sigue las indicaciones del curso.
- En GitHub, los mensajes de commit, las descripciones de los pull requests y los comentarios se centran en el trabajo y su evidencia. Omite las menciones a herramientas o asistentes de IA, las firmas de generación automática y los créditos de autoría o coautoría a asistentes, incluidos los trailers `Co-authored-by`.

### Actualización del tablero

Cuando trabajes en una issue, consulta su tarjeta, sus dependencias y los PRs vinculados en GitHub. Actualiza la tarjeta en la misma sesión en que ocurra el cambio, conforme a los [estados del tablero](CONTRIBUTING.md#estados-del-tablero).

1. Al comenzar el trabajo efectivo, marca **In progress**. Si una dependencia impide avanzar, marca **Blocked** y registra en la issue cuál es.
2. Al abrir un PR listo para revisión que entrega la issue, o al sacar ese PR de borrador, marca **In review**.
3. Al confirmar que el cambio está integrado, que los criterios se verificaron y que la issue está cerrada, marca **Done**. Revisa después las tarjetas que dependían de ella y pasa a **Ready** las que se quedaron sin dependencias abiertas.

Verifica que el cambio de estado se guardó. Si faltan permisos, la tarjeta no está en el tablero o el vínculo entre la issue y el PR es ambiguo, informa el pendiente en el resumen de la tarea.
