from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extensión del User de Django para añadir información específica del negocio.
    Roles: admin (acceso total), office (gestión de leads), field (técnicos).
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('office', 'Oficina'),
        ('field', 'Técnico de campo'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='field',
        verbose_name='Rol'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono directo'
    )

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == 'admin'

    def is_office(self):
        """Verifica si el usuario es de oficina"""
        return self.role == 'office'

    def is_field(self):
        """Verifica si el usuario es técnico de campo"""
        return self.role == 'field'

    def can_manage_leads(self):
        """Verifica si puede gestionar leads"""
        return self.role in ['admin', 'office']

    def can_create_budgets(self):
        """Verifica si puede crear presupuestos"""
        return self.role in ['admin', 'office']
