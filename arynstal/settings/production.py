"""
===============================================================================
ARCHIVO: arynstal/settings/production.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configuración de Django para el entorno de PRODUCCIÓN.
    Hereda de base.py y sobrescribe valores específicos para el servidor.

CARACTERÍSTICAS DE PRODUCCIÓN:
    - DEBUG = False (oculta errores detallados)
    - PostgreSQL como base de datos
    - SMTP real para envío de emails
    - Headers de seguridad activados (HTTPS, HSTS, etc.)
    - Todas las credenciales vienen de variables de entorno

VARIABLES DE ENTORNO REQUERIDAS:
    OBLIGATORIAS:
    - SECRET_KEY: Clave secreta única para producción
    - ALLOWED_HOSTS: Dominios permitidos (ej: "arynstal.es,www.arynstal.es")
    - DB_PASSWORD: Contraseña de la base de datos

    OPCIONALES (tienen valores por defecto):
    - DB_NAME: Nombre de la BD (default: 'arynstal')
    - DB_USER: Usuario de la BD (default: 'arynstal_user')
    - DB_HOST: Host de la BD (default: 'localhost')
    - DB_PORT: Puerto de la BD (default: '5432')
    - EMAIL_HOST: Servidor SMTP (default: 'smtp.gmail.com')
    - EMAIL_PORT: Puerto SMTP (default: '587')
    - EMAIL_HOST_USER: Usuario SMTP
    - EMAIL_HOST_PASSWORD: Contraseña SMTP
    - DEFAULT_FROM_EMAIL: Remitente (default: 'Arynstal <noreply@arynstal.es>')
    - LEAD_NOTIFICATION_EMAIL: Email para notificaciones de leads

DESPLIEGUE:
    Ver docs/DEPLOY_GUIDE.md para instrucciones detalladas de configuración.

===============================================================================
"""

from .base import *
import os


# =============================================================================
# DEBUG MODE
# =============================================================================

DEBUG = False
# NUNCA activar DEBUG en producción:
# - Expondría información sensible (rutas, código, variables)
# - Permite ataques basados en mensajes de error
# - Consume más memoria (Django guarda todas las queries SQL)


# =============================================================================
# SECRET KEY
# =============================================================================

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY environment variable must be set in production')
# La SECRET_KEY debe ser:
# - Única para cada instalación
# - Al menos 50 caracteres aleatorios
# - NUNCA commiteada al repositorio
# - Generarla con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"


# =============================================================================
# ALLOWED HOSTS
# =============================================================================

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
# Lista de dominios que pueden servir esta aplicación.
# Formato en variable de entorno: "arynstal.es,www.arynstal.es"
# Sin esto, Django rechaza todas las peticiones (error 400).


# =============================================================================
# CSRF TRUSTED ORIGINS
# =============================================================================

CSRF_TRUSTED_ORIGINS = [
    f'https://{host.strip()}' for host in
    os.environ.get('CSRF_TRUSTED_ORIGINS', 'arynstal.es,www.arynstal.es').split(',')
]
# Orígenes confiables para peticiones CSRF.
# Necesario cuando Django está detrás de proxy (Cloudflare → Nginx → Gunicorn).
# Sin esto, los formularios POST fallan con error 403 CSRF.


# =============================================================================
# DATABASE - PostgreSQL para producción
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # PostgreSQL: Base de datos robusta para producción.
        # Ventajas sobre SQLite: concurrencia, escalabilidad, backups.

        'NAME': os.environ.get('DB_NAME', 'arynstal'),
        # Nombre de la base de datos

        'USER': os.environ.get('DB_USER', 'arynstal_user'),
        # Usuario de la base de datos (NO usar root/postgres)

        'PASSWORD': os.environ.get('DB_PASSWORD'),
        # Contraseña (OBLIGATORIA en producción)

        'HOST': os.environ.get('DB_HOST', 'localhost'),
        # Host del servidor PostgreSQL

        'PORT': os.environ.get('DB_PORT', '5432'),
        # Puerto (5432 es el estándar de PostgreSQL)
    }
}


# =============================================================================
# EMAIL BACKEND - SMTP real para producción
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Usa servidor SMTP real para enviar emails.

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
# Servidor SMTP. Gmail requiere App Password (no contraseña normal).

EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
# Puerto SMTP. 587 para TLS (recomendado), 465 para SSL.

EMAIL_USE_TLS = True
# Usar TLS (Transport Layer Security) para cifrar la conexión.

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# Usuario SMTP (normalmente un email completo).

EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# Contraseña SMTP. Para Gmail, usar App Password de 2FA.

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Arynstal <noreply@arynstal.es>')
# Remitente por defecto para emails automáticos del sistema (via Brevo).
# Usa noreply@ porque los emails transaccionales no deben recibir respuestas.
# El email de contacto público (info@) se gestiona con Zoho Mail.


# =============================================================================
# NOTIFICATIONS - Override con variable de entorno
# =============================================================================

NOTIFICATIONS = {
    'LEAD': {
        'ENABLED': True,
        'ADMIN_EMAIL': os.environ.get('LEAD_NOTIFICATION_EMAIL', 'garzoncl01@gmail.com'),
        # Email que recibe notificaciones de nuevos leads.
        # Configurable via variable de entorno para facilitar cambios.
        'SEND_CUSTOMER_CONFIRMATION': True,
    },
}


# =============================================================================
# SECURITY SETTINGS - Headers de seguridad
# =============================================================================
# Configuraciones de seguridad obligatorias para producción.
# Protegen contra ataques comunes (XSS, clickjacking, MITM, etc.)

# -------------------------------------------------------------------------
# HTTPS
# -------------------------------------------------------------------------

SECURE_SSL_REDIRECT = True
# Redirige automáticamente HTTP → HTTPS.
# Requiere certificado SSL configurado en el servidor.

SESSION_COOKIE_SECURE = True
# Las cookies de sesión solo se envían por HTTPS.
# Previene robo de sesión en redes no seguras.

CSRF_COOKIE_SECURE = True
# El token CSRF solo se envía por HTTPS.
# Previene ataques CSRF en redes no seguras.

# -------------------------------------------------------------------------
# HSTS (HTTP Strict Transport Security)
# -------------------------------------------------------------------------

SECURE_HSTS_SECONDS = 31536000  # 1 año
# Indica al navegador que SIEMPRE use HTTPS para este dominio.
# El navegador recuerda esto durante 1 año.

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# HSTS también aplica a subdominios (api.arynstal.es, etc.)

SECURE_HSTS_PRELOAD = True
# Permite incluir el dominio en la lista HSTS preload de navegadores.
# Ver: https://hstspreload.org/

# -------------------------------------------------------------------------
# Otros headers de seguridad
# -------------------------------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
# Añade header: X-Content-Type-Options: nosniff
# Previene que el navegador "adivine" el tipo MIME.

SECURE_BROWSER_XSS_FILTER = True
# Añade header: X-XSS-Protection: 1; mode=block
# Activa el filtro XSS del navegador (obsoleto pero no daña).

X_FRAME_OPTIONS = 'DENY'
# Añade header: X-Frame-Options: DENY
# Previene que la página se muestre en iframes (clickjacking).


# =============================================================================
# STATIC FILES - Producción
# =============================================================================

STATIC_ROOT = BASE_DIR / 'staticfiles'
# Directorio donde 'python manage.py collectstatic' reúne
# todos los archivos estáticos.
# Nginx sirve este directorio directamente (no pasa por Django).


# =============================================================================
# LOGGING - Registro de errores
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # No deshabilitar loggers existentes de Django

    'handlers': {
        'file': {
            'level': 'ERROR',
            # Solo registrar errores (no warnings ni info)

            'class': 'logging.FileHandler',
            # Escribir a archivo

            'filename': BASE_DIR / 'logs' / 'django_errors.log',
            # Ubicación del archivo de log
            # IMPORTANTE: Crear el directorio 'logs/' antes de desplegar
        },
    },

    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
            # Registrar todos los errores de Django
        },
    },
}
# NOTA: Crear directorio logs/ con:
#   mkdir -p /ruta/al/proyecto/logs
#   chown www-data:www-data /ruta/al/proyecto/logs


# =============================================================================
# SENTRY - Monitoreo de errores
# =============================================================================
# Sentry captura errores en producción y los envía a un dashboard centralizado.
# Configurar SENTRY_DSN en las variables de entorno.
#
# Para obtener el DSN:
#   1. Crear cuenta en https://sentry.io
#   2. Crear proyecto Django
#   3. Copiar el DSN del proyecto
#
# El DSN tiene formato: https://xxx@yyy.ingest.sentry.io/zzz

SENTRY_DSN = os.environ.get('SENTRY_DSN')

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,

        # Integraciones
        integrations=[
            DjangoIntegration(
                # Capturar todas las transacciones
                transaction_style="url",
                # Middleware para medir performance
                middleware_spans=True,
            ),
            LoggingIntegration(
                # Capturar logs de nivel WARNING y superior
                level=None,
                event_level=None,
            ),
        ],

        # Porcentaje de transacciones para performance monitoring (0.0 a 1.0)
        # 0.1 = 10% de las peticiones se monitorizan para performance
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),

        # Porcentaje de sesiones para monitorear (crash-free sessions)
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),

        # Enviar datos de usuario (IP, email) con los errores
        # Útil para debugging, pero considerar privacidad
        send_default_pii=False,

        # Entorno (production, staging, etc.)
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),

        # Release/versión para tracking de deploys
        # release=os.environ.get('SENTRY_RELEASE', 'arynstal@1.0.0'),
    )


# =============================================================================
# WHITENOISE - Archivos estáticos sin Nginx
# =============================================================================
# Whitenoise sirve archivos estáticos directamente desde Django.
# Útil para deployments simples sin configurar Nginx para static.
#
# Para habilitar:
#   1. Añadir al MIDDLEWARE después de SecurityMiddleware
#   2. Ejecutar collectstatic

# Descomentar si quieres usar Whitenoise en lugar de Nginx para static:
# MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# =============================================================================
# CSP - Content Security Policy
# =============================================================================
# CSP previene ataques XSS controlando qué recursos puede cargar la página.
# Cada directiva especifica qué orígenes están permitidos para ese tipo de recurso.
#
# Documentación: https://django-csp.readthedocs.io/
# Referencia CSP: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP

# Añadir middleware de CSP
MIDDLEWARE += ['csp.middleware.CSPMiddleware']

# -------------------------------------------------------------------------
# Directivas CSP
# -------------------------------------------------------------------------

# default-src: Fallback para directivas no especificadas
CSP_DEFAULT_SRC = ("'self'",)

# script-src: Scripts JavaScript
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Necesario para scripts inline en templates
    # Añadir CDNs si los usas:
    # "https://cdn.jsdelivr.net",
    # "https://cdnjs.cloudflare.com",
)

# style-src: Hojas de estilo CSS
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Necesario para Tailwind inline styles
    # Añadir fuentes de Google si las usas:
    # "https://fonts.googleapis.com",
)

# img-src: Imágenes
CSP_IMG_SRC = (
    "'self'",
    "data:",  # Para imágenes base64
    "blob:",  # Para previews de imágenes
)

# font-src: Fuentes
CSP_FONT_SRC = (
    "'self'",
    # "https://fonts.gstatic.com",  # Google Fonts
)

# connect-src: Conexiones (fetch, WebSocket, etc.)
CSP_CONNECT_SRC = (
    "'self'",
    # Añadir Sentry si lo usas:
    # "https://*.ingest.sentry.io",
)

# frame-src: Iframes
CSP_FRAME_SRC = (
    "'none'",  # No permitir iframes
)

# object-src: Plugins (Flash, Java, etc.)
CSP_OBJECT_SRC = ("'none'",)

# base-uri: Restricción de <base> tag
CSP_BASE_URI = ("'self'",)

# form-action: Destinos de formularios
CSP_FORM_ACTION = ("'self'",)

# frame-ancestors: Quién puede embeber esta página en iframe
CSP_FRAME_ANCESTORS = ("'none'",)

# -------------------------------------------------------------------------
# Opciones adicionales
# -------------------------------------------------------------------------

# Reportar violaciones CSP (útil para debugging)
# CSP_REPORT_URI = "/csp-report/"

# Usar Report-Only para testear sin bloquear
# Cambiar a False cuando estés seguro de que funciona
CSP_REPORT_ONLY = os.environ.get('CSP_REPORT_ONLY', 'False').lower() == 'true'

# Incluir header Upgrade-Insecure-Requests
CSP_UPGRADE_INSECURE_REQUESTS = True
