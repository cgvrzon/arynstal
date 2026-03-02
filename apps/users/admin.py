"""
===============================================================================
ARCHIVO: apps/users/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configura el panel de administración para usuarios y perfiles.
    Usa django-unfold con doble herencia (UnfoldModelAdmin + BaseUserAdmin)
    para mantener la funcionalidad nativa de auth y el tema moderno.

===============================================================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import StackedInline as UnfoldStackedInline
from unfold.decorators import display

from .models import UserProfile


# =============================================================================
# INLINE: USERPROFILE
# =============================================================================

class UserProfileInline(UnfoldStackedInline):
    """Inline para editar el perfil de Arynstal dentro del User."""
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil de Arynstal'
    verbose_name_plural = 'Perfil de Arynstal'
    fields = ('role', 'phone')


# =============================================================================
# ADMIN: USER (EXTENDIDO CON UNFOLD)
# =============================================================================

class UserAdmin(UnfoldModelAdmin, BaseUserAdmin):
    """
    Admin extendido para User con tema Unfold.

    UnfoldModelAdmin PRIMERO en MRO para que el tema se aplique,
    BaseUserAdmin SEGUNDO para heredar fieldsets, filtros y lógica de auth.
    """

    inlines = (UserProfileInline,)

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL LISTADO
    # -------------------------------------------------------------------------

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'display_role',
        'assigned_leads_count'
    )

    list_filter = BaseUserAdmin.list_filter + ('profile__role',)

    # -------------------------------------------------------------------------
    # GESTIÓN DEL INLINE
    # -------------------------------------------------------------------------

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    # -------------------------------------------------------------------------
    # MÉTODOS DE VISUALIZACIÓN
    # -------------------------------------------------------------------------

    @display(description="Rol", label={
        "admin": "danger",
        "office": "info",
        "field": "success",
    })
    def display_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return None

    def assigned_leads_count(self, obj):
        count = obj.assigned_leads.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">LEADS {}</span>',
                count
            )
        return '-'
    assigned_leads_count.short_description = 'Leads asignados'

    # -------------------------------------------------------------------------
    # OPTIMIZACIÓN
    # -------------------------------------------------------------------------

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('profile').prefetch_related('assigned_leads')

    # -------------------------------------------------------------------------
    # GUARDADO
    # -------------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not hasattr(obj, 'profile'):
            UserProfile.objects.get_or_create(user=obj)

        if not change:
            from django.contrib import messages
            messages.info(
                request,
                f'Usuario creado correctamente. Edítalo ahora para configurar '
                f'su rol y teléfono en la sección "Perfil de Arynstal".'
            )


# =============================================================================
# REGISTRO DEL ADMIN PERSONALIZADO
# =============================================================================

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# =============================================================================
# ADMIN: USERPROFILE (OPCIONAL)
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(UnfoldModelAdmin):
    """Panel de administración independiente para perfiles."""
    list_display = ('user', 'display_role', 'phone')
    list_filter = ('role',)
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone'
    )
    readonly_fields = ('user',)

    @display(description="Rol", label={
        "admin": "danger",
        "office": "info",
        "field": "success",
    })
    def display_role(self, obj):
        return obj.role

    def has_add_permission(self, request):
        return False
