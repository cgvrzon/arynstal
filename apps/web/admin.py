"""
===============================================================================
ARCHIVO: apps/web/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configuración global del panel de administración de Django.
    Define los textos y títulos que aparecen en el header del admin.

FUNCIONES PRINCIPALES:
    - Personalización del título del sitio admin
    - Personalización del header y nombre mostrado

NOTA IMPORTANTE:
    La app 'web' NO tiene modelos propios. Sirve únicamente para las
    vistas públicas del frontend. Los modelos de datos están en:
    - apps.leads: Lead, LeadImage, Budget, LeadLog
    - apps.services: Service
    - apps.users: UserProfile

CONFIGURACIÓN DE ADMIN POR APP:
    - apps/leads/admin.py → LeadAdmin, BudgetAdmin, etc.
    - apps/services/admin.py → ServiceAdmin
    - apps/users/admin.py → UserAdmin extendido con UserProfile

===============================================================================
"""

from django.contrib import admin


# =============================================================================
# PERSONALIZACIÓN GLOBAL DEL ADMIN
# =============================================================================
# Estos valores se muestran en todas las páginas del panel de administración.
# Se configuran aquí (no en cada app) porque son globales al sitio.

admin.site.site_header = "Arynstal SL - Administración"
# Texto que aparece en la parte superior de todas las páginas del admin
# (reemplaza el texto por defecto "Django administration")

admin.site.site_title = "Arynstal Admin"
# Texto que aparece en la pestaña del navegador
# (se concatena con el nombre de cada sección)

admin.site.index_title = "Panel de control"
# Título que aparece en la página principal del admin (/admynstal/)
# (reemplaza "Site administration")
