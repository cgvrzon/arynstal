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

    Formulario de creación personalizado que incluye datos personales y rol
    en un solo paso (sin necesidad de editar después).

===============================================================================
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import format_html

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import StackedInline as UnfoldStackedInline
from unfold.decorators import display

from .models import UserProfile


# =============================================================================
# FORMULARIO DE CREACIÓN PERSONALIZADO
# =============================================================================

class ArynstalUserCreationForm(UserCreationForm):
    """
    Extiende UserCreationForm para incluir datos personales y rol
    en el formulario de creación (un solo paso).
    """
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label='Nombre',
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Apellidos',
    )
    email = forms.EmailField(
        required=False,
        label='Email',
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial='field',
        label='Rol en Arynstal',
        help_text='Administrador: acceso total. Oficina: gestión de leads. Técnico: acceso limitado.',
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Teléfono directo',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)


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

    El formulario de creación incluye datos personales y rol en un solo paso.
    """

    add_form = ArynstalUserCreationForm

    add_fieldsets = (
        ('Credenciales', {
            'fields': ('username', 'password1', 'password2'),
            'description': 'Datos de acceso al sistema',
        }),
        ('Información personal', {
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('Rol y contacto', {
            'fields': ('role', 'phone'),
            'description': 'Configuración del perfil de Arynstal',
        }),
    )

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
        if not change:
            # En creación: guardar first_name, last_name, email del form
            obj.first_name = form.cleaned_data.get('first_name', '')
            obj.last_name = form.cleaned_data.get('last_name', '')
            obj.email = form.cleaned_data.get('email', '')
            # Todos los usuarios del admin necesitan is_staff para poder loguearse
            obj.is_staff = True

        super().save_model(request, obj, form, change)

        if not change:
            # Signal ya creó el perfil con rol 'field' por defecto.
            # Actualizamos con los datos del formulario.
            obj.refresh_from_db()
            if hasattr(obj, 'profile'):
                obj.profile.role = form.cleaned_data.get('role', 'field')
                obj.profile.phone = form.cleaned_data.get('phone', '')
                obj.profile.save(update_fields=['role', 'phone'])
            else:
                UserProfile.objects.create(
                    user=obj,
                    role=form.cleaned_data.get('role', 'field'),
                    phone=form.cleaned_data.get('phone', ''),
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
