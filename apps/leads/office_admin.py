"""
===============================================================================
ARCHIVO: apps/leads/office_admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Panel de administración SIMPLIFICADO para usuarios de oficina.
    Accesible desde /offynstal/ (office + arynstal).

    Este panel está diseñado para ser intuitivo y fácil de usar,
    mostrando solo las funcionalidades esenciales para gestionar
    leads y presupuestos.

CARACTERÍSTICAS:
    - Solo muestra Lead y Budget (sin logs, imágenes, servicios, usuarios)
    - Campos simplificados (sin RGPD, metadatos técnicos)
    - No permite eliminar registros
    - Acceso restringido a roles 'office' y 'admin'
    - UI estándar de Django (simple y funcional)

ACCESO:
    URL: /offynstal/
    Roles permitidos: office, admin

===============================================================================
"""

from django.contrib import admin
from django.contrib.admin import AdminSite, ModelAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Lead, Budget


# =============================================================================
# ADMIN SITE PERSONALIZADO PARA OFICINA
# =============================================================================

class OfficeAdminSite(AdminSite):
    """
    AdminSite separado para usuarios de oficina.

    CARACTERÍSTICAS:
        - URL independiente (/offynstal/)
        - Títulos personalizados
        - Restricción de acceso por rol
    """
    site_header = "Arynstal - Panel de Oficina"
    site_title = "Offynstal"
    index_title = "Gestión de Leads y Presupuestos"

    def has_permission(self, request):
        """
        Verifica si el usuario tiene permiso para acceder al panel.

        Solo permite acceso a usuarios con rol 'office' o 'admin'.
        Los técnicos de campo ('field') no pueden acceder.

        RETORNA:
            bool: True si el usuario puede acceder.
        """
        if not request.user.is_active or not request.user.is_authenticated:
            return False

        # Verificar rol del usuario
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['office', 'admin']

        # Superusuarios siempre pueden acceder
        return request.user.is_superuser


# Instancia del AdminSite para oficina
office_site = OfficeAdminSite(name='office')


# =============================================================================
# ADMIN DE LEADS SIMPLIFICADO
# =============================================================================

class OfficeLeadAdmin(ModelAdmin):
    """
    Admin simplificado de Leads para usuarios de oficina.

    SIMPLIFICACIONES:
        - Solo campos esenciales (sin IP, user-agent, RGPD)
        - Sin inlines de imágenes ni logs
        - No permite eliminar
        - Listado limpio con badges de estado
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
        'status_badge',
        'urgency_badge',
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

    def status_badge(self, obj):
        """Badge de color para el estado del lead."""
        colors = {
            'nuevo': '#10B981',
            'contactado': '#3B82F6',
            'presupuestado': '#F59E0B',
            'cerrado': '#6B7280',
            'descartado': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: 600; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def urgency_badge(self, obj):
        """Badge para la urgencia."""
        if obj.urgency == 'urgente':
            return mark_safe(
                '<span style="background-color: #DC2626; color: white; '
                'padding: 3px 8px; border-radius: 4px; font-weight: 600; '
                'font-size: 11px;">URGENTE</span>'
            )
        return mark_safe(
            '<span style="color: #6B7280; font-size: 12px;">Normal</span>'
        )
    urgency_badge.short_description = 'Urgencia'

    # -------------------------------------------------------------------------
    # PERMISOS
    # -------------------------------------------------------------------------

    def has_delete_permission(self, request, obj=None):
        """Oficina no puede eliminar leads."""
        return False

    def has_add_permission(self, request):
        """Oficina puede crear leads (aunque normalmente vienen del formulario)."""
        return True


# =============================================================================
# ADMIN DE PRESUPUESTOS SIMPLIFICADO
# =============================================================================

class OfficeBudgetAdmin(ModelAdmin):
    """
    Admin simplificado de Presupuestos para usuarios de oficina.

    FUNCIONALIDADES:
        - Crear y editar presupuestos
        - Adjuntar archivo PDF
        - Ver referencia auto-generada
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL LISTADO
    # -------------------------------------------------------------------------

    list_display = (
        'reference',
        'lead_name',
        'amount_display',
        'status_badge',
        'valid_until',
        'created_at',
    )

    list_filter = ('status', 'created_at', 'valid_until')
    search_fields = ('reference', 'lead__name', 'lead__email', 'description')
    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL FORMULARIO
    # -------------------------------------------------------------------------

    readonly_fields = ('reference', 'created_at', 'created_by')
    autocomplete_fields = ['lead']

    fieldsets = (
        ('Presupuesto', {
            'fields': ('reference', 'lead', 'description'),
            'description': 'Información básica del presupuesto'
        }),
        ('Importe y Estado', {
            'fields': ('amount', 'status', 'valid_until'),
        }),
        ('Documento', {
            'fields': ('file',),
            'description': 'Adjuntar PDF del presupuesto'
        }),
        ('Metadatos', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',),
        }),
    )

    # -------------------------------------------------------------------------
    # MÉTODOS DE VISUALIZACIÓN
    # -------------------------------------------------------------------------

    def lead_name(self, obj):
        """Nombre del cliente asociado."""
        return obj.lead.name if obj.lead else '-'
    lead_name.short_description = 'Cliente'

    def amount_display(self, obj):
        """Importe formateado con símbolo de euro."""
        if obj.amount:
            formatted = '{:,.2f}'.format(obj.amount)
            return format_html(
                '<span style="font-weight: 600;">{} €</span>',
                formatted
            )
        return '-'
    amount_display.short_description = 'Importe'

    def status_badge(self, obj):
        """Badge de color para el estado del presupuesto."""
        colors = {
            'borrador': '#9CA3AF',
            'enviado': '#3B82F6',
            'aceptado': '#10B981',
            'rechazado': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: 600; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    # -------------------------------------------------------------------------
    # PERMISOS Y HOOKS
    # -------------------------------------------------------------------------

    def has_delete_permission(self, request, obj=None):
        """Oficina no puede eliminar presupuestos."""
        return False

    def save_model(self, request, obj, form, change):
        """Asigna el usuario creador automáticamente."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# REGISTRO DE MODELOS EN EL SITE DE OFICINA
# =============================================================================

office_site.register(Lead, OfficeLeadAdmin)
office_site.register(Budget, OfficeBudgetAdmin)
