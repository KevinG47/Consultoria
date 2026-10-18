# syntax=docker/dockerfile:1
#
# Imagen del proyecto: valida las 17 reglas del sistema de memoria
# (`python -m memoria validar`) sin instalar nada en la maquina.
#
# Construccion en dos etapas:
#   1. builder  — resuelve las dependencias con Poetry y las deja en un
#                 requirements.txt. Aqui queda Poetry y las herramientas; NADA
#                 de esto pasa a la imagen final.
#   2. runtime  — instala solo ese requirements.txt con pip, copia el codigo y
#                 ejecuta como usuario sin privilegios.
#
# Lo que NO se instala a proposito: torch, sentence-transformers y pyvis. Estan
# en el grupo opcional `ml` de pyproject.toml y solo hacen falta para
# RECONSTRUIR el RAG o el grafo; el indice (150 fragmentos) y los dashboards ya
# estan versionados como HTML estatico. `--only main` es lo que los deja fuera.

# ---------------------------------------------------------------------------
# ETAPA 1 — dependencias
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /build

# Poetry 2.x ya NO incluye `poetry export`: vive en un plugin aparte y sin el el
# comando responde "The requested command export does not exist".
# Compatibilidad comprobada: poetry-plugin-export 1.10.1 declara
# `poetry>=2.1.0,<3.0.0`, asi que funciona con el 2.5.x que instala esta linea.
RUN pip install --no-cache-dir "poetry>=2.0,<3.0" poetry-plugin-export

COPY pyproject.toml poetry.lock ./

# `--only main` deja fuera los grupos opcionales (ml, dev).
# `--without-hashes` evita el formato con hashes, que pip acepta igual.
#
# El resultado son 29 paquetes (~730 bytes de requirements.txt), frente a los 158
# del lock de repo_mejorado/, que si arrastraba el navegador.
#
# SI EL PLUGIN DIERA PROBLEMAS EN TU EQUIPO, esta es la alternativa equivalente
# (no necesita `export`, instala el grupo main en un venv de la etapa 1):
#   RUN python -m venv /opt/venv
#   RUN /opt/venv/bin/pip install --no-cache-dir poetry poetry-plugin-export
#   RUN /opt/venv/bin/poetry install --only main --no-root --no-directory
# y en la etapa 2:  COPY --from=builder /opt/venv /opt/venv  +  ENV PATH="/opt/venv/bin:$PATH"
RUN poetry export \
        --only main \
        --format requirements.txt \
        --output requirements.txt \
        --without-hashes

# ---------------------------------------------------------------------------
# ETAPA 2 — ejecucion
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # matplotlib sin pantalla: aqui no hay display
    MPLBACKEND=Agg

COPY --from=builder /build/requirements.txt /tmp/requirements.txt

# Solo dependencias de ejecucion: no hay Poetry ni compiladores en la imagen.
# Si alguna rueda no existiera para linux/cp311, este paso es el que fallaria
# (ver el informe de entrega).
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# Usuario sin privilegios. El UID es fijo para que el montaje de docker-compose
# tenga un dueno predecible.
RUN useradd --create-home --shell /usr/sbin/nologin --uid 10001 appuser

WORKDIR /app

# El .dockerignore deja fuera .git, .venv, __pycache__, node_modules, el clon
# antiguo del repositorio (441 MB), _archivo/ (145 MB), 04_auditoria/, y el CSV
# de 31 MB que se monta por volumen.
COPY --chown=appuser:appuser . /app

# GUARDIA DEL CONTEXTO. Si a la imagen le falta -o le llega vacio- algun archivo
# que las reglas leen, el BUILD falla aqui, diciendo cual. Sin este paso el build
# "funcionaba" y la imagen arrancaba dando 13 PASA / 2 FALLA (R14 y R17) sin
# explicar por que: paso con documentacion_auditoria/data/ejecucion_resumen.csv,
# que llego vacio porque en Windows era un archivo en la nube de OneDrive y
# Docker Desktop no lo pudo leer. R14 compara la cifra de scripts de los .tex
# contra ese archivo; sin el, una de sus siete comprobaciones falla (6/7).
RUN python /app/verificar_contexto_imagen.py

USER appuser

# `python -m memoria validar` necesita que el directorio de trabajo sea este:
# el paquete `memoria` vive en documentacion_auditoria/src.
WORKDIR /app/documentacion_auditoria/src

# Devuelve 1 si alguna regla FALLA y 0 si el conjunto queda en PASA/ADVERTENCIA.
# Estado esperado: R1-R17 con 15 PASA, 0 FALLA y 2 ADVERTENCIA (R12 y R15).
CMD ["python", "-m", "memoria", "validar"]
