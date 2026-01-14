from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Muestra el perfil de usuario inline en la página de edición de User.
    """
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil de Arynstal'
    verbose_name_plural = 'Perfil de Arynstal'
    fields = ('role', 'phone')


class UserAdmin(BaseUserAdmin):
    """
    Extiende el admin de User para incluir el perfil inline.
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role_badge', 'assigned_leads_count')
    list_filter = BaseUserAdmin.list_filter + ('profile__role',)

    def get_inline_instances(self, request, obj=None):
        """
        Solo muestra el inline del perfil durante la EDICIÓN, no durante la CREACIÓN.
        Esto evita conflictos con el signal que crea automáticamente el UserProfile.
        """
        if obj is None:
            # obj es None cuando estamos CREANDO un usuario nuevo
            return []
        # Si obj existe, estamos EDITANDO, mostrar el inline
        return super().get_inline_instances(request, obj)

    def role_badge(self, obj):
        """Muestra el rol del usuario con un badge de color"""
        if hasattr(obj, 'profile'):
            colors = {
                'admin': '#7C3AED',      # Púrpura
                'office': '#3B82F6',     # Azul
                'field': '#10B981',      # Verde
            }
            color = colors.get(obj.profile.role, '#6B7280')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
                color,
                obj.profile.get_role_display()
            )
        return mark_safe('<span style="color: #9CA3AF;">Sin perfil</span>')
    role_badge.short_description = 'Rol'

    def assigned_leads_count(self, obj):
        """Muestra el número de leads asignados"""
        count = obj.assigned_leads.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; border-radius: 3px; font-size: 11px;">📋 {}</span>',
                count
            )
        return '-'
    assigned_leads_count.short_description = 'Leads asignados'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('profile').prefetch_related('assigned_leads')
        return queryset

    def save_model(self, request, obj, form, change):
        """
        Guarda el usuario y asegura que tiene un UserProfile.
        """
        super().save_model(request, obj, form, change)
        # El signal ya debería haber creado el perfil, pero por si acaso...
        if not hasattr(obj, 'profile'):
            UserProfile.objects.get_or_create(user=obj)

        # Si es un usuario nuevo, informar al admin que debe configurar el perfil
        if not change:
            from django.contrib import messages
            messages.info(
                request,
                f'Usuario creado correctamente. Edítalo ahora para configurar su rol y teléfono en la sección "Perfil de Arynstal".'
            )


# Desregistrar el admin de User por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Panel de administración para perfiles de usuario (opcional).
    Normalmente se gestionan inline desde User.
    """
    list_display = (
        'user',
        'role_badge',
        'phone',
    )
    list_filter = ('role',)
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone'
    )
    readonly_fields = ('user',)

    def role_badge(self, obj):
        """Muestra el rol con un badge de color"""
        colors = {
            'admin': '#7C3AED',
            'office': '#3B82F6',
            'field': '#10B981',
        }
        color = colors.get(obj.role, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Rol'

    def has_add_permission(self, request):
        """No permitir crear perfiles manualmente (se crean automáticamente con signals)"""
        return False
