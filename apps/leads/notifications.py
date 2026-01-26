"""
===============================================================================
ARCHIVO: apps/leads/notifications.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Sistema de notificaciones por email para el módulo de leads.
    Gestiona el envío de emails automáticos cuando se crea un nuevo lead,
    tanto al administrador como al cliente.

FUNCIONES PRINCIPALES:
    - send_admin_notification: Notifica al admin de nuevo lead
    - send_customer_confirmation: Envía confirmación al cliente
    - notify_new_lead: Función orquestadora que envía ambos emails

FLUJO EN LA APLICACIÓN:
    1. Usuario envía formulario de contacto
    2. Vista contact_us() crea el Lead y llama a notify_new_lead()
    3. notify_new_lead() envía email al admin
    4. notify_new_lead() envía confirmación al cliente
    5. Retorna resultado de ambos envíos

CONFIGURACIÓN:
    Los emails se configuran en settings.NOTIFICATIONS['LEAD']:
    - ENABLED: Activa/desactiva notificaciones
    - ADMIN_EMAIL: Email del administrador
    - SEND_CUSTOMER_CONFIRMATION: Activa confirmación al cliente

TEMPLATES DE EMAIL:
    - templates/emails/lead_admin_notification.html
    - templates/emails/lead_customer_confirmation.html

ENTORNO:
    - Desarrollo: Los emails se muestran en consola (EMAIL_BACKEND=console)
    - Producción: Se envían vía SMTP (Brevo configurado en production.py)

PRINCIPIOS DE DISEÑO:
    - Fail-safe: Los errores de email no rompen el flujo principal
    - Logging: Todos los envíos y errores se registran
    - Configuración externa: Todo parametrizable desde settings

===============================================================================
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

# Logger para registrar eventos de notificaciones
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCIÓN AUXILIAR: OBTENER CONFIGURACIÓN
# =============================================================================

def get_notification_config() -> dict:
    """
    Obtiene la configuración de notificaciones desde settings.

    RETORNA:
        dict: Configuración del módulo LEAD en NOTIFICATIONS.
              Vacío si no está configurado.

    CONFIGURACIÓN ESPERADA (settings.py):
        NOTIFICATIONS = {
            'LEAD': {
                'ENABLED': True,
                'ADMIN_EMAIL': 'admin@ejemplo.com',
                'SEND_CUSTOMER_CONFIRMATION': True,
            }
        }

    EJEMPLO DE USO:
        >>> config = get_notification_config()
        >>> if config.get('ENABLED', True):
        >>>     # Enviar notificación
    """
    return settings.NOTIFICATIONS.get('LEAD', {})


# =============================================================================
# FUNCIÓN: NOTIFICACIÓN AL ADMINISTRADOR
# =============================================================================

def send_admin_notification(lead) -> bool:
    """
    Envía notificación al administrador cuando se crea un nuevo lead.

    DESCRIPCIÓN:
        Genera y envía un email HTML informando al administrador
        sobre el nuevo lead recibido, incluyendo todos los datos
        relevantes y un enlace directo al admin.

    PARÁMETROS:
        lead (Lead): Instancia del modelo Lead recién creado.

    RETORNA:
        bool: True si el email se envió correctamente, False si falló.

    FLUJO:
        1. Verificar si las notificaciones están habilitadas
        2. Obtener email del admin desde configuración
        3. Renderizar template HTML con datos del lead
        4. Crear versión texto plano (strip_tags)
        5. Enviar email con ambas versiones (HTML + texto)
        6. Registrar resultado en logs

    TEMPLATE UTILIZADO:
        templates/emails/lead_admin_notification.html

    CONTEXTO DEL TEMPLATE:
        - lead: Objeto Lead con todos sus datos
        - lead_url: URL relativa al admin para editar el lead

    MANEJO DE ERRORES:
        Los errores se capturan y registran en logs.
        La función retorna False pero no lanza excepción
        para no interrumpir el flujo principal.
    """
    config = get_notification_config()

    # -------------------------------------------------------------------------
    # Verificar si notificaciones están habilitadas
    # -------------------------------------------------------------------------
    if not config.get('ENABLED', True):
        logger.info(
            f'Notificaciones deshabilitadas. Lead {lead.id} no notificado.'
        )
        return False

    # Obtener email destino (con fallback por defecto)
    admin_email = config.get('ADMIN_EMAIL', 'info@arynstal.es')

    # -------------------------------------------------------------------------
    # Preparar contexto para el template
    # -------------------------------------------------------------------------
    # URL absoluta al admin (emails requieren enlaces absolutos).
    # El admin está en /gestion-interna/, no /admin/.
    path = reverse('admin:leads_lead_change', args=[lead.id])
    base = getattr(settings, 'COMPANY_INFO', {}).get('WEBSITE', '').rstrip('/')
    lead_url = f'{base}{path}' if base else path

    context = {
        'lead': lead,
        'lead_url': lead_url,
    }

    try:
        # ---------------------------------------------------------------------
        # Renderizar template HTML
        # ---------------------------------------------------------------------
        html_content = render_to_string(
            'emails/lead_admin_notification.html',
            context
        )
        # Generar versión texto plano (para clientes que no soportan HTML)
        text_content = strip_tags(html_content)

        # Asunto del email con emoji para destacar
        subject = f'Nuevo contacto: {lead.name}'

        # ---------------------------------------------------------------------
        # Crear y enviar email multipart (HTML + texto)
        # ---------------------------------------------------------------------
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,  # Versión texto plano
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[admin_email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            f'Notificación de admin enviada para Lead {lead.id} a {admin_email}'
        )
        return True

    except Exception as e:
        # Registrar error pero no propagar la excepción
        logger.error(
            f'Error enviando notificación de admin para Lead {lead.id}: {e}'
        )
        return False


# =============================================================================
# FUNCIÓN: CONFIRMACIÓN AL CLIENTE
# =============================================================================

def send_customer_confirmation(lead) -> bool:
    """
    Envía email de confirmación al cliente cuando se recibe su solicitud.

    DESCRIPCIÓN:
        Genera y envía un email de confirmación al cliente agradeciéndole
        su contacto e informándole de los próximos pasos.

    PARÁMETROS:
        lead (Lead): Instancia del modelo Lead recién creado.

    RETORNA:
        bool: True si el email se envió correctamente, False si falló.

    FLUJO:
        1. Verificar si notificaciones están habilitadas
        2. Verificar si confirmación al cliente está activa
        3. Renderizar template HTML personalizado
        4. Enviar email al email del lead

    TEMPLATE UTILIZADO:
        templates/emails/lead_customer_confirmation.html

    CONTEXTO DEL TEMPLATE:
        - lead: Objeto Lead (para personalizar con nombre, servicio, etc.)

    IMPORTANCIA UX:
        Este email es crucial para la experiencia del usuario:
        - Confirma que su mensaje fue recibido
        - Reduce ansiedad de "¿habrá llegado mi mensaje?"
        - Establece expectativas sobre tiempo de respuesta
        - Refuerza la imagen profesional de la empresa
    """
    config = get_notification_config()

    # -------------------------------------------------------------------------
    # Verificar configuración
    # -------------------------------------------------------------------------
    if not config.get('ENABLED', True):
        return False

    if not config.get('SEND_CUSTOMER_CONFIRMATION', True):
        logger.info(
            f'Confirmación al cliente deshabilitada. Lead {lead.id} no confirmado.'
        )
        return False

    # -------------------------------------------------------------------------
    # Preparar contexto para el template
    # -------------------------------------------------------------------------
    context = {
        'lead': lead,
    }

    try:
        # ---------------------------------------------------------------------
        # Renderizar template HTML
        # ---------------------------------------------------------------------
        html_content = render_to_string(
            'emails/lead_customer_confirmation.html',
            context
        )
        text_content = strip_tags(html_content)

        subject = 'Hemos recibido tu solicitud - Arynstal'

        # ---------------------------------------------------------------------
        # Crear y enviar email
        # ---------------------------------------------------------------------
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[lead.email],  # Email del cliente
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            f'Confirmación enviada al cliente {lead.email} para Lead {lead.id}'
        )
        return True

    except Exception as e:
        logger.error(
            f'Error enviando confirmación al cliente para Lead {lead.id}: {e}'
        )
        return False


# =============================================================================
# FUNCIÓN PRINCIPAL: NOTIFICAR NUEVO LEAD
# =============================================================================

def notify_new_lead(lead) -> dict:
    """
    Función orquestadora para notificar sobre un nuevo lead.

    DESCRIPCIÓN:
        Punto de entrada único para el sistema de notificaciones.
        Coordina el envío de todas las notificaciones relacionadas
        con un nuevo lead.

    PARÁMETROS:
        lead (Lead): Instancia del modelo Lead recién creado.

    RETORNA:
        dict: Resultado de cada notificación con estructura:
            {
                'admin_notified': bool,      # Email al admin enviado
                'customer_confirmed': bool,  # Email al cliente enviado
            }

    FLUJO:
        1. Llamar a send_admin_notification()
        2. Llamar a send_customer_confirmation()
        3. Retornar resultados agregados

    EJEMPLO DE USO EN VISTA:
        >>> lead = form.save()
        >>> results = notify_new_lead(lead)
        >>> if results['admin_notified']:
        >>>     messages.success(request, 'Notificación enviada')

    VENTAJAS DE ESTA ARQUITECTURA:
        - Punto único de entrada: Facilita testing y mantenimiento
        - Desacoplamiento: Las funciones individuales son independientes
        - Extensibilidad: Fácil añadir más notificaciones (SMS, Slack, etc.)
        - Visibilidad: El resultado permite saber qué se envió
    """
    results = {
        'admin_notified': False,
        'customer_confirmed': False,
    }

    # -------------------------------------------------------------------------
    # Enviar notificación al administrador
    # -------------------------------------------------------------------------
    results['admin_notified'] = send_admin_notification(lead)

    # -------------------------------------------------------------------------
    # Enviar confirmación al cliente
    # -------------------------------------------------------------------------
    results['customer_confirmed'] = send_customer_confirmation(lead)

    return results
