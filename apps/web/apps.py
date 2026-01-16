"""
===============================================================================
ARCHIVO: apps/web/apps.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configuración de la aplicación Django 'web'.
    Esta app sirve las vistas públicas del frontend (páginas que ven los
    visitantes del sitio).

PROPÓSITO DE LA APP WEB:
    - Renderizar las páginas públicas (home, servicios, contacto, etc.)
    - Procesar el formulario de contacto (crear Leads)
    - Servir archivos SEO (robots.txt, sitemap.xml)
    - Mostrar páginas legales (privacidad, cookies, aviso legal)

NOTA:
    Esta app NO tiene modelos propios. Los datos se guardan en otras apps:
    - apps.leads → Lead, LeadImage, Budget, LeadLog
    - apps.services → Service
    - apps.users → UserProfile

FLUJO DE REGISTRO:
    1. Esta clase se registra en INSTALLED_APPS de settings
    2. Django usa el atributo 'name' para importar la app
    3. 'default_auto_field' define el tipo de ID por defecto para modelos

===============================================================================
"""

from django.apps import AppConfig


class WebConfig(AppConfig):
    """
    Configuración de la app 'web'.

    ATRIBUTOS:
        default_auto_field: Tipo de campo para IDs autogenerados (BigAutoField
                          = enteros de 64 bits, soporta más de 9 quintillones).
        name: Ruta de importación de la app (usada por Django internamente).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.web'
