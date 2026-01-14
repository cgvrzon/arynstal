from django.urls import path
from . import views

urlpatterns = [
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