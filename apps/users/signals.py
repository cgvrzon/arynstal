"""
===============================================================================
ARCHIVO: apps/users/signals.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define el signal para la creación automática de UserProfile
    cuando se crea un nuevo User.

FUNCIONES PRINCIPALES:
    - create_user_profile: Crea perfil automáticamente al crear User

FLUJO EN LA APLICACIÓN:
    1. Se crea un User (desde admin, shell o cualquier método)
    2. Django dispara signal post_save
    3. create_user_profile() se ejecuta
    4. Se crea UserProfile con valores por defecto
    5. El admin puede editar el perfil después

PATRÓN UTILIZADO:
    Observer Pattern - El signal observa la creación de Users
    y reacciona creando el perfil asociado automáticamente.

IMPORTANTE - get_or_create:
    Usamos get_or_create en lugar de create para evitar errores
    de integridad si el perfil ya existe (posible en race conditions
    o si el inline del admin ya lo creó).

RELACIÓN CON OTROS ARCHIVOS:
    - models.py: Define UserProfile que se crea aquí
    - admin.py: Usa get_or_create como fallback adicional
    - apps.py: Importa este módulo para registrar el signal

===============================================================================
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import LoginAttempt, UserProfile

logger = logging.getLogger(__name__)


# =============================================================================
# SIGNAL: CREACIÓN AUTOMÁTICA DE PERFIL
# =============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente un UserProfile cuando se crea un nuevo User.

    Usa get_or_create para evitar duplicados si el inline del admin
    ya creó el perfil antes que este signal.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


# =============================================================================
# SIGNAL: REGISTRO DE LOGIN FALLIDO
# =============================================================================

def _get_client_ip(request) -> str:
    """Extrae IP real del cliente (mismo patrón que web/views.py)."""
    if request is None:
        return '0.0.0.0'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Registra cada intento de login fallido y alerta al admin al cruzar umbral.

    FLUJO:
        1. Extrae username, IP, user-agent y path del request
        2. Crea registro LoginAttempt
        3. Cuenta intentos en la ventana temporal (1h por defecto)
        4. Si count == threshold: envía alerta email (solo una vez al cruzar)
    """
    username = credentials.get('username', '')

    if request is None:
        ip = '0.0.0.0'
        user_agent = ''
        path = ''
    else:
        ip = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        path = request.path

    LoginAttempt.objects.create(
        username=username,
        ip_address=ip,
        user_agent=user_agent,
        path=path,
    )

    logger.warning(
        f'Login fallido: usuario="{username}" ip={ip} path={path}'
    )

    # Verificar umbral para alerta
    user_config = settings.NOTIFICATIONS.get('USER', {})
    threshold = user_config.get('FAILED_LOGIN_THRESHOLD', 5)
    window_minutes = user_config.get('FAILED_LOGIN_WINDOW_MINUTES', 60)

    window_start = timezone.now() - timedelta(minutes=window_minutes)

    recent_count = LoginAttempt.objects.filter(
        ip_address=ip,
        timestamp__gte=window_start,
    ).count()

    # Solo alertar cuando se cruza el umbral exacto (evita spam de alertas)
    if recent_count == threshold:
        from .notifications import send_failed_login_alert

        send_failed_login_alert(
            username=username,
            ip_address=ip,
            attempt_count=recent_count,
            path=path,
        )
