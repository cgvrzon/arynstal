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

import csv

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline as UnfoldTabularInline
from unfold.decorators import display
from unfold.sites import UnfoldAdminSite

from django.contrib import admin
from django.db.models import Count, Max
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html

from .admin import _build_lead_changelog, _determine_log_action
from .models import Budget, Lead, LeadImage, LeadLog
from .notifications import notify_lead_assigned


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
    index_template = "admin/office_index.html"

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


class OfficeBudgetInline(UnfoldTabularInline):
    """Inline de presupuestos del lead (office/admin pueden crear, editar y eliminar)."""
    model = Budget
    extra = 0
    readonly_fields = ('reference', 'created_at', 'created_by')
    fields = (
        'reference', 'description', 'amount', 'status',
        'valid_until', 'file', 'created_at', 'created_by'
    )
    can_delete = True
    tab = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by')


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
        'view_detail',
        'name',
        'phone',
        'email',
        'service',
        'display_status',
        'images_count',
        'created_at',
    )
    list_display_links = None

    list_filter = ('status', 'service', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')
    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['export_to_csv']

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL FORMULARIO
    # -------------------------------------------------------------------------

    inlines = [OfficeLeadImageInline, OfficeBudgetInline, OfficeLeadLogInline]

    fieldsets = (
        ('Datos del Cliente', {
            'fields': ('name', 'email', 'phone', 'location', 'preferred_contact'),
            'description': 'Información de contacto del cliente'
        }),
        ('Solicitud', {
            'fields': ('service', 'message'),
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

    def view_detail(self, obj):
        url = reverse('office:leads_lead_change', args=[obj.pk])
        return format_html(
            '<a href="{}" title="Ver detalle" class="office-view-detail">'
            '<span class="material-symbols-outlined">visibility</span>'
            '</a>',
            url
        )
    view_detail.short_description = ''

    # -------------------------------------------------------------------------
    # ACCIONES
    # -------------------------------------------------------------------------

    @admin.action(description='Exportar leads seleccionados a CSV')
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
        response.write('\ufeff')  # BOM para Excel

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Nombre', 'Email', 'Teléfono', 'Servicio',
            'Estado', 'Origen', 'Fecha creación',
            'Asignado a', 'Ubicación', 'Mensaje'
        ])

        for lead in queryset.select_related('service', 'assigned_to'):
            writer.writerow([
                lead.id,
                lead.name,
                lead.email,
                lead.phone,
                lead.service.name if lead.service else '',
                lead.get_status_display(),
                lead.get_source_display(),
                lead.created_at.strftime('%d/%m/%Y %H:%M'),
                str(lead.assigned_to) if lead.assigned_to else '',
                lead.location or '',
                lead.message[:100] + '...' if len(lead.message) > 100 else lead.message
            ])

        return response

    def get_actions(self, request):
        """Field no puede exportar CSV."""
        actions = super().get_actions(request)
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            actions.pop('export_to_csv', None)
        return actions

    # -------------------------------------------------------------------------
    # AUDITORÍA AUTOMÁTICA
    # -------------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if change:
            obj._logging_handled_in_admin = True
            old_obj = Lead.objects.get(pk=obj.pk)

            super().save_model(request, obj, form, change)

            changes = _build_lead_changelog(old_obj, obj, form)

            # Notificación de asignación
            if old_obj.assigned_to != obj.assigned_to and obj.assigned_to:
                notify_lead_assigned(obj, obj.assigned_to)

            # Log consolidado
            if changes:
                LeadLog.objects.create(
                    lead=obj,
                    user=request.user,
                    action=_determine_log_action(changes),
                    new_value=' | '.join(changes)
                )

            if hasattr(obj, '_logging_handled_in_admin'):
                delattr(obj, '_logging_handled_in_admin')
        else:
            super().save_model(request, obj, form, change)
            LeadLog.objects.create(
                lead=obj,
                user=request.user,
                action='created',
                new_value='Lead creado desde el admin'
            )

    # -------------------------------------------------------------------------
    # CAMPOS READONLY DINÁMICOS POR ROL
    # -------------------------------------------------------------------------

    def get_readonly_fields(self, request, obj=None):
        """Field solo puede editar notas. El resto de campos son read-only."""
        base_readonly = ('created_at', 'updated_at')
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            all_fields = (
                'name', 'email', 'phone', 'location', 'preferred_contact',
                'service', 'message',
                'status', 'assigned_to',
                'created_at', 'updated_at',
            )
            return all_fields
        return base_readonly

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

    def has_module_permission(self, request):
        """Acceso al módulo basado en rol (no en permisos de Django)."""
        if not request.user.is_active or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['office', 'admin', 'field']
        return False

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        """Office y admin pueden crear leads. Field no."""
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            return False
        return self.has_module_permission(request)


# =============================================================================
# ADMIN: PRESUPUESTOS EN OFFYNSTAL
# =============================================================================

class OfficeBudgetAdmin(UnfoldModelAdmin):
    """
    Admin de presupuestos para el panel de oficina.
    Office puede ver, crear y editar. No puede eliminar.
    Field no tiene acceso.
    """

    list_display = (
        'view_detail',
        'reference',
        'lead',
        'amount',
        'display_status',
        'valid_until',
        'created_at',
        'created_by',
    )
    list_display_links = None
    list_filter = ('status', 'created_at', 'valid_until')
    search_fields = ('reference', 'lead__name', 'lead__email', 'description')
    readonly_fields = ('reference', 'created_at', 'created_by')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información del presupuesto', {
            'fields': (
                'reference', 'lead', 'description',
                'amount', 'status', 'valid_until',
            )
        }),
        ('Archivo', {
            'fields': ('file',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'created_by'),
        }),
    )

    def view_detail(self, obj):
        url = reverse('office:leads_budget_change', args=[obj.pk])
        return format_html(
            '<a href="{}" title="Ver detalle" class="office-view-detail">'
            '<span class="material-symbols-outlined">visibility</span>'
            '</a>',
            url
        )
    view_detail.short_description = ''

    @display(description="Estado", label={
        "borrador": None,
        "enviado": "info",
        "aceptado": "success",
        "rechazado": "danger",
    })
    def display_status(self, obj):
        return obj.status

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # -------------------------------------------------------------------------
    # PERMISOS (basados en rol, no en permisos Django)
    # -------------------------------------------------------------------------

    def _is_office_or_admin(self, request):
        if not request.user.is_active or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['office', 'admin']
        return False

    def has_module_permission(self, request):
        return self._is_office_or_admin(request)

    def has_view_permission(self, request, obj=None):
        return self._is_office_or_admin(request)

    def has_add_permission(self, request):
        return self._is_office_or_admin(request)

    def has_change_permission(self, request, obj=None):
        return self._is_office_or_admin(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_office_or_admin(request)


# =============================================================================
# ADMIN: HISTORIAL DE LEADS EN OFFYNSTAL (READ-ONLY)
# =============================================================================

class OfficeLeadLogAdmin(UnfoldModelAdmin):
    """
    Historial de acciones sobre leads. Completamente read-only.
    Field solo ve logs de leads asignados a él.
    """

    list_display = ('lead', 'display_action', 'user', 'new_value', 'created_at')
    list_filter = ('action', 'created_at', 'lead')
    search_fields = ('lead__name', 'lead__email', 'new_value')
    readonly_fields = ('lead', 'action', 'user', 'old_value', 'new_value', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    @display(description="Acción", label={
        "created": "success",
        "status_changed": "info",
        "assigned": "warning",
        "note_added": None,
        "edited": "info",
        "updated": None,
    })
    def display_action(self, obj):
        return obj.action

    def changelist_view(self, request, extra_context=None):
        """Sin filtro de lead, muestra lista agrupada por lead."""
        if 'lead__id__exact' in request.GET:
            return super().changelist_view(request, extra_context)

        leads_with_logs = Lead.objects.filter(
            logs__isnull=False
        ).distinct().annotate(
            logs_count=Count('logs'),
            last_log=Max('logs__created_at')
        ).order_by('-last_log')

        # Field solo ve sus leads
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            leads_with_logs = leads_with_logs.filter(assigned_to=request.user)

        context = {
            **self.admin_site.each_context(request),
            'leads_with_logs': leads_with_logs,
            'title': 'Historial de Leads',
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request, 'admin/leadlog_grouped.html', context
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        if not request.user.is_active or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['office', 'admin', 'field']
        return False

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            queryset = queryset.filter(lead__assigned_to=request.user)
        return queryset.select_related('lead', 'user')


# =============================================================================
# REGISTRO DE MODELOS EN EL SITE DE OFICINA
# =============================================================================

office_site.register(Lead, OfficeLeadAdmin)
office_site.register(Budget, OfficeBudgetAdmin)
office_site.register(LeadLog, OfficeLeadLogAdmin)
