"""
Configuración de Django para el entorno de DESARROLLO.

- DEBUG activado
- SQLite como base de datos
- Emails se muestran en consola
- SECRET_KEY de desarrollo (NO usar en producción)
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
# Esta es solo para desarrollo, NUNCA usar en producción
SECRET_KEY = 'django-insecure-iw1@6^ff8yfffl(9hwvcicbpg*r!1kd(1mc+$rpua+1%dcwgz_'

# Hosts permitidos en desarrollo
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']


# Database - SQLite para desarrollo
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Email backend - Los emails se imprimen en consola
# https://docs.djangoproject.com/en/6.0/topics/email/#console-backend

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Debug toolbar (opcional, si lo instalas en el futuro)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']
