"""
Vistas públicas de la aplicación web (frontend).

FASE 7: Formulario de contacto conectado a modelo Lead.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from apps.leads.forms import LeadForm
from apps.leads.models import Lead, LeadImage


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
    Página de contacto con formulario para crear Leads.

    GET: Muestra el formulario vacío
    POST: Procesa el formulario, crea Lead + LeadImages, redirige con mensaje
    """
    if request.method == 'POST':
        form = LeadForm(request.POST)

        # Validar checkbox de privacidad (campo no en el modelo)
        privacy_accepted = request.POST.get('privacidad') == 'on'

        if not privacy_accepted:
            messages.error(request, 'Debes aceptar la política de privacidad para continuar.')
            return render(request, 'pages/contact.html', {'form': form})

        # Validar formulario
        if form.is_valid():
            # Obtener imágenes subidas
            images = request.FILES.getlist('fotos')

            # Validar número de imágenes (máximo 5)
            if len(images) > 5:
                messages.error(request, 'Solo puedes subir un máximo de 5 fotos.')
                return render(request, 'pages/contact.html', {'form': form})

            # Crear el Lead (sin guardar aún para asignar campos adicionales)
            lead = form.save(commit=False)
            lead.status = 'nuevo'  # Estado inicial
            lead.source = 'web'  # Origen del lead
            lead.save()

            # Crear LeadImages asociadas
            for image in images:
                LeadImage.objects.create(
                    lead=lead,
                    image=image
                )

            # Mensaje de éxito
            messages.success(
                request,
                '¡Solicitud enviada correctamente! Nos pondremos en contacto contigo en menos de 24 horas.'
            )

            # Redirigir para evitar re-envío del formulario (patrón POST-Redirect-GET)
            return redirect('contact_us')

        else:
            # Formulario inválido, mostrar errores
            messages.error(request, 'Por favor, corrige los errores en el formulario.')

    else:
        # GET: Mostrar formulario vacío
        form = LeadForm()

    return render(request, 'pages/contact.html', {'form': form})


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
