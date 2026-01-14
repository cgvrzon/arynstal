from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente un UserProfile cuando se crea un nuevo User.
    Usa get_or_create para evitar conflictos con el inline del admin.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Guarda el UserProfile cuando se guarda el User.
    Si no existe el perfil, lo crea.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Si por alguna razón no existe perfil, lo creamos
        UserProfile.objects.get_or_create(user=instance)
