# Cómo contribuir a AD-DelitosBog

Proyecto de análisis de datos llevado por dos personas: Sara Albarracín (`SarAlbN1`) y Juan Diego (`Juandi48`). Empieza por el [README](README.md) para preparar y ejecutar el proyecto. No hay wiki: cada decisión se mantiene en su issue o en el archivo que la documenta.

| Para | Fuente |
|---|---|
| Confirmar alcance, responsables y dependencias | La issue vinculada y el [tablero del proyecto](https://github.com/users/SarAlbN1/projects/11) |
| Conocer una fuente de datos, su URL, su filtro y su unidad de observación | [data/README.md](data/README.md) |
| Preparar una rama y registrar cambios | [Ramas y commits](#ramas-y-commits) |
| Cambiar una decisión metodológica, una fuente o la unidad de observación | La issue de decisión correspondiente (#18, #22, #37), antes de tocar código |
| Validar el trabajo y documentar evidencia | Las salidas de `outputs/auditoria/` y los criterios de calidad de #7 |
| Abrir, revisar, aprobar o fusionar un PR | [Pull requests y releases](#pull-requests-y-releases) |
| Trabajar con un asistente | [CLAUDE.md](CLAUDE.md) |

## Estados del tablero

Actualiza la tarjeta de la issue en el [tablero de AD-DelitosBog](https://github.com/users/SarAlbN1/projects/11) cuando cambie su situación. El campo `Status` tiene estos valores:

- **To-do**. La tarjeta está en el backlog y todavía no se ha evaluado si puede iniciarse.
- **Ready**. La tarea no tiene dependencias abiertas y puede tomarse.
- **Blocked**. Una dependencia abierta impide avanzar. Registra en la issue qué dependencia la bloquea. Cuando se resuelva la última, pasa la tarjeta a **Ready** si el trabajo aún no comenzó, o al estado que corresponda según el avance real.
- **In progress**. Mueve la tarjeta al comenzar el trabajo efectivo. Un PR en borrador mantiene este estado si el trabajo puede seguir.
- **In review**. Mueve la tarjeta cuando haya un PR abierto, listo para revisión y vinculado a la entrega de la issue. Un PR parcial que solo referencia la issue no cambia el estado de la issue completa.
- **Done**. Mueve la tarjeta cuando el cambio esté integrado, se hayan verificado los criterios y la issue esté cerrada.

Las dependencias se declaran en la sección `## Dependencias / bloqueos` del cuerpo de cada issue. Esa sección es la fuente del estado **Blocked**: si la cambias, actualiza la tarjeta.

## Ramas y commits

- `main` es la rama de integración. No se trabaja directamente sobre ella.
- Una rama por tarea, con el prefijo de su responsable o de su tipo: `sara/<tema>`, `juandi/<tema>`, `feat/<tema>`, `docs/<tema>`, `chore/<tema>`.
- No modifiques, renombres, rebases ni borres una rama ajena. Tampoco reescribas el historial de una rama compartida ni hagas `force push` sobre ella. Si una rama necesita cambios y no es tuya, pídelo a quien la abrió.
- Commits en imperativo, con un propósito por commit, y referencia a la issue cuando exista. Usa `Closes #<número>` solo en el PR y solo para la issue que el PR cierra de verdad.
- No subas datasets ni archivos pesados. `data/raw/` y `data/processed/` están en `.gitignore`. Si un cambio exige tocar `.gitignore`, explícalo en el PR.
- Los mensajes de commit, las descripciones de los PR y los comentarios se centran en el trabajo y su evidencia. Sin menciones a herramientas o asistentes de IA, sin firmas de generación automática y sin créditos de autoría o coautoría a asistentes, incluidos los trailers `Co-authored-by`. Ver [responsabilidad y autoría](CLAUDE.md#responsabilidad-y-autoría).
- Borra la rama después de fusionar, solo si es tuya.

## Pull requests y releases

Esta página es la fuente de las reglas de revisión, aprobación y fusión de AD-DelitosBog. Describe el proceso del equipo. La configuración efectiva de protección de `main` en GitHub queda por verificar.

### Abrir y revisar un PR

1. Integra los cambios a `main` mediante PR desde una rama propia. Usa el flujo de [ramas y commits](#ramas-y-commits).
2. Describe el cambio, sus criterios y las comprobaciones ejecutadas. Indica los resultados y pendientes. Enlaza la issue cuando exista y usa `Closes #<número>` solo para la issue real que cierre el PR.
3. Solicita revisión a la otra persona del equipo. Somos dos, así que el revisor es siempre quien no escribió el cambio: el autor no aprueba ni fusiona su propio PR, ni siquiera cuando el cambio es pequeño o urgente.
4. La revisión comprueba el último commit del PR, los criterios aplicables y la evidencia. Los hallazgos que impidan la integración se resuelven antes de fusionar. Una revisión que solicita cambios debe quedar resuelta por quien la emitió.
5. Un commit nuevo exige volver a verificar el PR y obtener una aprobación vigente para ese commit. El estado fusionable de GitHub por sí solo no satisface la revisión.
6. Si el PR cambia una cifra del informe, incluye el archivo de `outputs/` o el comando que la produce. Una cifra sin evidencia reproducible bloquea la revisión.

### Revisión delegada a un asistente

- Un asistente puede analizar un PR y comunicar hallazgos. Para publicar una revisión, registrar una aprobación o fusionar en GitHub, debe tener autorización expresa para esa acción y ese PR.
- La cuenta activa debe pertenecer a la persona que delega la acción. Esa persona debe ser un integrante con permiso de escritura distinto del autor del PR. El asistente que escribió o modificó el PR no puede aprobarlo ni fusionarlo bajo otra identidad.
- Para **aprobar**, comprueba la identidad del colaborador, el autor y el último commit. Verifica el cambio, registra en GitHub el alcance y los resultados de la revisión y emite la aprobación si se cumplen los criterios y se resolvieron los hallazgos bloqueantes.
- Para **fusionar**, verifica que la autorización incluya esa acción, que el commit actual coincida con el aprobado y que las comprobaciones exigidas estén correctas. Si cambió el PR o fallan los permisos, reporta el bloqueo y detén la operación.

### Fusión y publicación

- Integra mediante **squash** con aprobación vigente del otro integrante, controles requeridos aprobados, conversaciones resueltas y sin solicitudes de cambio activas. Comprueba el commit antes de ejecutar la fusión.
- Respeta las protecciones de GitHub. Las acciones administrativas, los cambios de reglas, la fusión automática, el `force push` y el borrado de `main` quedan fuera del flujo de integración.
- Después de fusionar, registra la evidencia y actualiza el estado de la tarjeta. Comprueba qué dependencias quedaron desbloqueadas y mueve a **Ready** las tarjetas que ya no tengan dependencias abiertas.
- Publica el tag de entrega sobre el commit integrado y verificado, una vez cumplidos los criterios de calidad de #7 y autorizada la publicación. Una etiqueta por entrega.
