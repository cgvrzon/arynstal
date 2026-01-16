"""
===============================================================================
ARCHIVO: apps/web/models.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    La app 'web' NO tiene modelos propios.
    Sirve únicamente para las vistas públicas del frontend.

ARQUITECTURA DEL PROYECTO:
    Los modelos de datos están organizados en apps especializadas:

    apps.leads (CRM):
        - Lead: Solicitudes de clientes potenciales
        - LeadImage: Imágenes adjuntas a leads
        - Budget: Presupuestos generados
        - LeadLog: Historial de cambios (auditoría)

    apps.services:
        - Service: Catálogo de servicios ofrecidos

    apps.users:
        - UserProfile: Extensión del User de Django con roles

RAZÓN DE ESTA ESTRUCTURA:
    Separar las vistas públicas (app web) de los datos (apps específicas)
    permite una mejor organización y mantenibilidad del código.
    La app web importa los modelos de otras apps cuando los necesita.

===============================================================================
"""

# Esta app no tiene modelos - ver docstring para más información
