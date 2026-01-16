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
    - DEFAULT_FROM_EMAIL: Remitente (default: 'info@arynstal.es')
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

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'info@arynstal.es')
# Remitente por defecto para todos los emails del sistema.


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
