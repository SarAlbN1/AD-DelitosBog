# Entorno de referencia para las cifras de modelado del informe (#46, #54).
#
# Fija el sistema, Python y las versiones exactas de requirements-lock.txt, para que las cifras
# no dependan de la máquina (ver «Entorno de referencia» en docs/REPRODUCIBILIDAD.md).
# La imagen no contiene datos ni código: el repositorio se monta en /repo al ejecutar.
#
#   docker build -t ad-delitosbog:referencia .
#   docker run --rm -v "<ruta del repo>:/repo" ad-delitosbog:referencia python -m pytest -q tests
FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    OMP_NUM_THREADS=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AD_ENTORNO=referencia-docker-py3.12.8

# libgomp1: OpenMP que usan HistGradientBoosting y XGBoost.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-lock.txt /tmp/requirements-lock.txt
RUN pip install -r /tmp/requirements-lock.txt

WORKDIR /repo
