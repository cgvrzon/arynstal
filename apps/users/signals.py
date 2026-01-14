from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente un UserProfile cuando se crea un nuevo User.
    Usa get_or_create para evitar conflictos con el inline del admin.

    NOTA: No necesitamos signal para 'save' porque Django maneja
    automáticamente el guardado de modelos relacionados (inline).
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
