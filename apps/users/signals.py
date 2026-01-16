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

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


# =============================================================================
# SIGNAL: CREACIÓN AUTOMÁTICA DE PERFIL
# =============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente un UserProfile cuando se crea un nuevo User.

    CUÁNDO SE EJECUTA:
        Después de cada User.save() si el usuario es nuevo (created=True).

    PARÁMETROS:
        sender (class): La clase del modelo que envió el signal (User).
        instance (User): La instancia del usuario que se acaba de guardar.
        created (bool): True si es un nuevo registro, False si es actualización.
        **kwargs: Argumentos adicionales del signal (no usados).

    COMPORTAMIENTO:
        - Solo actúa cuando created=True (usuario nuevo)
        - Usa get_or_create para evitar duplicados
        - El perfil se crea con valores por defecto (role='field')

    VALORES POR DEFECTO DEL PERFIL:
        - role: 'field' (técnico de campo - rol más restrictivo)
        - phone: '' (vacío)

    NOTA SOBRE get_or_create:
        Usamos get_or_create en lugar de create porque:
        1. El inline del admin podría crear el perfil antes
        2. Evita IntegrityError en race conditions
        3. Es idempotente (seguro de ejecutar múltiples veces)

    FLUJO TÍPICO:
        1. Admin crea usuario desde /gestion-interna/auth/user/add/
        2. User.save() se ejecuta
        3. Este signal se dispara
        4. Se crea UserProfile con role='field'
        5. Admin puede editar el perfil para cambiar el rol
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
