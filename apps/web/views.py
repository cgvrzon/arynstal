"""
===============================================================================
ARCHIVO: apps/web/views.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define las vistas públicas del frontend de la aplicación.
    Estas vistas sirven las páginas que ven los visitantes del sitio.

FUNCIONES PRINCIPALES:
    PÁGINAS PÚBLICAS:
    - home: Página de inicio
    - services: Catálogo de servicios
    - projects: Portfolio de proyectos
    - about_us: Información de la empresa
    - contact_us: Formulario de contacto (CRÍTICA)

    PÁGINAS LEGALES:
    - privacy: Política de privacidad
    - legal_notice: Aviso legal
    - cookies: Política de cookies

    PÁGINAS DE ERROR:
    - handler404: Error 404 personalizado
    - handler500: Error 500 personalizado

    FUNCIONES AUXILIARES:
    - get_client_ip: Obtiene IP real del visitante
    - check_honeypot: Detecta bots mediante campo trampa

FLUJO PRINCIPAL - FORMULARIO DE CONTACTO:
    1. Usuario accede a /contact/ (GET)
    2. Se muestra formulario vacío con LeadForm
    3. Usuario rellena y envía (POST)
    4. Se verifican medidas anti-spam:
       - Rate limiting: Máx 5 envíos/hora por IP
       - Honeypot: Campo oculto detecta bots
    5. Se valida formulario y checkbox de privacidad
    6. Se crea Lead con datos del formulario
    7. Se adjuntan imágenes (máx 5)
    8. Se envían notificaciones por email
    9. Redirect a /contact/ con mensaje de éxito

SEGURIDAD IMPLEMENTADA:
    - Rate limiting: django-ratelimit (5/hora por IP)
    - Honeypot: Campo oculto 'website_url'
    - RGPD: Checkbox obligatorio de privacidad
    - Registro de IP: Para auditoría y anti-spam
    - User-Agent: Para identificar posibles bots

PATRÓN POST-REDIRECT-GET:
    Después de procesar el formulario, se redirige para evitar
    que el usuario reenvíe el formulario al refrescar la página.

===============================================================================
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect

from django.conf import settings
from django_ratelimit.decorators import ratelimit

from apps.leads.forms import LeadForm
from apps.leads.models import LeadImage
from apps.leads.notifications import notify_new_lead
from apps.leads.validators import validate_image_file


# =============================================================================
# PÁGINAS PÚBLICAS BÁSICAS
# =============================================================================
# Vistas simples que solo renderizan templates sin lógica adicional.

def home(request):
    """
    Página de inicio de la web.

    TEMPLATE: templates/pages/index.html

    CONTENIDO:
        - Hero con propuesta de valor
        - Resumen de servicios
        - Call to action hacia contacto
    """
    return render(request, 'pages/index.html')


def services(request):
    """
    Página del catálogo de servicios.

    TEMPLATE: templates/pages/services.html

    CONTENIDO:
        - Listado de servicios de Arynstal
        - Descripciones y iconos
        - Enlaces a contacto

    FUTURO:
        Podría cargar Service.objects.filter(is_active=True)
        para mostrar servicios dinámicamente desde BD.
    """
    return render(request, 'pages/services.html')


def projects(request):
    """
    Página de portfolio/proyectos realizados.

    TEMPLATE: templates/pages/projects.html

    CONTENIDO:
        - Galería de proyectos completados
        - Testimonios de clientes
    """
    return render(request, 'pages/projects.html')


def about_us(request):
    """
    Página de información sobre la empresa.

    TEMPLATE: templates/pages/about.html

    CONTENIDO:
        - Historia de Arynstal
        - Equipo y valores
        - Certificaciones
    """
    return render(request, 'pages/about.html')


# =============================================================================
# FUNCIONES AUXILIARES DE SEGURIDAD
# =============================================================================

def get_client_ip(request) -> str:
    """
    Obtiene la IP real del cliente, considerando proxies y CDNs.

    PROPÓSITO:
        Necesitamos la IP real para:
        - Rate limiting preciso
        - Registro en Lead para auditoría
        - Detección de spam/abuso

    ALGORITMO:
        1. Buscar header X-Forwarded-For (usado por proxies/CDNs)
        2. Si existe, tomar la primera IP (la del cliente original)
        3. Si no, usar REMOTE_ADDR directamente

    PARÁMETROS:
        request: Objeto HttpRequest de Django.

    RETORNA:
        str: Dirección IP del cliente.

    NOTA SOBRE PROXIES:
        Cuando hay proxy (Nginx, Cloudflare), REMOTE_ADDR contiene
        la IP del proxy, no del cliente. X-Forwarded-For contiene
        la cadena de IPs: "cliente, proxy1, proxy2".
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Tomar la primera IP (cliente original)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Sin proxy, usar REMOTE_ADDR directamente
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_honeypot(request) -> bool:
    """
    Verifica si el formulario fue enviado por un bot usando honeypot.

    TÉCNICA HONEYPOT:
        Se añade un campo oculto al formulario que los humanos no ven
        ni rellenan, pero los bots sí (porque procesan todo el HTML).
        Si el campo tiene valor, es un bot.

    PARÁMETROS:
        request: Objeto HttpRequest con datos POST.

    RETORNA:
        bool: True si es bot (honeypot tiene valor), False si es humano.

    CONFIGURACIÓN (settings.FORM_SECURITY):
        HONEYPOT: {
            'ENABLED': True,
            'FIELD_NAME': 'website_url',
            'CSS_CLASS': 'ohnohoney'
        }

    IMPORTANTE:
        Si se detecta bot, NO informamos al atacante.
        Simulamos éxito para que no sepa que fue detectado.
    """
    honeypot_config = settings.FORM_SECURITY.get('HONEYPOT', {})

    # Si honeypot está deshabilitado, pasar todos
    if not honeypot_config.get('ENABLED', True):
        return False

    # Obtener nombre del campo trampa
    field_name = honeypot_config.get('FIELD_NAME', 'website_url')
    honeypot_value = request.POST.get(field_name, '')

    # Si el campo tiene valor, es un bot
    return bool(honeypot_value)


# =============================================================================
# CONFIGURACIÓN DE RATE LIMITING
# =============================================================================
# Cargamos la configuración aquí para usarla en el decorador.

_rate_config = settings.FORM_SECURITY.get('RATE_LIMIT', {}).get('CONTACT_FORM', {})
_rate = _rate_config.get('rate', '3/h')  # 3 envíos por hora por defecto


# =============================================================================
# VISTA PRINCIPAL: FORMULARIO DE CONTACTO
# =============================================================================

@ratelimit(key='ip', rate=_rate, method='POST', block=False)
def contact_us(request):
    """
    Página de contacto con formulario para crear Leads.

    DESCRIPCIÓN:
        Vista central del CRM. Permite a los visitantes enviar
        solicitudes de información que se convierten en Leads.
        Incluye múltiples capas de seguridad anti-spam.

    MÉTODOS HTTP:
        GET: Muestra el formulario vacío
        POST: Procesa el formulario y crea el Lead

    PARÁMETROS:
        request: Objeto HttpRequest de Django.

    RETORNA:
        HttpResponse: Página renderizada o redirect.

    TEMPLATE:
        templates/pages/contact.html

    CONTEXTO:
        form: Instancia de LeadForm (vacía o con errores)

    SEGURIDAD:
        1. Rate Limiting (@ratelimit decorator)
           - Máximo configurable de envíos por hora por IP
           - Si excede, muestra mensaje y no procesa

        2. Honeypot (check_honeypot)
           - Detecta bots que rellenan campos ocultos
           - Si detecta bot, simula éxito silenciosamente

        3. Validación de privacidad
           - Checkbox obligatorio de RGPD
           - Sin él, no se procesa el formulario

        4. Validación de imágenes
           - Máximo 5 imágenes
           - Validación de tipo y tamaño en modelo

    FLUJO COMPLETO:
        1. [GET] Usuario accede a /contact/
        2. Se renderiza formulario vacío
        3. [POST] Usuario envía formulario
        4. Verificar rate limit → Si excede, error y salir
        5. Verificar honeypot → Si bot, éxito falso y salir
        6. Verificar privacidad → Si no acepta, error y salir
        7. Validar formulario → Si errores, mostrarlos
        8. Validar imágenes → Si >5, error
        9. Crear Lead con datos adicionales (IP, UA, etc.)
        10. Crear LeadImages para cada imagen
        11. Enviar notificaciones por email
        12. Redirect a /contact/ con mensaje de éxito

    PATRÓN POST-REDIRECT-GET:
        Después de éxito, redirigimos a la misma página.
        Esto evita que el navegador reenvíe el formulario
        si el usuario refresca la página.
    """

    # -------------------------------------------------------------------------
    # PASO 1: Verificar Rate Limiting
    # -------------------------------------------------------------------------
    # El decorador @ratelimit añade el atributo 'limited' si se excedió el límite.
    # Usamos block=False para manejar el error manualmente.

    if getattr(request, 'limited', False):
        messages.error(
            request,
            'Has enviado demasiadas solicitudes. Por favor, espera un momento '
            'antes de intentarlo de nuevo.'
        )
        form = LeadForm()
        return render(request, 'pages/contact.html', {'form': form})

    # -------------------------------------------------------------------------
    # PASO 2: Procesar POST
    # -------------------------------------------------------------------------

    if request.method == 'POST':

        # ---------------------------------------------------------------------
        # PASO 2.1: Verificar Honeypot
        # ---------------------------------------------------------------------
        if check_honeypot(request):
            # Es un bot - simular éxito para no revelar la detección
            # El bot cree que funcionó, pero no creamos nada
            messages.success(
                request,
                '¡Solicitud enviada correctamente! '
                'Nos pondremos en contacto contigo en menos de 24 horas.'
            )
            return redirect('contact_us')

        # ---------------------------------------------------------------------
        # PASO 2.2: Crear formulario con datos POST
        # ---------------------------------------------------------------------
        form = LeadForm(request.POST)

        # ---------------------------------------------------------------------
        # PASO 2.3: Validar checkbox de privacidad
        # ---------------------------------------------------------------------
        # El checkbox no está en LeadForm, se valida manualmente
        privacy_accepted = request.POST.get('privacidad') == 'on'

        if not privacy_accepted:
            messages.error(
                request,
                'Debes aceptar la política de privacidad para continuar.'
            )
            return render(request, 'pages/contact.html', {'form': form})

        # ---------------------------------------------------------------------
        # PASO 2.4: Validar formulario
        # ---------------------------------------------------------------------
        if form.is_valid():

            # -----------------------------------------------------------------
            # PASO 2.5: Validar imágenes (magic bytes, tamaño, extensión)
            # -----------------------------------------------------------------
            images = request.FILES.getlist('fotos')

            if len(images) > 5:
                messages.error(
                    request,
                    'Solo puedes subir un máximo de 5 fotos.'
                )
                return render(request, 'pages/contact.html', {'form': form})

            for i, image in enumerate(images):
                try:
                    validate_image_file(image)
                except ValidationError as e:
                    messages.error(
                        request,
                        f'Imagen {i + 1} ({getattr(image, "name", "?")}): {str(e)}'
                    )
                    return render(
                        request, 'pages/contact.html', {'form': form}
                    )

            # -----------------------------------------------------------------
            # PASO 2.6: Crear Lead
            # -----------------------------------------------------------------
            # Usamos commit=False para añadir campos adicionales antes de guardar
            lead = form.save(commit=False)
            lead.status = 'nuevo'
            lead.source = 'web'
            lead.privacy_accepted = True
            lead.ip_address = get_client_ip(request)
            lead.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            lead.save()

            # -----------------------------------------------------------------
            # PASO 2.7: Crear LeadImages
            # -----------------------------------------------------------------
            for image in images:
                LeadImage.objects.create(
                    lead=lead,
                    image=image
                )

            # -----------------------------------------------------------------
            # PASO 2.8: Enviar notificaciones
            # -----------------------------------------------------------------
            # notify_new_lead maneja errores internamente, no bloquea
            notify_new_lead(lead)

            # -----------------------------------------------------------------
            # PASO 2.9: Mensaje de éxito y redirect
            # -----------------------------------------------------------------
            messages.success(
                request,
                '¡Solicitud enviada correctamente! '
                'Nos pondremos en contacto contigo en menos de 24 horas.'
            )

            # Patrón POST-Redirect-GET
            return redirect('contact_us')

        else:
            # Formulario inválido, mostrar errores
            messages.error(
                request,
                'Por favor, corrige los errores en el formulario.'
            )

    else:
        # ---------------------------------------------------------------------
        # GET: Mostrar formulario vacío
        # ---------------------------------------------------------------------
        form = LeadForm()

    return render(request, 'pages/contact.html', {'form': form})


# =============================================================================
# PÁGINAS LEGALES (RGPD)
# =============================================================================
# Requeridas por la normativa de protección de datos.

def privacy(request):
    """
    Política de privacidad (RGPD).

    TEMPLATE: templates/legal/privacy.html

    CONTENIDO:
        - Información sobre tratamiento de datos
        - Derechos del usuario
        - Contacto del responsable

    OBLIGATORIO:
        Enlazado desde el formulario de contacto.
    """
    return render(request, 'legal/privacy.html')


def legal_notice(request):
    """
    Aviso legal de la empresa.

    TEMPLATE: templates/legal/legal_notice.html

    CONTENIDO:
        - Datos fiscales de la empresa
        - Información del responsable
        - Condiciones de uso
    """
    return render(request, 'legal/legal_notice.html')


def cookies(request):
    """
    Política de cookies.

    TEMPLATE: templates/legal/cookies.html

    CONTENIDO:
        - Tipos de cookies utilizadas
        - Finalidad de cada cookie
        - Cómo desactivarlas
    """
    return render(request, 'legal/cookies.html')


# =============================================================================
# HANDLERS DE ERROR
# =============================================================================
# Vistas personalizadas para errores HTTP.
# Se configuran en urls.py raíz: handler404 = 'apps.web.views.handler404'

def handler404(request, exception):
    """
    Vista personalizada para error 404 (página no encontrada).

    PARÁMETROS:
        request: HttpRequest
        exception: Excepción que causó el 404

    TEMPLATE: templates/errors/404.html

    NOTA:
        Solo se muestra con DEBUG=False.
        En desarrollo, Django muestra su propia página de debug.
    """
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """
    Vista personalizada para error 500 (error del servidor).

    PARÁMETROS:
        request: HttpRequest

    TEMPLATE: templates/errors/500.html

    NOTA:
        Solo se muestra con DEBUG=False.
        En producción, es importante tener esta página
        para no mostrar información sensible al usuario.
    """
    return render(request, 'errors/500.html', status=500)


# =============================================================================
# HEALTH CHECK - MONITOREO
# =============================================================================

def health_check(request):
    """
    Endpoint de health check para monitoreo de disponibilidad.

    PROPÓSITO:
        Permite a servicios externos verificar que la aplicación está
        funcionando correctamente. Usado por:
        - UptimeRobot, Better Uptime, Pingdom
        - Load balancers
        - Kubernetes liveness probes
        - Sistemas de alertas

    URL: /health/

    MÉTODO HTTP:
        GET

    RETORNA:
        JsonResponse con:
        - status: "healthy" o "unhealthy"
        - timestamp: Hora actual del servidor
        - database: Estado de la conexión a BD
        - version: Versión de la aplicación

    CÓDIGOS HTTP:
        200: Todo funciona correctamente
        503: Algún componente está fallando

    EJEMPLO DE RESPUESTA:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "database": "connected",
            "version": "1.0.0"
        }

    NOTA:
        Este endpoint NO requiere autenticación para que los servicios
        de monitoreo externos puedan acceder sin credenciales.
    """
    from django.http import JsonResponse
    from django.db import connection
    from django.utils import timezone

    # Verificar conexión a la base de datos
    db_status = "connected"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"

    # Determinar estado general
    is_healthy = db_status == "connected"

    response_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": timezone.now().isoformat(),
        "database": db_status,
        "version": "1.0.0",
    }

    status_code = 200 if is_healthy else 503

    return JsonResponse(response_data, status=status_code)
