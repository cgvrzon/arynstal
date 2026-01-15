"""
Sistema de notificaciones por email para leads.

FASE 9: Notificaciones automáticas cuando se crea un nuevo lead.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def get_notification_config():
    """Obtiene la configuración de notificaciones."""
    return settings.NOTIFICATIONS.get('LEAD', {})


def send_admin_notification(lead):
    """
    Envía notificación al administrador cuando se crea un nuevo lead.

    Args:
        lead: Instancia del modelo Lead

    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    config = get_notification_config()

    if not config.get('ENABLED', True):
        logger.info(f'Notificaciones deshabilitadas. Lead {lead.id} no notificado.')
        return False

    admin_email = config.get('ADMIN_EMAIL', 'info@arynstal.es')

    context = {
        'lead': lead,
        'lead_url': f'/admin/leads/lead/{lead.id}/change/',
    }

    try:
        # Renderizar templates
        html_content = render_to_string('emails/lead_admin_notification.html', context)
        text_content = strip_tags(html_content)

        subject = f'🔔 Nuevo contacto: {lead.name}'

        # Crear email con versión HTML y texto plano
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            to=[admin_email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(f'Notificación de admin enviada para Lead {lead.id} a {admin_email}')
        return True

    except Exception as e:
        logger.error(f'Error enviando notificación de admin para Lead {lead.id}: {e}')
        return False


def send_customer_confirmation(lead):
    """
    Envía confirmación al cliente cuando se recibe su solicitud.

    Args:
        lead: Instancia del modelo Lead

    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    config = get_notification_config()

    if not config.get('ENABLED', True):
        return False

    if not config.get('SEND_CUSTOMER_CONFIRMATION', True):
        logger.info(f'Confirmación al cliente deshabilitada. Lead {lead.id} no confirmado.')
        return False

    context = {
        'lead': lead,
    }

    try:
        # Renderizar templates
        html_content = render_to_string('emails/lead_customer_confirmation.html', context)
        text_content = strip_tags(html_content)

        subject = 'Hemos recibido tu solicitud - Arynstal'

        # Crear email con versión HTML y texto plano
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            to=[lead.email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(f'Confirmación enviada al cliente {lead.email} para Lead {lead.id}')
        return True

    except Exception as e:
        logger.error(f'Error enviando confirmación al cliente para Lead {lead.id}: {e}')
        return False


def notify_new_lead(lead):
    """
    Función principal para notificar sobre un nuevo lead.
    Envía tanto la notificación al admin como la confirmación al cliente.

    Args:
        lead: Instancia del modelo Lead

    Returns:
        dict: Resultado de cada notificación
    """
    results = {
        'admin_notified': False,
        'customer_confirmed': False,
    }

    # Notificación al admin
    results['admin_notified'] = send_admin_notification(lead)

    # Confirmación al cliente
    results['customer_confirmed'] = send_customer_confirmation(lead)

    return results
