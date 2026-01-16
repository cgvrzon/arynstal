"""
===============================================================================
ARCHIVO: apps/web/urls.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define el enrutamiento URL para todas las páginas públicas de la web.
    Mapea URLs a las vistas correspondientes en views.py.

ESTRUCTURA DE URLs:
    RAÍZ:
    - / → home (página de inicio)

    PÁGINAS PRINCIPALES:
    - /services/ → services (catálogo de servicios)
    - /projects/ → projects (portfolio)
    - /about-us/ → about_us (sobre nosotros)
    - /contact/ → contact_us (formulario de contacto)

    PÁGINAS LEGALES:
    - /privacy/ → privacy (política de privacidad)
    - /legal-notice/ → legal_notice (aviso legal)
    - /cookies/ → cookies (política de cookies)

    SEO:
    - /robots.txt → Archivo para crawlers
    - /sitemap.xml → Mapa del sitio para SEO

FLUJO DE CONFIGURACIÓN:
    1. arynstal/urls.py incluye este archivo con: include('apps.web.urls')
    2. Cada path() mapea una URL a una función de views.py
    3. El parámetro name permite usar {% url 'name' %} en templates

NOTA SOBRE ADMIN:
    La URL del admin (/gestion-interna/) se define en arynstal/urls.py,
    no aquí, porque es configuración global del proyecto.

===============================================================================
"""

from django.urls import path
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
import os
from . import views


# =============================================================================
# PATRONES DE URL
# =============================================================================

urlpatterns = [

    # -------------------------------------------------------------------------
    # SEO - ARCHIVOS PARA CRAWLERS
    # -------------------------------------------------------------------------
    # robots.txt y sitemap.xml se sirven como archivos estáticos desde
    # la carpeta static/. Esto permite editarlos fácilmente sin tocar código.

    path('robots.txt', serve, {
        'path': 'robots.txt',
        'document_root': settings.STATICFILES_DIRS[0],
    }, name='robots'),
    # URL: /robots.txt
    # Propósito: Indica a los crawlers qué pueden indexar

    path('sitemap.xml', serve, {
        'path': 'sitemap.xml',
        'document_root': settings.STATICFILES_DIRS[0],
        'content_type': 'application/xml',
    }, name='sitemap'),
    # URL: /sitemap.xml
    # Propósito: Mapa del sitio para SEO (Google Search Console)

    # -------------------------------------------------------------------------
    # PÁGINAS PRINCIPALES
    # -------------------------------------------------------------------------

    path('', views.home, name='home'),
    # URL: /
    # Vista: home()
    # Template: pages/index.html
    # Propósito: Página de inicio con hero y resumen de servicios

    path('services/', views.services, name='services'),
    # URL: /services/
    # Vista: services()
    # Template: pages/services.html
    # Propósito: Catálogo de servicios de Arynstal

    path('projects/', views.projects, name='projects'),
    # URL: /projects/
    # Vista: projects()
    # Template: pages/projects.html
    # Propósito: Portfolio de proyectos realizados

    path('about-us/', views.about_us, name='about_us'),
    # URL: /about-us/
    # Vista: about_us()
    # Template: pages/about.html
    # Propósito: Información sobre la empresa

    path('contact/', views.contact_us, name='contact_us'),
    # URL: /contact/
    # Vista: contact_us()
    # Template: pages/contact.html
    # Propósito: Formulario de contacto para crear leads
    # IMPORTANTE: Esta es la vista más crítica del sitio

    # -------------------------------------------------------------------------
    # PÁGINAS LEGALES (RGPD)
    # -------------------------------------------------------------------------
    # Obligatorias según la normativa de protección de datos.

    path('privacy/', views.privacy, name='privacy'),
    # URL: /privacy/
    # Vista: privacy()
    # Template: legal/privacy.html
    # Propósito: Política de privacidad (enlazada desde formulario)

    path('legal-notice/', views.legal_notice, name='legal_notice'),
    # URL: /legal-notice/
    # Vista: legal_notice()
    # Template: legal/legal_notice.html
    # Propósito: Aviso legal de la empresa

    path('cookies/', views.cookies, name='cookies'),
    # URL: /cookies/
    # Vista: cookies()
    # Template: legal/cookies.html
    # Propósito: Política de cookies
]
