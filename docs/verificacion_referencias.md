# Verificación de referencias (issue #24)

Fecha de consulta: **2026-11-11**. Cada referencia de `Informe/primera_entrega.tex` se comparó con su fuente primaria: un registro del repositorio institucional, el PDF del documento, Crossref (DOI) u Open Library (libros).

**Resultado:** las 8 referencias existen y son pertinentes; 7 de ellas son estudios académicos. Se corrigieron dos datos y queda una duda abierta.

| Clave | Referencia | Cómo se verificó | Título, autoría y año | ¿Coincide la descripción del informe? | Estado |
|---|---|---|---|---|---|
| `campo2017` | Campo Agredo (2017), trabajo de grado de pregrado, Universidad de los Andes | API DSpace del repositorio Uniandes (`dc.title`, `dc.contributor.author`, `dc.date.issued`, `dc.type`); handle `1992/50785` | Sí. El título oficial termina «…en **base** de datos» y no «…bases de datos» | Sí: el resumen trata la predicción del hurto a personas con algoritmos sobre bases de datos | ✅ Corregido (título y enlace persistente) |
| `fonseca2019` | Fonseca Vásquez (2019), Especialización en Geomática, UMNG | Portada del PDF (11 de junio de 2019) | Sí | Sí: análisis espacial en Los Mártires 2017–2018 para decisiones de los CAI | ✅ |
| `garzon2025` | Garzón Acosta (2025), Especialización en Estadística Aplicada, Fundación Universitaria Los Libertadores | PDF (artículo de 7 páginas, «Aceptado: mayo 08, 2025») | Sí | Sí: MCE frente a VECM, 2015–2024, ADF, causalidad de Granger, IPC, desempleo y capturas | ✅ |
| `martinez2025` | Martínez Chitiva (2025), Maestría en Tecnología de la Información Geográfica, Universidad de Manizales | Registro del repositorio RIDUM (handle `20.500.12746/7648`) | Sí. El tipo «tesis de maestría» se deduce de la colección; el registro no tiene un campo de tipo | Sí: modelo espacio-temporal; **Random Forest supera a los métodos estadísticos**; datos hasta 2020 | ✅ |
| `riascos2020` | Riascos, Dulce, Moreno y Gómez (2020), *Prediciendo el crimen en Bogotá*, Nota de Política, Universidad de los Andes | PDF: autores, «Octubre 2020», ISSN 2027-7199 | Sí | Sí: despliegue policial, cámaras y ubicación de CAI; sesgo y subregistro | ✅ **Número 38 confirmado** en el [listado oficial](https://gobierno.uniandes.edu.co/es/publicaciones/notas-de-politica) («Nota de política No. 38»). El «34» de los metadatos del PDF es el título del archivo de Illustrator; la portada no imprime el número |
| `urcuqui2020` | Urcuqui, Moreno, Montenegro, Riascos y Dulce (2020), IEEE BESC 2020, pp. 1–6 | Crossref | Sí | Sí: GAN condicional, exactitud y equidad | ✅ Se añadió el DOI `10.1109/BESC51023.2020.9348315` (antes había una URL personal) |
| `riascos2023` | Riascos Villegas, Ñungo, Gómez Tobón, Dulce Rubio y Gómez (2023), *PLOS ONE, 18*(7), e0287776 | Crossref (DOI `10.1371/journal.pone.0287776`) | Sí | Sí: modelado espacio-temporal con subregistro | ✅ |
| `provost2013` | Provost y Fawcett (2013), *Data science for business*, O'Reilly Media | Open Library (ISBN 9781449361327) | Sí | Sí: referencia metodológica general | ✅ |

## Pendientes
- [x] Confirmar el número de la nota de política de Riascos et al. (34 o 38) en el listado de notas de política de la Escuela de Gobierno Alberto Lleras Camargo.
- [ ] Martínez Chitiva (2025): leer el PDF para extraer las fuentes de datos y los modelos comparados, que la matriz del #25 necesita.
- [ ] Las referencias de los datasets (Línea 123, Policía y Fiscalía) llevan «(s. f.)». En APA 7 deben incluir la fecha de consulta; esto se aborda en el #26.
