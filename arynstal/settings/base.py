"""
===============================================================================
ARCHIVO: arynstal/settings/base.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configuración base de Django compartida entre todos los entornos.
    Define las configuraciones comunes que NO cambian entre desarrollo y
    producción: apps instaladas, middleware, templates, validadores, etc.

ARQUITECTURA DE SETTINGS:
    El proyecto usa un patrón de settings dividido en archivos:

    settings/
    ├── __init__.py      → Importa el entorno correcto
    ├── base.py          → Este archivo (configuración común)
    ├── development.py   → Configuración para desarrollo local
    └── production.py    → Configuración para servidor de producción

FLUJO DE CARGA:
    1. Django lee DJANGO_SETTINGS_MODULE (ej: arynstal.settings.development)
    2. development.py hace 'from .base import *' (hereda base)
    3. development.py sobrescribe valores específicos (DEBUG, SECRET_KEY, etc.)

SECCIONES EN ESTE ARCHIVO:
    1. PATHS: Rutas base del proyecto
    2. INSTALLED_APPS: Apps de Django y del proyecto
    3. MIDDLEWARE: Pipeline de procesamiento de requests
    4. TEMPLATES: Configuración del motor de templates
    5. PASSWORD_VALIDATORS: Reglas de contraseñas
    6. INTERNATIONALIZATION: Idioma y zona horaria
    7. STATIC FILES: Archivos CSS/JS/imágenes estáticas
    8. MEDIA FILES: Archivos subidos por usuarios
    9. UPLOAD LIMITS: Límites de seguridad para uploads
    10. FORM_SECURITY: Configuración anti-spam (rate limit, honeypot)
    11. NOTIFICATIONS: Configuración de emails automáticos
    12. COMPANY_INFO: Datos de la empresa para templates

===============================================================================
"""

from pathlib import Path


# =============================================================================
# 1. PATHS - RUTAS BASE DEL PROYECTO
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Ruta absoluta al directorio raíz del proyecto Django.
# Se calcula subiendo 3 niveles desde este archivo:
#   settings/base.py → settings/ → arynstal/ → /home/.../arynstal/
# Se usa para construir rutas a templates, static, media, etc.


# =============================================================================
# 2. INSTALLED_APPS - APLICACIONES INSTALADAS
# =============================================================================

INSTALLED_APPS = [
    # Apps de Django (framework)
    'django.contrib.admin',           # Panel de administración
    'django.contrib.auth',            # Sistema de autenticación
    'django.contrib.contenttypes',    # Framework de tipos de contenido
    'django.contrib.sessions',        # Manejo de sesiones
    'django.contrib.messages',        # Framework de mensajes flash
    'django.contrib.staticfiles',     # Manejo de archivos estáticos

    # Apps del proyecto Arynstal
    'apps.leads.apps.LeadsConfig',        # CRM: Leads, presupuestos, auditoría
    'apps.services.apps.ServicesConfig',  # Catálogo de servicios
    'apps.users.apps.UsersConfig',        # Perfiles de usuario con roles
    'apps.web.apps.WebConfig',            # Vistas públicas del frontend
]


# =============================================================================
# 3. MIDDLEWARE - PIPELINE DE PROCESAMIENTO
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Añade headers de seguridad (X-Content-Type-Options, etc.)

    'django.contrib.sessions.middleware.SessionMiddleware',
    # Habilita el sistema de sesiones

    'django.middleware.common.CommonMiddleware',
    # Funcionalidad común: trailing slashes, redirects, etc.

    'django.middleware.csrf.CsrfViewMiddleware',
    # Protección contra ataques CSRF

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Asocia el usuario a cada request

    'django.contrib.messages.middleware.MessageMiddleware',
    # Habilita mensajes flash entre requests

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Protección contra clickjacking (X-Frame-Options)
]


# =============================================================================
# 4. URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = 'arynstal.urls'
# Módulo que contiene el urlpatterns principal.
# Django usa este archivo para resolver todas las URLs.


# =============================================================================
# 5. TEMPLATES - CONFIGURACIÓN DE PLANTILLAS
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Motor de templates de Django (DTL - Django Template Language)

        'DIRS': [BASE_DIR / 'templates'],
        # Directorio adicional donde buscar templates.
        # Permite tener templates globales fuera de las apps.

        'APP_DIRS': True,
        # Buscar templates en directorio 'templates/' de cada app.

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                # Añade 'debug' y 'sql_queries' al contexto

                'django.template.context_processors.request',
                # Añade 'request' al contexto (necesario para admin)

                'django.contrib.auth.context_processors.auth',
                # Añade 'user' y 'perms' al contexto

                'django.contrib.messages.context_processors.messages',
                # Añade 'messages' al contexto (mensajes flash)
            ],
        },
    },
]


# =============================================================================
# 6. WSGI APPLICATION
# =============================================================================

WSGI_APPLICATION = 'arynstal.wsgi.application'
# Punto de entrada WSGI para servidores de producción (Gunicorn, uWSGI).


# =============================================================================
# 7. PASSWORD VALIDATORS - VALIDADORES DE CONTRASEÑA
# =============================================================================
# Aseguran que las contraseñas de usuarios cumplan requisitos mínimos.
# Se aplican en admin, formularios de registro, cambio de contraseña, etc.

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # Rechaza contraseñas similares al username, email, nombre, etc.
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        # Requiere longitud mínima (por defecto 8 caracteres)
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # Rechaza contraseñas comunes (lista de 20,000 contraseñas)
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # Rechaza contraseñas que sean solo números
    },
]


# =============================================================================
# 8. INTERNATIONALIZATION - IDIOMA Y ZONA HORARIA
# =============================================================================

LANGUAGE_CODE = 'es-es'
# Idioma por defecto del sitio (español de España).
# Afecta al admin, mensajes de error, fechas, etc.

TIME_ZONE = 'Europe/Madrid'
# Zona horaria del servidor.
# Todas las fechas se guardan en UTC pero se muestran en esta zona.

USE_I18N = True
# Habilita el sistema de internacionalización (traducciones).

USE_TZ = True
# Habilita soporte de zonas horarias.
# Las fechas se guardan en UTC en la base de datos.


# =============================================================================
# 9. STATIC FILES - ARCHIVOS ESTÁTICOS (CSS, JS, IMÁGENES)
# =============================================================================
# Archivos que NO cambian durante la ejecución (assets del frontend).

STATIC_URL = '/static/'
# URL base para servir archivos estáticos.
# Ejemplo: /static/css/main.css

STATICFILES_DIRS = [
    BASE_DIR / 'static',
    # Directorio donde se almacenan los archivos estáticos del proyecto.
    # Aquí van: CSS, JS, imágenes del diseño, robots.txt, sitemap.xml, etc.
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
# Directorio donde 'collectstatic' reúne todos los archivos.
# Usado en producción por el servidor web (Nginx).


# =============================================================================
# 10. MEDIA FILES - ARCHIVOS SUBIDOS POR USUARIOS
# =============================================================================
# Archivos que SÍ cambian durante la ejecución (uploads de usuarios).

MEDIA_URL = '/media/'
# URL base para servir archivos subidos.
# Ejemplo: /media/leads/123/imagen.jpg

MEDIA_ROOT = BASE_DIR / 'media'
# Directorio donde se almacenan los archivos subidos.
# Estructura: media/leads/{lead_id}/imagen.jpg


# =============================================================================
# 11. UPLOAD LIMITS - LÍMITES DE SEGURIDAD PARA UPLOADS
# =============================================================================
# Previene ataques de denegación de servicio por archivos muy grandes.

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
# Tamaño máximo de datos POST en memoria.
# Requests más grandes se escriben a disco temporal.

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
# Tamaño máximo de archivo que se guarda en memoria.
# Archivos más grandes se guardan temporalmente en disco.


# =============================================================================
# 12. DEFAULT PRIMARY KEY TYPE
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Tipo de campo para IDs autogenerados por defecto.
# BigAutoField = enteros de 64 bits (hasta 9.2 quintillones).


# =============================================================================
# 13. FORM_SECURITY - SEGURIDAD DE FORMULARIOS PÚBLICOS
# =============================================================================
# Configuración centralizada para medidas anti-spam.
# Usada por views.py en el formulario de contacto.

FORM_SECURITY = {

    # -------------------------------------------------------------------------
    # Rate Limiting - Límites de envío por IP
    # -------------------------------------------------------------------------
    # Previene spam automatizado limitando envíos por dirección IP.
    # Usa la librería django-ratelimit.

    'RATE_LIMIT': {
        'CONTACT_FORM': {
            'rate': '5/h',    # Máximo 5 envíos por hora por IP
            'block': True,    # Bloquear inmediatamente si excede
        },
        # Preparado para futuros formularios:
        # 'NEWSLETTER': {'rate': '3/d', 'block': True},
        # 'COMMENTS': {'rate': '10/h', 'block': False},
    },

    # -------------------------------------------------------------------------
    # Honeypot - Campo trampa para bots
    # -------------------------------------------------------------------------
    # Añade un campo oculto que los humanos no ven pero los bots rellenan.
    # Si el campo tiene valor, sabemos que es un bot.

    'HONEYPOT': {
        'FIELD_NAME': 'website_url',   # Nombre del campo trampa
        'CSS_CLASS': 'ohnohoney',       # Clase CSS que lo oculta
        'ENABLED': True,                # Activar/desactivar
    },

    # Preparado para futuras medidas de seguridad:
    # 'CAPTCHA': {
    #     'ENABLED': False,
    #     'PROVIDER': 'recaptcha',  # 'recaptcha', 'hcaptcha', 'turnstile'
    #     'SITE_KEY': '',
    #     'SECRET_KEY': '',
    # },
    # 'BEHAVIOR_ANALYSIS': {
    #     'ENABLED': False,
    #     'MIN_FILL_TIME_SECONDS': 3,  # Tiempo mínimo para llenar formulario
    # },
}


# =============================================================================
# 14. NOTIFICATIONS - SISTEMA DE NOTIFICACIONES EMAIL
# =============================================================================
# Configuración para emails automáticos del sistema.
# Usada por apps/leads/notifications.py.

NOTIFICATIONS = {
    # Notificaciones de nuevos leads desde el formulario de contacto
    'LEAD': {
        'ENABLED': True,
        # Email(s) que reciben notificación cuando llega un nuevo lead
        'ADMIN_EMAIL': 'admin@arynstal.es',
        # Enviar confirmación automática al cliente
        'SEND_CUSTOMER_CONFIRMATION': True,
    },
    # Preparado para futuras notificaciones:
    # 'BUDGET_REQUEST': {
    #     'ENABLED': True,
    #     'ADMIN_EMAIL': 'presupuestos@arynstal.es',
    # },
}


# =============================================================================
# 15. COMPANY_INFO - INFORMACIÓN DE LA EMPRESA
# =============================================================================
# Datos de contacto y empresa para usar en templates y emails.
# Centralizado aquí para facilitar su actualización.

COMPANY_INFO = {
    'NAME': 'Arynstal',                        # Nombre comercial
    'LEGAL_NAME': 'Arynstal S.L.',             # Razón social
    'EMAIL': 'info@arynstal.es',               # Email de contacto
    'PHONE': '600 000 000',                    # Teléfono (TODO: actualizar)
    'ADDRESS': 'Barcelona, España',            # Dirección
    'WEBSITE': 'https://arynstal.es',          # URL del sitio
    'DESCRIPTION': 'Instalaciones y reformas', # Descripción breve
}
