# AD-DelitosBog

Proyecto de Analítica de Datos de Ingeniería de Sistemas, Pontificia Universidad Javeriana. Sara Albarracín y Juan Diego Rojas.

¿Cuánto mejora el pronóstico de hurtos registrados para el día siguiente en Bogotá al usar calendario y rezagos frente a repetir el conteo del mismo día de la semana anterior? La comparación se hará sobre las mismas fechas de evaluación. La variable objetivo es el número diario de víctimas de hurto a personas registradas por la Policía en Bogotá entre 2020 y 2025 (D-01, [docs/decisiones.md](docs/decisiones.md)). Como pregunta complementaria, se describe la distribución de las llamadas de hurto a la Línea 123 entre localidades.

El proyecto usa tres fuentes de delito, descritas en [data/README.md](data/README.md):
- **Policía, registro:** una fila por víctima. Es la fuente principal y la base de la variable objetivo. El agregado diario de MinDefensa solo cubre 2018–2019 como contexto.
- **Fiscalía:** procesos por hurto en todas sus modalidades, una fila por proceso–delito. Es complementaria.
- **Línea 123:** llamadas tramitadas. Es complementaria. Las tres tienen unidades de observación distintas y no se suman entre sí.

## Reproducción

1. Desde la raíz del repositorio, instale las dependencias en un entorno de Python 3. En Colab, abra el notebook, haga accesible el repositorio y use su raíz como directorio de trabajo. Puede instalar las dependencias allí con `%pip install "pandas>=2" matplotlib geopandas scikit-learn`.

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install "pandas>=2" matplotlib geopandas scikit-learn jupyter
   ```

2. Reutilice las descargas locales o siga [las instrucciones de descarga](data/README.md).
3. Ejecute todas las celdas de [01 · Preprocesamiento](notebooks/01_preprocesamiento.ipynb) y después las de [02 · Análisis exploratorio](notebooks/02_analisis_exploratorio.ipynb). Las tablas y figuras se guardan en `data/processed/`.
4. Consulte [la segunda entrega](docs/segunda_entrega.md) para ver la auditoría, los hallazgos y el protocolo de evaluación de la tercera entrega.

Python y pandas permiten reproducir la limpieza, construir atributos y calcular estadística descriptiva. Matplotlib genera las gráficas, GeoPandas maneja las geometrías distritales y scikit-learn se usará para la regresión lineal, el árbol y la evaluación cronológica.
