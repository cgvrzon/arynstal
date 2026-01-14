from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Lead, LeadLog


@receiver(post_save, sender=Lead)
def log_lead_creation(sender, instance, created, **kwargs):
    """
    Crea un log cuando se crea un nuevo lead desde el formulario web.
    """
    if created and instance.source == 'web':
        LeadLog.objects.create(
            lead=instance,
            action='created',
            new_value=f'Lead creado desde {instance.get_source_display()}'
        )


# Variable global para almacenar el estado anterior del lead
_lead_previous_state = {}


@receiver(pre_save, sender=Lead)
def store_lead_previous_state(sender, instance, **kwargs):
    """
    Almacena el estado anterior del lead antes de guardarlo.
    """
    if instance.pk:
        try:
            old_instance = Lead.objects.get(pk=instance.pk)
            _lead_previous_state[instance.pk] = {
                'status': old_instance.status,
                'assigned_to': old_instance.assigned_to,
            }
        except Lead.DoesNotExist:
            pass


@receiver(post_save, sender=Lead)
def log_lead_changes(sender, instance, created, **kwargs):
    """
    Registra automáticamente los cambios en el lead.
    """
    if not created and instance.pk in _lead_previous_state:
        old_state = _lead_previous_state[instance.pk]

        # Detectar cambio de estado
        if old_state['status'] != instance.status:
            LeadLog.objects.create(
                lead=instance,
                action='status_changed',
                old_value=dict(Lead.STATUS_CHOICES).get(old_state['status']),
                new_value=instance.get_status_display()
            )

        # Detectar cambio de asignación
        if old_state['assigned_to'] != instance.assigned_to:
            LeadLog.objects.create(
                lead=instance,
                action='assigned',
                old_value=str(old_state['assigned_to']) if old_state['assigned_to'] else 'Sin asignar',
                new_value=str(instance.assigned_to) if instance.assigned_to else 'Sin asignar'
            )

        # Limpiar el estado almacenado
        del _lead_previous_state[instance.pk]
