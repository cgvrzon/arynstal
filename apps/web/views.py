"""
Vistas públicas de la aplicación web (frontend).

FASE 7: Formulario de contacto conectado a modelo Lead.
FASE 8: Seguridad anti-spam (rate limiting + honeypot).
FASE 9: Notificaciones por email (admin + cliente).
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from apps.leads.forms import LeadForm
from apps.leads.models import Lead, LeadImage
from apps.leads.notifications import notify_new_lead


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


def get_client_ip(request):
    """Obtiene la IP real del cliente, considerando proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_honeypot(request):
    """
    Verifica el campo honeypot.
    Retorna True si es bot (honeypot tiene valor), False si es humano.
    """
    honeypot_config = settings.FORM_SECURITY.get('HONEYPOT', {})
    if not honeypot_config.get('ENABLED', True):
        return False

    field_name = honeypot_config.get('FIELD_NAME', 'website_url')
    honeypot_value = request.POST.get(field_name, '')

    # Si el campo tiene valor, es un bot
    return bool(honeypot_value)


# Obtener configuración de rate limit
_rate_config = settings.FORM_SECURITY.get('RATE_LIMIT', {}).get('CONTACT_FORM', {})
_rate = _rate_config.get('rate', '5/h')


@ratelimit(key='ip', rate=_rate, method='POST', block=False)
def contact_us(request):
    """
    Página de contacto con formulario para crear Leads.

    Seguridad implementada:
    - Rate limiting: Máximo de envíos por IP/hora
    - Honeypot: Campo oculto para detectar bots

    GET: Muestra el formulario vacío
    POST: Procesa el formulario, crea Lead + LeadImages, redirige con mensaje
    """
    # Verificar si fue rate-limited
    if getattr(request, 'limited', False):
        messages.error(
            request,
            'Has enviado demasiadas solicitudes. Por favor, espera un momento antes de intentarlo de nuevo.'
        )
        form = LeadForm()
        return render(request, 'pages/contact.html', {'form': form})

    if request.method == 'POST':
        # Verificar honeypot (anti-bot)
        if check_honeypot(request):
            # Es un bot - simular éxito para no revelar la detección
            messages.success(
                request,
                '¡Solicitud enviada correctamente! Nos pondremos en contacto contigo en menos de 24 horas.'
            )
            return redirect('contact_us')

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
            lead.status = 'nuevo'
            lead.source = 'web'
            lead.privacy_accepted = True
            lead.ip_address = get_client_ip(request)
            lead.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            lead.save()

            # Crear LeadImages asociadas
            for image in images:
                LeadImage.objects.create(
                    lead=lead,
                    image=image
                )

            # Enviar notificaciones por email (no bloquea si falla)
            notify_new_lead(lead)

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
