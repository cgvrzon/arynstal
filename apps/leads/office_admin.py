"""
===============================================================================
ARCHIVO: apps/leads/office_admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Panel de administración SIMPLIFICADO para usuarios de oficina.
    Accesible desde /offynstal/ (office + arynstal).
    Usa django-unfold para una interfaz moderna e intuitiva.

CARACTERÍSTICAS:
    - Solo muestra Lead con inlines de imágenes y logs
    - Campos simplificados (sin RGPD, metadatos técnicos)
    - No permite eliminar registros
    - Acceso restringido a roles 'office' y 'admin'
    - Interfaz moderna con django-unfold

ACCESO:
    URL: /offynstal/
    Roles permitidos: office, admin

===============================================================================
"""

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline as UnfoldTabularInline
from unfold.decorators import display
from unfold.sites import UnfoldAdminSite

from django.utils.html import format_html

from .models import Lead, LeadImage, LeadLog


# =============================================================================
# ADMIN SITE PERSONALIZADO PARA OFICINA
# =============================================================================

class OfficeAdminSite(UnfoldAdminSite):
    """
    AdminSite separado para usuarios de oficina con tema Unfold.

    Usa settings_name = "UNFOLD_OFFICE" para cargar su propia
    configuración visual desde settings/base.py.
    """
    settings_name = "UNFOLD_OFFICE"

    def has_permission(self, request):
        """Solo permite acceso a usuarios con rol 'office' o 'admin'."""
        if not request.user.is_active or not request.user.is_authenticated:
            return False

        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['office', 'admin', 'field']

        return request.user.is_superuser


office_site = OfficeAdminSite(name='office')


# =============================================================================
# INLINES PARA EL PANEL DE OFICINA
# =============================================================================

class OfficeLeadImageInline(UnfoldTabularInline):
    """Inline de imágenes adjuntas al lead (max 5, con preview)."""
    model = LeadImage
    extra = 0
    max_num = 5
    readonly_fields = ('uploaded_at', 'image_preview')
    fields = ('image_preview', 'image', 'uploaded_at')
    can_delete = True
    tab = True

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; '
                'border-radius: 4px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


class OfficeLeadLogInline(UnfoldTabularInline):
    """Inline de historial de acciones del lead (read-only, max 10)."""
    model = LeadLog
    extra = 0
    max_num = 10
    readonly_fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    can_delete = False
    tab = True

    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
# ADMIN DE LEADS SIMPLIFICADO
# =============================================================================

class OfficeLeadAdmin(UnfoldModelAdmin):
    """
    Admin simplificado de Leads para usuarios de oficina.

    Incluye inlines de imágenes y logs en pestañas separadas.
    Badges de estado y urgencia con el sistema de labels de Unfold.
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL LISTADO
    # -------------------------------------------------------------------------

    list_display = (
        'id',
        'name',
        'phone',
        'email',
        'service',
        'display_status',
        'display_urgency',
        'images_count',
        'created_at',
    )

    list_filter = ('status', 'urgency', 'service', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')
    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL FORMULARIO
    # -------------------------------------------------------------------------

    readonly_fields = ('created_at', 'updated_at')
    inlines = [OfficeLeadImageInline, OfficeLeadLogInline]

    fieldsets = (
        ('Datos del Cliente', {
            'fields': ('name', 'email', 'phone', 'location', 'preferred_contact'),
            'description': 'Información de contacto del cliente'
        }),
        ('Solicitud', {
            'fields': ('service', 'message', 'urgency'),
            'description': 'Detalles de lo que necesita el cliente'
        }),
        ('Gestión', {
            'fields': ('status', 'assigned_to', 'notes'),
            'description': 'Estado y seguimiento interno'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # -------------------------------------------------------------------------
    # MÉTODOS DE VISUALIZACIÓN
    # -------------------------------------------------------------------------

    @display(description="Estado", label={
        "nuevo": "success",
        "contactado": "info",
        "presupuestado": "warning",
        "cerrado": None,
        "descartado": "danger",
    })
    def display_status(self, obj):
        return obj.status

    @display(description="Urgencia", label={
        "urgente": "danger",
        "normal": None,
    })
    def display_urgency(self, obj):
        return obj.urgency

    def images_count(self, obj):
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">IMG {}</span>',
                count
            )
        return '-'
    images_count.short_description = 'Imágenes'

    # -------------------------------------------------------------------------
    # OPTIMIZACIÓN
    # -------------------------------------------------------------------------

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Técnicos de campo solo ven leads asignados (mismo patrón que LeadAdmin)
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            queryset = queryset.filter(assigned_to=request.user)
        return queryset.select_related(
            'service', 'assigned_to'
        ).prefetch_related('images')

    # -------------------------------------------------------------------------
    # PERMISOS
    # -------------------------------------------------------------------------

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return True


# =============================================================================
# REGISTRO DE MODELOS EN EL SITE DE OFICINA
# =============================================================================

office_site.register(Lead, OfficeLeadAdmin)
