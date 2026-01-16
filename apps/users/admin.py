"""
===============================================================================
ARCHIVO: apps/users/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configura el panel de administración para usuarios y perfiles.
    Extiende el UserAdmin de Django para incluir el perfil de Arynstal
    como inline, permitiendo editar rol y teléfono desde la misma página.

FUNCIONES PRINCIPALES:
    - UserAdmin: Admin extendido con perfil inline y badges
    - UserProfileAdmin: Admin separado para perfiles (opcional)
    - UserProfileInline: Inline para editar perfil dentro de User

FLUJO EN LA APLICACIÓN:
    1. Admin accede a /gestion-interna/auth/user/
    2. Ve listado de usuarios con roles y leads asignados
    3. Al crear usuario, signal crea el perfil automáticamente
    4. Admin edita usuario y configura rol en sección "Perfil de Arynstal"

INTEGRACIÓN CON DJANGO AUTH:
    - Desregistra el UserAdmin por defecto
    - Registra versión extendida con inline de perfil
    - Mantiene toda la funcionalidad original (contraseñas, permisos, etc.)

===============================================================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import UserProfile


# =============================================================================
# INLINE: USERPROFILE
# =============================================================================

class UserProfileInline(admin.StackedInline):
    """
    Inline para editar el perfil de Arynstal dentro del User.

    DESCRIPCIÓN:
        Muestra los campos de UserProfile (rol, teléfono) en la
        página de edición del User, evitando navegar a otro modelo.

    CARACTERÍSTICAS:
        - Formato StackedInline (campos apilados, no en tabla)
        - No permite eliminar el perfil
        - Solo se muestra en edición, no en creación

    NOTA:
        El perfil se crea automáticamente via signal, por eso
        no se muestra durante la creación del usuario.
    """
    model = UserProfile
    can_delete = False  # No permitir eliminar el perfil
    verbose_name = 'Perfil de Arynstal'
    verbose_name_plural = 'Perfil de Arynstal'
    fields = ('role', 'phone')


# =============================================================================
# ADMIN: USER (EXTENDIDO)
# =============================================================================

class UserAdmin(BaseUserAdmin):
    """
    Admin extendido para el modelo User de Django.

    DESCRIPCIÓN:
        Extiende el UserAdmin por defecto para incluir:
        - Inline del perfil de Arynstal
        - Badge visual del rol en el listado
        - Contador de leads asignados
        - Filtro por rol

    CARACTERÍSTICAS:
        - Hereda toda la funcionalidad de BaseUserAdmin
        - Añade inline de UserProfile
        - Optimiza queries para evitar N+1
        - Maneja la creación de perfil automática

    NOTA SOBRE CREACIÓN:
        Al crear un usuario, el inline NO se muestra para evitar
        conflictos con el signal que crea el perfil. Después de
        guardar, se muestra un mensaje indicando que debe editar
        el usuario para configurar su rol.
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
        'role_badge',              # Badge visual del rol
        'assigned_leads_count'     # Contador de leads asignados
    )

    # Añadir filtro por rol a los filtros existentes
    list_filter = BaseUserAdmin.list_filter + ('profile__role',)

    # -------------------------------------------------------------------------
    # GESTIÓN DEL INLINE
    # -------------------------------------------------------------------------

    def get_inline_instances(self, request, obj=None):
        """
        Controla cuándo mostrar el inline del perfil.

        PROPÓSITO:
            Evitar conflictos entre el inline y el signal que crea
            el perfil automáticamente al crear un usuario.

        LÓGICA:
            - Si obj es None → Creación → No mostrar inline
            - Si obj existe → Edición → Mostrar inline

        PARÁMETROS:
            request: Request HTTP
            obj: Instancia del User o None si es creación

        RETORNA:
            list: Lista de inlines a mostrar (vacía en creación)
        """
        if obj is None:
            # Estamos CREANDO un usuario nuevo, no mostrar inline
            return []
        # Estamos EDITANDO, mostrar el inline
        return super().get_inline_instances(request, obj)

    # -------------------------------------------------------------------------
    # MÉTODOS DE VISUALIZACIÓN
    # -------------------------------------------------------------------------

    def role_badge(self, obj) -> str:
        """
        Genera badge de color según el rol del usuario.

        PARÁMETROS:
            obj (User): Instancia del usuario.

        RETORNA:
            str: HTML con badge coloreado o 'Sin perfil'.

        COLORES:
            - admin: Púrpura (#7C3AED)
            - office: Azul (#3B82F6)
            - field: Verde (#10B981)
        """
        if hasattr(obj, 'profile'):
            colors = {
                'admin': '#7C3AED',
                'office': '#3B82F6',
                'field': '#10B981',
            }
            color = colors.get(obj.profile.role, '#6B7280')
            return format_html(
                '<span style="background-color: {}; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold; '
                'font-size: 11px;">{}</span>',
                color,
                obj.profile.get_role_display()
            )
        return mark_safe('<span style="color: #9CA3AF;">Sin perfil</span>')
    role_badge.short_description = 'Rol'

    def assigned_leads_count(self, obj) -> str:
        """
        Muestra el número de leads asignados al usuario.

        PARÁMETROS:
            obj (User): Instancia del usuario.

        RETORNA:
            str: Badge con contador o guión si no tiene leads.

        PROPÓSITO:
            Permite ver la carga de trabajo de cada empleado.
        """
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
        """
        Optimiza las consultas precargando relaciones.

        OPTIMIZACIONES:
            - select_related('profile'): Para role_badge
            - prefetch_related('assigned_leads'): Para contador

        RETORNA:
            QuerySet: Usuarios con relaciones precargadas.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('profile').prefetch_related('assigned_leads')

    # -------------------------------------------------------------------------
    # GUARDADO
    # -------------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        """
        Guarda el usuario y asegura que tiene perfil.

        PROPÓSITO:
            Garantizar que todo usuario tenga un UserProfile,
            incluso si el signal falló por alguna razón.

        FLUJO:
            1. Guardar el usuario (padre)
            2. Verificar si tiene perfil (signal debería haberlo creado)
            3. Si no tiene, crear uno con valores por defecto
            4. Si es usuario nuevo, mostrar mensaje informativo

        PARÁMETROS:
            request: Request HTTP
            obj (User): Usuario a guardar
            form: Formulario con los datos
            change (bool): True si es edición, False si es creación
        """
        super().save_model(request, obj, form, change)

        # Asegurar que existe el perfil (por si acaso)
        if not hasattr(obj, 'profile'):
            UserProfile.objects.get_or_create(user=obj)

        # Mensaje informativo para usuarios nuevos
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
# Reemplazar el UserAdmin por defecto de Django con nuestra versión extendida

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# =============================================================================
# ADMIN: USERPROFILE (OPCIONAL)
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Panel de administración independiente para perfiles.

    DESCRIPCIÓN:
        Permite gestionar perfiles de forma separada del User.
        El uso principal es desde el inline en UserAdmin,
        este admin es complementario para casos especiales.

    CARACTERÍSTICAS:
        - No permite crear perfiles manualmente
        - Útil para búsquedas y listados de roles
        - Usuario en solo lectura (se gestiona desde User)
    """
    list_display = ('user', 'role_badge', 'phone')
    list_filter = ('role',)
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone'
    )
    readonly_fields = ('user',)  # No cambiar el usuario asociado

    def role_badge(self, obj) -> str:
        """Genera badge de color según el rol."""
        colors = {
            'admin': '#7C3AED',
            'office': '#3B82F6',
            'field': '#10B981',
        }
        color = colors.get(obj.role, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Rol'

    def has_add_permission(self, request) -> bool:
        """
        Deshabilita la creación manual de perfiles.

        PROPÓSITO:
            Los perfiles se crean automáticamente via signal.
            Crearlos manualmente podría causar inconsistencias.

        RETORNA:
            bool: Siempre False.
        """
        return False
