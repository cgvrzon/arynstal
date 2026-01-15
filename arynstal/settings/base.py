"""
Django settings for arynstal project.
Configuración base compartida entre todos los entornos.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Ajustamos BASE_DIR porque ahora estamos en settings/ en lugar de la raíz
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del proyecto
    'apps.leads.apps.LeadsConfig',
    'apps.services.apps.ServicesConfig',
    'apps.users.apps.UsersConfig',
    'apps.contact.apps.ContactConfig',
    'apps.web.apps.WebConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'arynstal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'arynstal.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# Media files (Uploaded files - imágenes de contactos, etc.)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Límites de seguridad para uploads
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB máximo por request
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB máximo por archivo


# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD - FORMULARIOS PÚBLICOS
# =============================================================================
# Configuración centralizada para medidas anti-spam.
# Escalable: añadir nuevas configuraciones aquí para futuras medidas.

FORM_SECURITY = {
    # Rate Limiting - Límites de envío por IP
    'RATE_LIMIT': {
        'CONTACT_FORM': {
            'rate': '5/h',  # 5 envíos por hora por IP
            'block': True,  # Bloquear si excede (vs solo avisar)
        },
        # Preparado para futuros formularios:
        # 'NEWSLETTER': {'rate': '3/d', 'block': True},
        # 'COMMENTS': {'rate': '10/h', 'block': False},
    },

    # Honeypot - Campos trampa para bots
    'HONEYPOT': {
        'FIELD_NAME': 'website_url',  # Nombre del campo trampa
        'CSS_CLASS': 'ohnohoney',  # Clase CSS para ocultar
        'ENABLED': True,
    },

    # Preparado para futuras medidas:
    # 'CAPTCHA': {
    #     'ENABLED': False,
    #     'PROVIDER': 'recaptcha',  # 'recaptcha', 'hcaptcha', 'turnstile'
    #     'SITE_KEY': '',
    #     'SECRET_KEY': '',
    # },
    # 'BEHAVIOR_ANALYSIS': {
    #     'ENABLED': False,
    #     'MIN_FILL_TIME_SECONDS': 3,  # Mínimo tiempo para llenar formulario
    # },
}


# =============================================================================
# CONFIGURACIÓN DE NOTIFICACIONES
# =============================================================================
# Sistema de notificaciones por email para eventos del sistema.

NOTIFICATIONS = {
    # Notificaciones de nuevos leads
    'LEAD': {
        'ENABLED': True,
        # Email(s) que reciben notificación de nuevo lead (admin/comercial)
        'ADMIN_EMAIL': 'info@arynstal.es',
        # Enviar confirmación al cliente
        'SEND_CUSTOMER_CONFIRMATION': True,
    },
    # Preparado para futuras notificaciones:
    # 'BUDGET_REQUEST': {
    #     'ENABLED': True,
    #     'ADMIN_EMAIL': 'presupuestos@arynstal.es',
    # },
}
