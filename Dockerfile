# =============================================================================
# Dockerfile — Imagen Docker para Arynstal (Django CRM)
# =============================================================================
#
# Multi-stage build:
#   Stage 1 (builder): Instalar dependencias del sistema y Python
#   Stage 2 (runtime): Copiar solo lo necesario para ejecutar la app
#
# Resultado: imagen final sin gcc, sin cache de pip, ~200-300 MB
# vs imagen single-stage que pesaria ~500-800 MB
#
# USO:
#   docker build -t arynstal .
#   docker compose up --build
#
# =============================================================================


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ STAGE 1: BUILDER — Instalar dependencias                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

FROM python:3.12-slim AS builder
# python:3.12-slim: Debian minimo con Python 3.12 (~150 MB)
# "AS builder": Nombre este stage para referenciarlo despues

# Variables de entorno para Python en Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# PYTHONDONTWRITEBYTECODE: No crear archivos .pyc (imagen mas limpia)
# PYTHONUNBUFFERED: Output directo a stdout (logs visibles en tiempo real)

WORKDIR /app

# Dependencias del sistema necesarias para compilar paquetes Python
# - gcc: Compilador C (necesario para psycopg2 y Pillow)
# - libpq-dev: Headers de PostgreSQL (para psycopg2)
# - libjpeg-dev, zlib1g-dev: Para Pillow (procesamiento de imagenes)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
# --no-install-recommends: No instalar paquetes sugeridos (menor tamano)
# rm -rf /var/lib/apt/lists/*: Limpiar cache de apt (menor tamano de capa)

# Copiar DIRECTORIO requirements completo (production.txt importa base.txt con -r)
# Se copia antes que el resto del codigo para optimizar cache de capas:
# si el codigo cambia pero requirements no, esta capa se reutiliza
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt \
    && pip install --no-cache-dir -r requirements/development.txt
# Instalamos ambos: production (psycopg2, gunicorn) + development (pytest, black)
# En un entorno profesional se usarian targets separados en el Dockerfile,
# pero para desarrollo local es mas practico tener todo disponible


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ STAGE 2: RUNTIME — Solo lo necesario para ejecutar                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

FROM python:3.12-slim AS runtime
# Imagen fresca: NO tiene gcc, ni cache de pip, ni headers de desarrollo

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencia de runtime para PostgreSQL (sin headers de desarrollo)
# libpq5 es la libreria cliente, libpq-dev son los headers para compilar
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes Python instalados desde el builder
# Solo copiamos los site-packages (librerias) y binarios (gunicorn, etc.)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Crear usuario sin privilegios (seguridad)
# Si el contenedor es comprometido, el atacante no tiene root
RUN addgroup --system app \
    && adduser --system --ingroup app app

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /app/logs /app/staticfiles /app/media \
    && chown -R app:app /app

# Copiar codigo de la aplicacion
COPY --chown=app:app . .

# Copiar y dar permisos al entrypoint
COPY --chown=app:app entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Cambiar al usuario sin privilegios
USER app

# Documentar el puerto que usa la app
EXPOSE 8000

# Script de inicializacion (espera BD, migra, collectstatic)
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto: Gunicorn para produccion
# En docker-compose.yml se sobreescribe con runserver para desarrollo
CMD ["gunicorn", "arynstal.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
