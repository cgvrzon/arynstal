"""
===============================================================================
ARCHIVO: apps/users/notifications.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Sistema de notificaciones email para el módulo de usuarios.
    Gestiona el envío de emails de bienvenida con link de activación
    y alertas de intentos de login fallidos.

FUNCIONES PRINCIPALES:
    - send_welcome_email: Email de bienvenida con link de activación
    - send_failed_login_alert: Alerta al admin por intentos fallidos

PATRÓN:
    Replica el patrón de apps/leads/notifications.py:
    EmailMultiAlternatives, try/except, return bool, logger.

===============================================================================
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.signing import TimestampSigner
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Signer con salt único para tokens de activación
ACTIVATION_SIGNER = TimestampSigner(salt='user-account-activation')


# =============================================================================
# FUNCIÓN AUXILIAR: OBTENER CONFIGURACIÓN
# =============================================================================

def get_user_notification_config() -> dict:
    """Obtiene la configuración de notificaciones de usuario desde settings."""
    return settings.NOTIFICATIONS.get('USER', {})


def _parse_admin_emails(config: dict) -> list[str]:
    """Extrae la lista de emails de administrador desde la configuración."""
    raw = config.get('ADMIN_EMAILS') or config.get('ADMIN_EMAIL', '')

    if isinstance(raw, (list, tuple)):
        emails = raw
    else:
        emails = raw.split(',')

    return [e.strip() for e in emails if e.strip()]


# =============================================================================
# FUNCIÓN AUXILIAR: GENERAR TOKEN DE ACTIVACIÓN
# =============================================================================

def generate_activation_token(user) -> str:
    """
    Genera un token firmado para activación de cuenta.

    Usa TimestampSigner de Django con salt único. El token incluye
    el user.pk firmado, y se valida con max_age en la vista.
    No requiere almacenamiento en BD.
    """
    return ACTIVATION_SIGNER.sign(str(user.pk))


# =============================================================================
# FUNCIÓN: EMAIL DE BIENVENIDA CON ACTIVACIÓN
# =============================================================================

def send_welcome_email(user) -> bool:
    """
    Envía email de bienvenida con link de activación al nuevo usuario.

    PARÁMETROS:
        user (User): Instancia del usuario recién creado.

    RETORNA:
        bool: True si el email se envió correctamente, False si falló.

    FLUJO:
        1. Verificar que el usuario tiene email
        2. Generar token de activación firmado
        3. Construir URL de activación
        4. Renderizar template HTML
        5. Enviar email
    """
    config = get_user_notification_config()

    if not config.get('WELCOME_EMAIL_ENABLED', True):
        logger.info(
            f'Email de bienvenida deshabilitado. Usuario {user.username} no notificado.'
        )
        return False

    if not user.email:
        logger.warning(
            f'Usuario {user.username} sin email. '
            f'No se puede enviar email de bienvenida.'
        )
        return False

    token = generate_activation_token(user)
    base = getattr(settings, 'COMPANY_INFO', {}).get('WEBSITE', '').rstrip('/')
    activation_url = f'{base}/account/activate/{token}/'
    resend_url = f'{base}/account/request-activation/'

    context = {
        'user': user,
        'activation_url': activation_url,
        'resend_url': resend_url,
        'expiry_hours': config.get('ACTIVATION_TOKEN_HOURS', 48),
    }

    try:
        html_content = render_to_string(
            'emails/user_welcome_activation.html',
            context,
        )
        text_content = strip_tags(html_content)

        subject = f'Bienvenido a Arynstal - Activa tu cuenta'

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[user.email],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            f'Email de bienvenida enviado a {user.email} (usuario: {user.username})'
        )
        return True

    except Exception as e:
        logger.error(
            f'Error enviando email de bienvenida a {user.username}: {e}'
        )
        return False


# =============================================================================
# FUNCIÓN: ALERTA DE INTENTOS DE LOGIN FALLIDOS
# =============================================================================

def send_failed_login_alert(username, ip_address, attempt_count, path='') -> bool:
    """
    Envía alerta al admin cuando se alcanza el umbral de intentos fallidos.

    PARÁMETROS:
        username (str): Nombre de usuario que se intentó.
        ip_address (str): IP desde la que se intentó.
        attempt_count (int): Número de intentos en la ventana temporal.
        path (str): URL del panel donde se intentó.

    RETORNA:
        bool: True si el email se envió correctamente, False si falló.
    """
    config = get_user_notification_config()

    if not config.get('FAILED_LOGIN_ALERT_ENABLED', True):
        logger.info(
            f'Alerta de login fallido deshabilitada. '
            f'{attempt_count} intentos para "{username}" no notificados.'
        )
        return False

    admin_emails = _parse_admin_emails(config)
    if not admin_emails:
        admin_emails = ['admin@arynstal.es']

    context = {
        'username': username,
        'ip_address': ip_address,
        'attempt_count': attempt_count,
        'path': path,
    }

    try:
        html_content = render_to_string(
            'emails/failed_login_alert.html',
            context,
        )
        text_content = strip_tags(html_content)

        subject = f'Alerta: {attempt_count} intentos de login fallidos para "{username}"'

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=admin_emails,
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

        logger.info(
            f'Alerta de login fallido enviada a {admin_emails} '
            f'({attempt_count} intentos para "{username}" desde {ip_address})'
        )
        return True

    except Exception as e:
        logger.error(
            f'Error enviando alerta de login fallido para "{username}": {e}'
        )
        return False
