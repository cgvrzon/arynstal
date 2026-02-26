#!/bin/bash

# =============================================================================
# entrypoint.sh — Script de inicializacion del contenedor Django
# =============================================================================
#
# Este script se ejecuta CADA VEZ que el contenedor arranca.
# Su funcion es asegurar que todo esta listo antes de lanzar Django:
#
#   1. Esperar a que PostgreSQL acepte conexiones
#   2. Ejecutar migraciones pendientes
#   3. Recopilar archivos estaticos
#   4. Lanzar el comando principal (runserver o gunicorn)
#
# USO:
#   Como ENTRYPOINT en Dockerfile — recibe CMD como argumento ($@)
#   Ejemplo: entrypoint.sh python manage.py runserver 0.0.0.0:8000
#
# =============================================================================

set -e
# set -e: Salir inmediatamente si cualquier comando falla.
# Sin esto, el script continuaria ejecutando comandos aunque
# la migracion o collectstatic fallaran.

# ─── Paso 1: Esperar a PostgreSQL ────────────────────────────────────────────
# depends_on en docker-compose solo espera a que el CONTENEDOR arranque,
# no a que PostgreSQL este listo para aceptar conexiones (puede tardar 2-5s).
# Sin esta espera, Django intentaria conectarse y fallaria con:
#   "connection refused" o "the database system is starting up"

echo "Esperando a PostgreSQL en ${DB_HOST}:${DB_PORT}..."

while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${DB_HOST}', int('${DB_PORT}')))
    s.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
    echo "  PostgreSQL no disponible, reintentando en 1s..."
    sleep 1
done

echo "PostgreSQL disponible."

# ─── Paso 1b: Esperar a Redis (si Celery esta configurado) ────────────────
# Solo espera si CELERY_BROKER_URL esta definido (worker, beat, flower, web)
if [ -n "$CELERY_BROKER_URL" ]; then
    # Extraer host y puerto de la URL redis://host:port/db
    REDIS_HOST=$(echo "$CELERY_BROKER_URL" | sed -E 's|redis://([^:]+):([0-9]+).*|\1|')
    REDIS_PORT=$(echo "$CELERY_BROKER_URL" | sed -E 's|redis://([^:]+):([0-9]+).*|\2|')

    echo "Esperando a Redis en ${REDIS_HOST}:${REDIS_PORT}..."

    while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${REDIS_HOST}', int('${REDIS_PORT}')))
    s.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
        echo "  Redis no disponible, reintentando en 1s..."
        sleep 1
    done

    echo "Redis disponible."
fi

# ─── Paso 2: Migraciones ────────────────────────────────────────────────────
# Ejecutar migraciones pendientes automaticamente.
# En desarrollo esto es comodo: cambias un modelo, reinicias el contenedor,
# y las migraciones se aplican solas.

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# ─── Paso 3: Archivos estaticos ─────────────────────────────────────────────
# Recopilar archivos estaticos en STATIC_ROOT.
# Necesario para que WhiteNoise o el servidor los sirva correctamente.

echo "Recopilando archivos estaticos..."
python manage.py collectstatic --noinput

# ─── Paso 4: Lanzar comando principal ───────────────────────────────────────
# exec reemplaza este proceso bash por el comando de Django.
# Sin exec, el script bash quedaria como proceso padre y Django como hijo.
# Con exec, Django ES el proceso principal del contenedor (PID 1).
# Esto es importante para que Docker pueda enviar signals (SIGTERM) correctamente.

echo "Lanzando: $@"
exec "$@"
