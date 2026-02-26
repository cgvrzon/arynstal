import logging

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_new_lead_notifications(self, lead_id):
    """Envía notificaciones de nuevo lead (admin + confirmación cliente)."""
    from apps.leads.models import Lead
    from apps.leads.notifications import notify_new_lead

    try:
        lead = Lead.objects.get(pk=lead_id)
    except Lead.DoesNotExist:
        logger.error(f'Lead {lead_id} no encontrado para notificación.')
        return

    try:
        notify_new_lead(lead)
    except Exception as exc:
        logger.error(f'Error notificando Lead {lead_id}: {exc}')
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_lead_assigned_notification(self, lead_id, user_id):
    """Notifica al técnico cuando se le asigna un lead."""
    from apps.leads.models import Lead
    from apps.leads.notifications import notify_lead_assigned

    try:
        lead = Lead.objects.get(pk=lead_id)
        user = User.objects.get(pk=user_id)
    except (Lead.DoesNotExist, User.DoesNotExist) as exc:
        logger.error(f'Lead {lead_id} o User {user_id} no encontrado: {exc}')
        return

    try:
        notify_lead_assigned(lead, user)
    except Exception as exc:
        logger.error(f'Error notificando asignación Lead {lead_id}: {exc}')
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_note_added_notification(self, lead_id, user_id):
    """Notifica a admins cuando un técnico añade nota a un lead."""
    from apps.leads.models import Lead
    from apps.leads.notifications import notify_note_added

    try:
        lead = Lead.objects.get(pk=lead_id)
        user = User.objects.get(pk=user_id)
    except (Lead.DoesNotExist, User.DoesNotExist) as exc:
        logger.error(f'Lead {lead_id} o User {user_id} no encontrado: {exc}')
        return

    try:
        notify_note_added(lead, user)
    except Exception as exc:
        logger.error(f'Error notificando nota en Lead {lead_id}: {exc}')
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def log_unassigned_leads():
    """Loguea leads con status 'nuevo' sin técnico asignado."""
    from apps.leads.models import Lead

    count = Lead.objects.filter(status='nuevo', assigned_to__isnull=True).count()
    if count:
        logger.warning(f'{count} lead(s) sin asignar con status "nuevo".')
    else:
        logger.info('No hay leads sin asignar.')
