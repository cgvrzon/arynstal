#!/bin/bash
# =============================================================================
# Wrapper para ejecutar manage.py con variables de entorno de produccion.
#
# Uso:
#   sudo /var/www/arynstal/app/scripts/manage_prod.sh migrate
#   sudo /var/www/arynstal/app/scripts/manage_prod.sh collectstatic --noinput
#   sudo /var/www/arynstal/app/scripts/manage_prod.sh showmigrations
#
# Este script garantiza que manage.py SIEMPRE corre con las variables
# de produccion, independientemente de como se invoque (manual, CI/CD, cron).
# =============================================================================

set -euo pipefail

APP_DIR="/var/www/arynstal/app"
ENV_FILE="${APP_DIR}/.env"
PYTHON="${APP_DIR}/venv/bin/python"
MANAGE="${APP_DIR}/manage.py"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: No se encontro ${ENV_FILE}" >&2
    exit 1
fi

# Cargar todas las variables de entorno de produccion
set -a && source "$ENV_FILE" && set +a

exec "$PYTHON" "$MANAGE" "$@"
