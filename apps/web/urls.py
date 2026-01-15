from django.urls import path
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
import os
from . import views

urlpatterns = [
    # SEO - robots.txt y sitemap.xml
    path('robots.txt', serve, {
        'path': 'robots.txt',
        'document_root': settings.STATICFILES_DIRS[0],
    }, name='robots'),
    path('sitemap.xml', serve, {
        'path': 'sitemap.xml',
        'document_root': settings.STATICFILES_DIRS[0],
        'content_type': 'application/xml',
    }, name='sitemap'),

    # Páginas principales
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('projects/', views.projects, name='projects'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact/', views.contact_us, name='contact_us'),

    # Páginas legales (RGPD)
    path('privacy/', views.privacy, name='privacy'),
    path('legal-notice/', views.legal_notice, name='legal_notice'),
    path('cookies/', views.cookies, name='cookies'),
]