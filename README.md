# AD-DelitosBog

Proyecto de Analítica de Datos de Ingeniería de Sistemas, Pontificia Universidad Javeriana. Sara Albarracín y Juan Diego Rojas.

¿Cuánto mejora el pronóstico de hurtos registrados para el día siguiente en Bogotá al usar calendario y rezagos frente a repetir el conteo del mismo día de la semana anterior? La comparación se hace sobre las mismas fechas de evaluación. La variable objetivo es el número diario de víctimas de hurto a personas registradas por la Policía en Bogotá entre 2020 y 2025 (D-01, [docs/decisiones.md](docs/decisiones.md)). Como pregunta complementaria, se describe la distribución de las llamadas de hurto a la Línea 123 entre localidades.

El proyecto usa tres fuentes de delito, descritas en [data/README.md](data/README.md):
- **Policía, registro:** una fila por víctima. Es la fuente principal y la base de la variable objetivo. El agregado diario de MinDefensa solo cubre 2018–2019 como contexto.
- **Fiscalía:** procesos por hurto en todas sus modalidades, una fila por proceso–delito. Es complementaria.
- **Línea 123:** llamadas tramitadas. Es complementaria.

Las tres tienen unidades de observación distintas y no se suman entre sí.

## Qué contiene

- **El informe** (`Informe/`), en LaTeX, con las secciones 1 a 11 y los apéndices A a D.
- **El tablero de Power BI** (`powerbi/Tablero-DelitosBOG.pbip`), que lee los CSV de `outputs/powerbi/`. Se documenta en [docs/POWERBI.md](docs/POWERBI.md).
- **El modelado** (`scripts/modelado/`): cinco familias evaluadas con el mismo protocolo contra cuatro comparadores triviales. Son SARIMA, ETS, bosque aleatorio, gradiente por histogramas y regresión lineal. El protocolo está en [docs/METODOLOGIA.md](docs/METODOLOGIA.md) y su implementación, en [docs/MODELADO.md](docs/MODELADO.md).
- **Las cifras** (`outputs/`): cada cifra del informe sale de un archivo de esa carpeta, producido por un script.

## Reproducción

La guía completa, con los dos modos (copia congelada o descarga nueva), las huellas SHA-256 y las cifras de control, es [docs/REPRODUCIBILIDAD.md](docs/REPRODUCIBILIDAD.md). En resumen:

1. Instale las dependencias en un entorno de Python 3 y compruebe el código:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   pytest -q tests
   ```

2. Obtenga las fuentes con [las instrucciones de descarga](data/README.md), o reutilice la copia congelada. Van en `data/raw/<fuente>/`.
3. Siga el orden de la guía: la auditoría (sección 4), el preprocesamiento, el análisis exploratorio y los comparadores (sección 5) y el modelado (sección 6).
4. **Las cifras de modelado del informe se generan en la imagen de Docker de referencia** (`Dockerfile` y `requirements-lock.txt`, sección 1.1 de la guía), porque algunos modelos no dan la misma cifra en todos los sistemas. `requirements.txt` es el entorno de desarrollo.

Los hallazgos están en [docs/AUDITORIA.md](docs/AUDITORIA.md) y [docs/EDA_HALLAZGOS.md](docs/EDA_HALLAZGOS.md).

Python y pandas reproducen la limpieza, construyen las variables y calculan la estadística descriptiva. Matplotlib genera las gráficas y GeoPandas maneja las geometrías distritales. scikit-learn y statsmodels ajustan los modelos, y Power BI Desktop abre el tablero.

## Estructura del repositorio

```
AD-DelitosBog/
├── CLAUDE.md, CONTRIBUTING.md   Reglas de trabajo del equipo
├── Dockerfile, requirements*.txt   Entorno de referencia y dependencias
├── config/          Manifiesto de fuentes de la auditoría y protocolo de modelado
├── data/
│   ├── raw/         Archivos originales, sin modificar. Ignorado por Git
│   └── processed/   Series y variables derivadas. Ignorado por Git
├── docs/            Auditoría, decisiones, diccionario, metodología, modelado, reproducción
├── Informe/         Informe académico en LaTeX
├── outputs/         Cifras del informe, una carpeta por etapa (auditoria, eda, modelado, powerbi...)
├── powerbi/         Tablero de Power BI (proyecto .pbip)
├── scripts/         Auditoría, descarga, preprocesamiento, EDA y exportación
│   └── modelado/    Arnés de evaluación y los modelos
└── tests/           Pruebas automáticas, con datos sintéticos
```

Dos reglas sobre qué entra en Git:

- **Los datos no se versionan.** `data/raw/` y `data/processed/` están en `.gitignore`, junto con
  las cachés, los entornos virtuales y los temporales. Los datos se reproducen con las instrucciones
  de [`data/README.md`](data/README.md).
- **La evidencia sí se versiona.** `outputs/` contiene las salidas de cada etapa, que son ligeras y
  sostienen las cifras del informe, así que se versionan para poder comparar entre ejecuciones.

Para comprobar que un archivo de datos queda excluido:

```sh
git check-ignore -v data/raw/ejemplo.csv
# .gitignore:3:/data/raw/	data/raw/ejemplo.csv
```
