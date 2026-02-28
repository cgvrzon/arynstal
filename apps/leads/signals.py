"""
===============================================================================
ARCHIVO: apps/leads/signals.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define los signals (señales) de Django para el modelo Lead.
    Los signals permiten ejecutar código automáticamente cuando
    ocurren eventos en los modelos (crear, guardar, eliminar).

FUNCIONES PRINCIPALES:
    - log_lead_creation: Registra cuando se crea un lead desde la web
    - store_lead_previous_state: Almacena estado antes de guardar
    - log_lead_changes: Detecta y registra cambios en el lead

FLUJO EN LA APLICACIÓN:
    1. Usuario envía formulario web → Lead.save() se ejecuta
    2. pre_save signal almacena estado anterior
    3. post_save signal compara y registra cambios
    4. LeadLog se crea automáticamente con la acción

PATRÓN UTILIZADO:
    Observer Pattern - Los signals actúan como observadores del modelo.
    Cuando el modelo cambia, los observers (receivers) son notificados.

IMPORTANTE - VARIABLE GLOBAL:
    _lead_previous_state es un dict global que almacena el estado
    anterior de los leads entre pre_save y post_save. Esta es una
    limitación de Django que no provee acceso al estado anterior
    directamente en post_save.

    ADVERTENCIA: En entornos multi-proceso (gunicorn con workers),
    esta variable es segura porque cada request se maneja en un
    solo proceso secuencialmente.

RELACIÓN CON OTROS ARCHIVOS:
    - models.py: Define Lead y LeadLog que se usan aquí
    - admin.py: También crea logs (con acceso a request.user)
    - apps.py: Importa este módulo para registrar signals

===============================================================================
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Lead, LeadLog


# =============================================================================
# VARIABLE GLOBAL - ALMACENAMIENTO TEMPORAL DE ESTADO
# =============================================================================
# Almacena el estado anterior del lead entre pre_save y post_save.
# La clave es el PK del lead, el valor es un dict con los campos a monitorear.
#
# CICLO DE VIDA:
#   1. pre_save: Se guarda estado en _lead_previous_state[pk]
#   2. post_save: Se compara y se elimina de _lead_previous_state[pk]
#
# NOTA: Se limpia automáticamente en post_save para evitar memory leaks.

_lead_previous_state = {}


# =============================================================================
# SIGNAL: LOG DE CREACIÓN
# =============================================================================

@receiver(post_save, sender=Lead)
def log_lead_creation(sender, instance, created, **kwargs):
    """
    Crea un registro de auditoría cuando se crea un nuevo lead desde la web.

    CUÁNDO SE EJECUTA:
        Después de cada Lead.save() si el lead es nuevo (created=True).

    PARÁMETROS:
        sender (class): La clase del modelo que envió el signal (Lead).
        instance (Lead): La instancia del lead que se acaba de guardar.
        created (bool): True si es un nuevo registro, False si es actualización.
        **kwargs: Argumentos adicionales del signal (no usados).

    COMPORTAMIENTO:
        - Solo actúa si created=True Y el origen es 'web'
        - Leads creados desde admin tienen su propio log (ver admin.py)
        - Crea un LeadLog con action='created'

    NOTA:
        No se registra el usuario porque desde el formulario web
        no hay usuario autenticado (es anónimo).
    """
    if created and instance.source == 'web':
        LeadLog.objects.create(
            lead=instance,
            action='created',
            new_value=f'Lead creado desde {instance.get_source_display()}'
        )


# =============================================================================
# SIGNAL: ALMACENAR ESTADO ANTERIOR (PRE-SAVE)
# =============================================================================

@receiver(pre_save, sender=Lead)
def store_lead_previous_state(sender, instance, **kwargs):
    """
    Almacena el estado anterior del lead antes de que se guarde.

    CUÁNDO SE EJECUTA:
        Antes de cada Lead.save() si el lead ya existe (tiene PK).

    PARÁMETROS:
        sender (class): La clase del modelo que envió el signal (Lead).
        instance (Lead): La instancia del lead que se va a guardar.
        **kwargs: Argumentos adicionales del signal (no usados).

    PROPÓSITO:
        Django no provee acceso al estado anterior en post_save.
        Este signal captura los valores antes del cambio para
        poder compararlos después en log_lead_changes.

    CAMPOS MONITOREADOS:
        - status: Estado del lead (nuevo, contactado, etc.)
        - assigned_to: Usuario asignado al lead

    FLUJO:
        1. Verificar que el lead existe (tiene PK)
        2. Cargar el estado actual desde la BD
        3. Guardar en _lead_previous_state[pk]
        4. post_save usará estos datos y limpiará el dict

    NOTA - GUARDADO DESDE ADMIN:
        Si el save proviene del admin (._logging_handled_in_admin),
        no almacenamos estado: el admin ya crea los LeadLog en
        save_model con request.user. Así evitamos logs duplicados.
    """
    if getattr(instance, '_logging_handled_in_admin', False):
        return
    if instance.pk:
        try:
            # Obtener el estado actual desde la BD (antes del cambio)
            old_instance = Lead.objects.get(pk=instance.pk)
            _lead_previous_state[instance.pk] = {
                'status': old_instance.status,
                'assigned_to': old_instance.assigned_to,
            }
        except Lead.DoesNotExist:
            # Caso edge: el lead fue eliminado entre la carga y el save
            pass


# =============================================================================
# SIGNAL: DETECTAR Y REGISTRAR CAMBIOS (POST-SAVE)
# =============================================================================

@receiver(post_save, sender=Lead)
def log_lead_changes(sender, instance, created, **kwargs):
    """
    Registra automáticamente los cambios realizados en el lead.

    CUÁNDO SE EJECUTA:
        Después de cada Lead.save() si es una actualización (created=False).

    PARÁMETROS:
        sender (class): La clase del modelo que envió el signal (Lead).
        instance (Lead): La instancia del lead recién guardada.
        created (bool): True si es nuevo, False si es actualización.
        **kwargs: Argumentos adicionales del signal (no usados).

    CAMBIOS DETECTADOS:
        1. Cambio de estado (status_changed)
           - Ejemplo: nuevo → contactado
        2. Cambio de asignación (assigned)
           - Ejemplo: Sin asignar → María García

    FLUJO:
        1. Si es nuevo (created=True), salir (log_lead_creation se encarga)
        2. Verificar si hay estado anterior almacenado
        3. Comparar status: si cambió, crear LeadLog
        4. Comparar assigned_to: si cambió, crear LeadLog
        5. Limpiar _lead_previous_state para evitar memory leak

    NOTA SOBRE USUARIO:
        Este signal no tiene acceso a request.user porque se ejecuta
        a nivel de modelo. Los logs creados desde admin.py sí tienen
        el usuario porque se usa save_model() con acceso al request.
    """
    # No procesar leads nuevos (ya se manejan en log_lead_creation)
    if not created and instance.pk in _lead_previous_state:
        old_state = _lead_previous_state[instance.pk]

        # ---------------------------------------------------------------------
        # Detectar cambio de estado
        # ---------------------------------------------------------------------
        if old_state['status'] != instance.status:
            LeadLog.objects.create(
                lead=instance,
                action='status_changed',
                old_value=dict(Lead.STATUS_CHOICES).get(old_state['status']),
                new_value=instance.get_status_display()
            )

        # ---------------------------------------------------------------------
        # Detectar cambio de asignación
        # ---------------------------------------------------------------------
        if old_state['assigned_to'] != instance.assigned_to:
            LeadLog.objects.create(
                lead=instance,
                action='assigned',
                old_value=str(old_state['assigned_to']) if old_state['assigned_to'] else 'Sin asignar',
                new_value=str(instance.assigned_to) if instance.assigned_to else 'Sin asignar'
            )

        # ---------------------------------------------------------------------
        # Limpiar estado almacenado (evitar memory leak)
        # ---------------------------------------------------------------------
        del _lead_previous_state[instance.pk]
