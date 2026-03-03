import logging

from django.contrib.auth.models import User
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from .notifications import ACTIVATION_SIGNER, send_welcome_email

logger = logging.getLogger(__name__)


# =============================================================================
# HELPER: URL DE LOGIN SEGÚN ROL
# =============================================================================

def _get_login_url_for_user(user) -> str:
    """
    Devuelve la URL de login del panel correspondiente al rol del usuario.

    - admin → /admynstal/login/
    - office, field → /offynstal/login/
    - Sin perfil (fallback) → /offynstal/login/
    """
    if hasattr(user, 'profile') and user.profile.role == 'admin':
        return '/admynstal/login/'
    return '/offynstal/login/'


# =============================================================================
# VISTA: ACTIVAR CUENTA
# =============================================================================

def activate_account(request, token):
    """
    Activa la cuenta de un usuario verificando el token firmado.

    FLUJO:
        1. Decodifica y verifica el token con TimestampSigner
        2. Valida que no haya expirado (max_age configurable, default 48h)
        3. Busca el usuario por pk
        4. Activa la cuenta (is_active=True)
        5. Renderiza template de éxito con link al login según rol
    """
    user_config = settings.NOTIFICATIONS.get('USER', {})
    max_age_hours = user_config.get('ACTIVATION_TOKEN_HOURS', 48)
    max_age_seconds = max_age_hours * 3600

    try:
        user_pk = ACTIVATION_SIGNER.unsign(token, max_age=max_age_seconds)
        user = User.objects.select_related('profile').get(pk=user_pk)

        login_url = _get_login_url_for_user(user)

        if user.is_active:
            return render(request, 'pages/activation_success.html', {
                'user': user,
                'login_url': login_url,
                'already_active': True,
            })

        user.is_active = True
        user.save(update_fields=['is_active'])
        logger.info(f'Cuenta activada: {user.username} (pk={user.pk})')

        return render(request, 'pages/activation_success.html', {
            'user': user,
            'login_url': login_url,
            'already_active': False,
        })

    except SignatureExpired:
        logger.warning(f'Token de activación expirado: {token[:20]}...')
        return render(request, 'pages/activation_error.html', {
            'error': 'expired',
            'message': (
                f'El enlace de activación ha expirado (válido {max_age_hours}h). '
                'Puedes solicitar uno nuevo con tus credenciales.'
            ),
            'resend_url': '/account/request-activation/',
        }, status=400)

    except (BadSignature, User.DoesNotExist):
        logger.warning(f'Token de activación inválido: {token[:20]}...')
        return render(request, 'pages/activation_error.html', {
            'error': 'invalid',
            'message': (
                'El enlace de activación no es válido. '
                'Contacta con el administrador.'
            ),
        }, status=400)


# =============================================================================
# VISTA: SOLICITAR REENVÍO DE ACTIVACIÓN
# =============================================================================

@ratelimit(key='ip', rate='5/h', method='POST', block=False)
def request_activation(request):
    """
    Permite a un usuario con cuenta inactiva solicitar un nuevo email
    de activación introduciendo sus credenciales (username + password).

    Usa check_password() directamente porque authenticate() de Django
    rechaza usuarios con is_active=False.
    """
    context = {}

    if request.method == 'POST':
        # Rate limit check
        if getattr(request, 'limited', False):
            context['error'] = (
                'Demasiadas solicitudes. Inténtalo de nuevo más tarde.'
            )
            return render(request, 'pages/request_activation.html', context)

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Mensaje genérico para no enumerar usuarios
        generic_error = 'Credenciales incorrectas. Verifica tu usuario y contraseña.'

        if not username or not password:
            context['error'] = generic_error
            return render(request, 'pages/request_activation.html', context)

        try:
            user = User.objects.select_related('profile').get(username=username)
        except User.DoesNotExist:
            context['error'] = generic_error
            return render(request, 'pages/request_activation.html', context)

        if not user.check_password(password):
            context['error'] = generic_error
            return render(request, 'pages/request_activation.html', context)

        # Credenciales válidas
        if user.is_active:
            login_url = _get_login_url_for_user(user)
            context['info'] = 'Tu cuenta ya está activa. Puedes iniciar sesión.'
            context['login_url'] = login_url
            return render(request, 'pages/request_activation.html', context)

        # Cuenta inactiva → reenviar email de activación
        if not user.email:
            context['error'] = (
                'Tu cuenta no tiene email asociado. Contacta con el administrador.'
            )
            return render(request, 'pages/request_activation.html', context)

        sent = send_welcome_email(user)
        if sent:
            context['success'] = (
                f'Se ha enviado un nuevo email de activación a {user.email}. '
                'Revisa tu bandeja de entrada.'
            )
            logger.info(
                f'Reenvío de activación solicitado: {user.username} → {user.email}'
            )
        else:
            context['error'] = (
                'No se pudo enviar el email. Inténtalo de nuevo más tarde '
                'o contacta con el administrador.'
            )

    return render(request, 'pages/request_activation.html', context)
