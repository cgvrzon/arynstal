"""
===============================================================================
ARCHIVO: apps/users/models.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Extiende el modelo User de Django con información específica del negocio.
    Define roles de usuario que determinan los permisos en la aplicación.

FUNCIONES PRINCIPALES:
    - UserProfile: Modelo de extensión del User de Django

FLUJO EN LA APLICACIÓN:
    1. Se crea un User (desde admin o shell)
    2. Signal post_save crea automáticamente UserProfile
    3. Admin edita el perfil para asignar rol
    4. El rol determina qué puede hacer el usuario

SISTEMA DE ROLES:
    - admin: Acceso total a todas las funcionalidades
    - office: Personal de oficina, gestiona leads y presupuestos
    - field: Técnicos de campo, acceso limitado (futuro: app móvil)

PATRÓN DE EXTENSIÓN:
    Django recomienda no modificar el modelo User directamente.
    En su lugar, se usa OneToOneField para extenderlo (UserProfile).
    Esto permite:
    - Mantener compatibilidad con contrib.auth
    - Añadir campos específicos del negocio
    - Acceder fácilmente: user.profile.role

RELACIÓN CON OTROS MODELOS:
    User ←→ UserProfile (1:1)
    User ←── Lead.assigned_to (1:N)
    User ←── Budget.created_by (1:N)
    User ←── LeadLog.user (1:N)

===============================================================================
"""

from django.db import models
from django.contrib.auth.models import User


# =============================================================================
# MODELO: USERPROFILE
# =============================================================================

class UserProfile(models.Model):
    """
    Extensión del modelo User de Django con datos específicos de Arynstal.

    DESCRIPCIÓN:
        Añade información de negocio al User estándar de Django:
        rol del empleado, teléfono directo, etc.

    ROLES DISPONIBLES:
        - admin: Administrador del sistema
          * Acceso total a todas las funcionalidades
          * Puede crear/eliminar usuarios
          * Puede ver estadísticas y configuración

        - office: Personal de oficina
          * Gestiona leads (crear, editar, asignar)
          * Crea y envía presupuestos
          * No puede eliminar datos ni configurar sistema

        - field: Técnico de campo
          * Acceso limitado (preparado para futura app móvil)
          * Ve leads asignados
          * No puede crear presupuestos

    CREACIÓN AUTOMÁTICA:
        El perfil se crea automáticamente mediante signal cuando
        se crea un User (ver signals.py).

    EJEMPLO DE USO:
        >>> user = User.objects.get(username='maria')
        >>> if user.profile.can_manage_leads():
        >>>     # Mostrar opciones de gestión de leads
    """

    # -------------------------------------------------------------------------
    # CONSTANTES - ROLES
    # -------------------------------------------------------------------------

    ROLE_CHOICES = [
        ('admin', 'Administrador'),      # Acceso total
        ('office', 'Oficina'),           # Gestión de leads y presupuestos
        ('field', 'Técnico de campo'),   # Acceso limitado (campo)
    ]

    # -------------------------------------------------------------------------
    # CAMPOS
    # -------------------------------------------------------------------------

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # Si se elimina User, se elimina perfil
        related_name='profile',    # Permite: user.profile
        verbose_name='Usuario'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='field',  # Por defecto, rol más restrictivo
        verbose_name='Rol'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono directo'
        # Teléfono personal del empleado para contacto interno
    )

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN META
    # -------------------------------------------------------------------------

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    # -------------------------------------------------------------------------
    # MÉTODOS
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        """
        Representación en texto del perfil.
        Formato: 'María García - Oficina' o 'admin - Administrador'
        """
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

    # -------------------------------------------------------------------------
    # MÉTODOS DE VERIFICACIÓN DE ROL
    # -------------------------------------------------------------------------
    # Estos métodos encapsulan la lógica de permisos.
    # Usar estos métodos en lugar de comparar directamente con strings.

    def is_admin(self) -> bool:
        """
        Verifica si el usuario tiene rol de administrador.

        RETORNA:
            bool: True si es administrador.
        """
        return self.role == 'admin'

    def is_office(self) -> bool:
        """
        Verifica si el usuario tiene rol de oficina.

        RETORNA:
            bool: True si es personal de oficina.
        """
        return self.role == 'office'

    def is_field(self) -> bool:
        """
        Verifica si el usuario tiene rol de técnico de campo.

        RETORNA:
            bool: True si es técnico de campo.
        """
        return self.role == 'field'

    # -------------------------------------------------------------------------
    # MÉTODOS DE PERMISOS
    # -------------------------------------------------------------------------
    # Encapsulan la lógica de qué roles pueden hacer qué acciones.
    # Facilita cambiar permisos sin modificar código en múltiples lugares.

    def can_manage_leads(self) -> bool:
        """
        Verifica si el usuario puede gestionar leads.

        PERMISOS:
            - admin: Sí
            - office: Sí
            - field: No

        RETORNA:
            bool: True si puede gestionar leads.

        USO:
            >>> if request.user.profile.can_manage_leads():
            >>>     # Mostrar botón de editar lead
        """
        return self.role in ['admin', 'office']

    def can_create_budgets(self) -> bool:
        """
        Verifica si el usuario puede crear presupuestos.

        PERMISOS:
            - admin: Sí
            - office: Sí
            - field: No

        RETORNA:
            bool: True si puede crear presupuestos.
        """
        return self.role in ['admin', 'office']
