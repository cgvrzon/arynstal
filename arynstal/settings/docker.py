"""
===============================================================================
ARCHIVO: arynstal/settings/docker.py
PROYECTO: Arynstal - Sistema CRM para gestion de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCION:
    Configuracion de Django para el entorno de DESARROLLO en Docker.
    Hereda de production.py para obtener la misma infraestructura
    (PostgreSQL, estructura de settings) pero desactiva las restricciones
    de seguridad que requieren HTTPS.

POR QUE EXISTE ESTE ARCHIVO:
    - development.py usa SQLite -> no replica produccion
    - production.py usa PostgreSQL pero requiere HTTPS -> no funciona en local
    - docker.py = PostgreSQL de produccion + comportamiento de desarrollo

    Es el patron estandar en equipos profesionales: un settings por entorno.

DIFERENCIAS CON PRODUCTION:
    - DEBUG = True (tracebacks detallados + autoreload del dev server)
    - Sin SSL redirect (no hay certificado en local)
    - Cookies no requieren HTTPS (login y CSRF funcionan por HTTP)
    - Sin HSTS (evita que el navegador fuerce HTTPS en localhost)
    - Sin CSP middleware (simplifica debugging)
    - Email por consola (no necesita SMTP configurado)
    - Sin Sentry (errores se ven en la terminal, no en dashboard externo)

USO:
    export DJANGO_ENV=docker
    # o en .env.docker:
    DJANGO_ENV=docker

===============================================================================
"""

from .production import *  # noqa: F401, F403

# =============================================================================
# DEBUG MODE — Activar para desarrollo
# =============================================================================

DEBUG = True
# En Docker dev queremos:
#   - Tracebacks detallados en el navegador
#   - Autoreload del servidor de desarrollo (runserver)
#   - Django Debug Toolbar (si se instala en el futuro)


# =============================================================================
# SEGURIDAD — Desactivar restricciones HTTPS para entorno local
# =============================================================================
# En local no hay certificado SSL. Estas flags asumen HTTPS y rompen
# el entorno si no se desactivan:

SECURE_SSL_REDIRECT = False
# Sin esto: loop infinito de redirecciones HTTP -> HTTPS -> HTTP -> ...

SESSION_COOKIE_SECURE = False
# Sin esto: la cookie de sesion no se envia por HTTP -> login roto

CSRF_COOKIE_SECURE = False
# Sin esto: el token CSRF no se envia por HTTP -> formularios rotos (403)

SECURE_HSTS_SECONDS = 0
# Sin esto: el navegador recuerda "usar HTTPS para localhost" durante 1 anio

SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


# =============================================================================
# CSP — Desactivar en desarrollo
# =============================================================================
# El middleware CSP de produccion puede bloquear recursos en desarrollo
# si las rutas difieren. Lo eliminamos para simplificar debugging.

MIDDLEWARE = [m for m in MIDDLEWARE if m != 'csp.middleware.CSPMiddleware']


# =============================================================================
# EMAIL — Backend de consola (sin SMTP)
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Los emails se imprimen en la terminal del contenedor.
# Util para ver notificaciones de leads sin configurar Brevo.


# =============================================================================
# SENTRY — Desactivar en desarrollo
# =============================================================================
# No queremos enviar errores de desarrollo al dashboard de produccion.
# Sentry se inicializa en production.py solo si SENTRY_DSN existe,
# pero lo hacemos explicito aqui para claridad.

SENTRY_DSN = None


# =============================================================================
# CELERY — Activo con Redis (docker-compose levanta el contenedor Redis)
# =============================================================================
# Docker es el ÚNICO entorno donde Celery funciona con Redis real.
# production.py y development.py usan ALWAYS_EAGER (ejecución síncrona).

CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False


# =============================================================================
# LOGGING — Consola en vez de archivo
# =============================================================================
# En Docker, los logs deben ir a stdout/stderr para que
# `docker compose logs` los capture correctamente.

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
