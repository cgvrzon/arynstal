"""
Vistas públicas de la aplicación web (frontend).

FASE actual: Solo renderiza páginas estáticas.
FASE 7: Se implementará la lógica del formulario de contacto → Lead.
"""

from django.shortcuts import render


def home(request):
    """Página de inicio"""
    return render(request, 'web/index.html')


def services(request):
    """Página de servicios"""
    return render(request, 'web/services.html')


def projects(request):
    """Página de proyectos/portfolio"""
    return render(request, 'web/projects.html')


def about_us(request):
    """Página sobre nosotros"""
    return render(request, 'web/about_us.html')


def contact_us(request):
    """
    Página de contacto.

    TODO FASE 7: Implementar lógica de formulario que cree Lead.
    Por ahora solo muestra la página estática.
    """
    return render(request, 'web/contact_us.html')
