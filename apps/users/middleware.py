"""
===============================================================================
ARCHIVO: apps/users/middleware.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Middleware para configurar expiración de sesión según el rol del usuario.
    Debe ir DESPUÉS de AuthenticationMiddleware en settings.MIDDLEWARE.

===============================================================================
"""

from django.conf import settings


class RoleSessionExpiryMiddleware:
    """
    Configura la expiración de sesión según el rol del usuario.

    FUNCIONAMIENTO:
        - Lee el rol del usuario autenticado
        - Aplica set_expiry() con la duración correspondiente
        - Usa flag _role_expiry_set para no recalcular en cada request

    CONFIGURACIÓN (settings.SESSION_SECURITY):
        ADMIN_SESSION_DURATION: segundos para admin (default 8h)
        OFFICE_SESSION_DURATION: segundos para office (default 4h)
        FIELD_SESSION_DURATION: segundos para field (default 2h)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.session.get('_role_expiry_set')
        ):
            session_config = getattr(settings, 'SESSION_SECURITY', {})

            duration_map = {
                'admin': session_config.get('ADMIN_SESSION_DURATION', 8 * 3600),
                'office': session_config.get('OFFICE_SESSION_DURATION', 4 * 3600),
                'field': session_config.get('FIELD_SESSION_DURATION', 2 * 3600),
            }

            role = getattr(getattr(request.user, 'profile', None), 'role', None)
            duration = duration_map.get(role, session_config.get('FIELD_SESSION_DURATION', 2 * 3600))

            request.session.set_expiry(duration)
            request.session['_role_expiry_set'] = True

        return self.get_response(request)
