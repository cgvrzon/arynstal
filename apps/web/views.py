"""
Vistas públicas de la aplicación web (frontend).

FASE actual: Solo renderiza páginas estáticas.
FASE 7: Se implementará la lógica del formulario de contacto → Lead.
"""

from django.shortcuts import render


def home(request):
    """Página de inicio"""
    return render(request, 'pages/index.html')


def services(request):
    """Página de servicios"""
    return render(request, 'pages/services.html')


def projects(request):
    """Página de proyectos/portfolio"""
    return render(request, 'pages/projects.html')


def about_us(request):
    """Página sobre nosotros"""
    return render(request, 'pages/about.html')


def contact_us(request):
    """
    Página de contacto.

    TODO FASE 7: Implementar lógica de formulario que cree Lead.
    Por ahora solo muestra la página estática.
    """
    return render(request, 'pages/contact.html')


def privacy(request):
    """Política de privacidad"""
    return render(request, 'legal/privacy.html')


def legal_notice(request):
    """Aviso legal"""
    return render(request, 'legal/legal_notice.html')


def cookies(request):
    """Política de cookies"""
    return render(request, 'legal/cookies.html')


def handler404(request, exception):
    """Vista personalizada para error 404"""
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Vista personalizada para error 500"""
    return render(request, 'errors/500.html', status=500)
