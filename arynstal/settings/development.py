"""
===============================================================================
ARCHIVO: arynstal/settings/development.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configuración de Django para el entorno de DESARROLLO LOCAL.
    Hereda de base.py y sobrescribe valores específicos para desarrollo.

CARACTERÍSTICAS DE DESARROLLO:
    - DEBUG = True (muestra errores detallados)
    - SQLite como base de datos (sin configuración externa)
    - Emails se muestran en consola (no se envían realmente)
    - SECRET_KEY hardcodeada (solo para desarrollo)
    - ALLOWED_HOSTS = localhost

USO:
    Se activa automáticamente cuando DJANGO_SETTINGS_MODULE está configurado
    como 'arynstal.settings.development' (ver manage.py y .env).

IMPORTANTE:
    - NUNCA usar esta configuración en producción
    - La SECRET_KEY de este archivo es pública (está en el repo)
    - En producción usar production.py con variables de entorno

===============================================================================
"""

from .base import *


# =============================================================================
# DEBUG MODE
# =============================================================================

DEBUG = True
# Activa el modo debug de Django:
# - Muestra páginas de error detalladas con traceback
# - Habilita la debug toolbar (si está instalada)
# - Muestra queries SQL en errores
# ADVERTENCIA: NUNCA activar en producción (expone información sensible)


# =============================================================================
# SECRET KEY
# =============================================================================

SECRET_KEY = 'django-insecure-iw1@6^ff8yfffl(9hwvcicbpg*r!1kd(1mc+$rpua+1%dcwgz_'
# Clave secreta para firmas criptográficas (CSRF, sesiones, etc.)
# ADVERTENCIA: Esta clave es SOLO para desarrollo.
# - Está hardcodeada en el código (se commitea al repo)
# - En producción se usa variable de entorno SECRET_KEY


# =============================================================================
# ALLOWED HOSTS
# =============================================================================

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
# Hosts/dominios que pueden servir esta aplicación.
# En desarrollo solo permitimos localhost y sus variantes:
# - localhost: Nombre DNS estándar
# - 127.0.0.1: IPv4 de loopback
# - [::1]: IPv6 de loopback


# =============================================================================
# DATABASE - SQLite para desarrollo
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # SQLite: Base de datos embebida en un solo archivo.
        # Ideal para desarrollo: sin configuración, sin servidor.

        'NAME': BASE_DIR / 'db.sqlite3',
        # Archivo donde se guarda la base de datos.
        # Se crea automáticamente en la raíz del proyecto.
    }
}
# NOTA: En producción se usa PostgreSQL (ver production.py)


# =============================================================================
# EMAIL BACKEND - Consola para desarrollo
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# En lugar de enviar emails realmente, los imprime en la consola.
# Útil para desarrollo: ver el contenido de los emails sin configurar SMTP.
#
# Ejemplo de salida en consola:
# -------------------------------------------------------
# Content-Type: text/html; charset="utf-8"
# Subject: Nueva solicitud de contacto
# From: info@arynstal.es
# To: admin@arynstal.es
# ...
# -------------------------------------------------------


# =============================================================================
# DEBUG TOOLBAR (Opcional)
# =============================================================================
# Descomentar estas líneas si instalas django-debug-toolbar:
#
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']
#
# La debug toolbar muestra:
# - Tiempo de carga de cada componente
# - Queries SQL ejecutadas
# - Templates renderizados
# - Cache hits/misses
# - Señales disparadas
