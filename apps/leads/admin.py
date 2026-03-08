"""
===============================================================================
ARCHIVO: apps/leads/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configura el panel de administración de Django para la gestión de leads.
    Usa django-unfold para una interfaz moderna con badges, iconos y sidebar.

FUNCIONES PRINCIPALES:
    - LeadAdmin: Administración completa de leads con inlines
    - LeadImageAdmin: Gestión de imágenes adjuntas
    - BudgetAdmin: Gestión de presupuestos
    - LeadLogAdmin: Visualización de auditoría (solo lectura)

===============================================================================
"""

import csv

from django.contrib import admin
from django.db.models import Count, Max
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline as UnfoldTabularInline
from unfold.decorators import display

from .models import Lead, LeadImage, Budget, LeadLog
from .notifications import notify_lead_assigned, notify_note_added

admin.site.index_template = 'admin/admin_index.html'


# =============================================================================
# HELPER: CHANGELOG CONSOLIDADO PARA LEADS
# =============================================================================

def _build_lead_changelog(old_obj, new_obj, form):
    """
    Construye la lista de cambios comparando el lead antes y después del save.
    Retorna una lista de strings descriptivos para cada cambio detectado.
    """
    changes = []

    if old_obj.status != new_obj.status:
        changes.append(
            f"Estado: {old_obj.get_status_display()} → {new_obj.get_status_display()}"
        )

    if old_obj.assigned_to != new_obj.assigned_to:
        old_assigned = str(old_obj.assigned_to) if old_obj.assigned_to else 'Sin asignar'
        new_assigned = str(new_obj.assigned_to) if new_obj.assigned_to else 'Sin asignar'
        changes.append(f"Asignado: {old_assigned} → {new_assigned}")

    if old_obj.notes != new_obj.notes:
        changes.append("Nota: actualizada")

    tracked = {'status', 'assigned_to', 'notes'}
    other_fields = {
        'name', 'email', 'phone', 'location', 'service',
        'message', 'preferred_contact', 'source',
    }
    for field_name in form.changed_data:
        if field_name in other_fields and field_name not in tracked:
            verbose = form.fields[field_name].label or field_name
            changes.append(f"{verbose} modificado")

    return changes


def _determine_log_action(changes):
    """Determina el action type basándose en los cambios detectados."""
    if len(changes) == 1:
        if changes[0].startswith('Estado:'):
            return 'status_changed'
        if changes[0].startswith('Asignado:'):
            return 'assigned'
        if 'Nota' in changes[0]:
            return 'note_added'
    return 'edited'


# =============================================================================
# INLINES - MODELOS RELACIONADOS EDITABLES DENTRO DEL LEAD
# =============================================================================

class LeadImageInline(UnfoldTabularInline):
    """Inline para gestionar imágenes adjuntas a un lead."""
    model = LeadImage
    extra = 0
    readonly_fields = ('uploaded_at', 'image_preview')
    fields = ('image_preview', 'image', 'uploaded_at')
    can_delete = True
    max_num = 5

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; '
                'border-radius: 4px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


class BudgetInline(UnfoldTabularInline):
    """Inline para gestionar presupuestos asociados a un lead."""
    model = Budget
    extra = 0
    readonly_fields = ('reference', 'created_at', 'created_by')
    fields = (
        'reference', 'description', 'amount', 'status',
        'valid_until', 'file', 'created_at', 'created_by'
    )
    can_delete = False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by')


class LeadLogInline(UnfoldTabularInline):
    """Inline para visualizar el historial de acciones del lead (read-only)."""
    model = LeadLog
    extra = 0
    readonly_fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    can_delete = False
    max_num = 20

    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
# ADMIN: LEAD (MODELO PRINCIPAL)
# =============================================================================

@admin.register(Lead)
class LeadAdmin(UnfoldModelAdmin):
    """Panel de administración completo para leads."""

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
        'display_source',
        'images_count',
        'budgets_count',
        'created_at',
        'assigned_to'
    )
    list_display_links = None

    list_filter = (
        'status',
        'source',
        'privacy_accepted',
        'created_at',
        'assigned_to',
        'service'
    )

    search_fields = (
        'name',
        'email',
        'phone',
        'message',
        'location'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'ip_address',
        'user_agent'
    )

    list_per_page = 25
    date_hierarchy = 'created_at'
    inlines = [LeadImageInline, BudgetInline, LeadLogInline]
    autocomplete_fields = ['service', 'assigned_to']
    actions = ['export_to_csv']

    # -------------------------------------------------------------------------
    # ACCIONES PERSONALIZADAS
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

    # -------------------------------------------------------------------------
    # FIELDSETS
    # -------------------------------------------------------------------------

    fieldsets = (
        ('Información del cliente', {
            'fields': (
                'name',
                'email',
                'phone',
                'location',
                'preferred_contact'
            )
        }),
        ('Detalles de la solicitud', {
            'fields': (
                'service',
                'message',
                'source'
            ),
            'classes': ('wide',)
        }),
        ('Gestión interna', {
            'fields': (
                'status',
                'assigned_to',
                'notes'
            ),
            'classes': ('wide',)
        }),
        ('RGPD y Seguridad', {
            'fields': (
                'privacy_accepted',
                'ip_address',
                'user_agent'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    # -------------------------------------------------------------------------
    # MÉTODOS DE VISUALIZACIÓN - BADGES CON UNFOLD @display
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

    @display(description="Origen", label={
        "web": "info",
        "telefono": "success",
        "recomendacion": "warning",
        "otro": None,
    })
    def display_source(self, obj):
        return obj.source

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

    def budgets_count(self, obj):
        count = obj.budgets.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #FEF3C7; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">PRES {}</span>',
                count
            )
        return '-'
    budgets_count.short_description = 'Presupuestos'

    def view_detail(self, obj):
        url = reverse('admin:leads_lead_change', args=[obj.pk])
        return format_html(
            '<a href="{}" title="Ver detalle" class="office-view-detail">'
            '<span class="material-symbols-outlined">visibility</span>'
            '</a>',
            url
        )
    view_detail.short_description = ''

    # -------------------------------------------------------------------------
    # OPTIMIZACIÓN DE QUERIES
    # -------------------------------------------------------------------------

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        # Filtrar por rol: técnicos de campo solo ven sus leads asignados
        if hasattr(request.user, 'profile') and request.user.profile.is_field():
            queryset = queryset.filter(assigned_to=request.user)

        return queryset.select_related(
            'service', 'assigned_to'
        ).prefetch_related(
            'images', 'budgets'
        )

    # -------------------------------------------------------------------------
    # AUDITORÍA AUTOMÁTICA
    # -------------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if change:
            obj._logging_handled_in_admin = True
            old_obj = Lead.objects.get(pk=obj.pk)

            super().save_model(request, obj, form, change)

            changes = _build_lead_changelog(old_obj, obj, form)

            # Notificaciones
            if old_obj.assigned_to != obj.assigned_to and obj.assigned_to:
                notify_lead_assigned(obj, obj.assigned_to)
            if old_obj.notes != obj.notes and obj.notes:
                if hasattr(request.user, 'profile') and request.user.profile.is_field():
                    notify_note_added(obj, request.user)

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


# =============================================================================
# ADMIN: LEADIMAGE
# =============================================================================

@admin.register(LeadImage)
class LeadImageAdmin(UnfoldModelAdmin):
    """Panel de administración para imágenes de leads."""
    list_display = ('view_detail', 'lead', 'image_preview', 'uploaded_at')
    list_display_links = None
    list_filter = ('uploaded_at',)
    readonly_fields = ('uploaded_at', 'image_preview')
    search_fields = ('lead__name', 'lead__email')

    def view_detail(self, obj):
        url = reverse('admin:leads_leadimage_change', args=[obj.pk])
        return format_html(
            '<a href="{}" title="Ver detalle" class="office-view-detail">'
            '<span class="material-symbols-outlined">visibility</span>'
            '</a>',
            url
        )
    view_detail.short_description = ''

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; '
                'border-radius: 4px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


# =============================================================================
# ADMIN: BUDGET
# =============================================================================

@admin.register(Budget)
class BudgetAdmin(UnfoldModelAdmin):
    """Panel de administración para presupuestos."""
    list_display = (
        'view_detail',
        'reference',
        'lead',
        'amount',
        'display_status',
        'valid_until',
        'created_at',
        'created_by'
    )
    list_display_links = None
    list_filter = ('status', 'created_at', 'valid_until')
    search_fields = ('reference', 'lead__name', 'lead__email', 'description')
    readonly_fields = ('reference', 'created_at', 'created_by')
    autocomplete_fields = ['lead']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información del presupuesto', {
            'fields': (
                'reference',
                'lead',
                'description',
                'amount',
                'status',
                'valid_until'
            )
        }),
        ('Archivo', {
            'fields': ('file',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def view_detail(self, obj):
        url = reverse('admin:leads_budget_change', args=[obj.pk])
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


# =============================================================================
# ADMIN: LEADLOG (AUDITORÍA)
# =============================================================================

@admin.register(LeadLog)
class LeadLogAdmin(UnfoldModelAdmin):
    """Panel de administración para logs de auditoría (solo lectura)."""
    list_display = (
        'lead',
        'display_action',
        'user',
        'new_value',
        'created_at'
    )
    list_filter = ('action', 'created_at', 'user', 'lead')
    search_fields = ('lead__name', 'lead__email', 'new_value')
    readonly_fields = (
        'lead', 'user', 'action',
        'old_value', 'new_value', 'created_at'
    )
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

    def has_delete_permission(self, request, obj=None):
        return False
