"""
===============================================================================
ARCHIVO: apps/services/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configura el panel de administración para el modelo Service.
    Usa django-unfold para interfaz moderna con badges y sidebar.

===============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.decorators import display

from .models import Service


# =============================================================================
# ADMIN: SERVICE
# =============================================================================

@admin.register(Service)
class ServiceAdmin(UnfoldModelAdmin):
    """Panel de administración para el catálogo de servicios."""

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL LISTADO
    # -------------------------------------------------------------------------

    list_display = (
        'order',
        'name',
        'slug',
        'display_is_active',
        'created_at',
        'leads_count'
    )

    list_display_links = ('name',)
    list_editable = ('order',)
    list_per_page = 25

    list_filter = (
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'slug',
        'description',
        'short_description'
    )

    # -------------------------------------------------------------------------
    # CAMPOS ESPECIALES
    # -------------------------------------------------------------------------

    prepopulated_fields = {
        'slug': ('name',)
    }

    readonly_fields = (
        'created_at',
        'updated_at',
        'image_preview'
    )

    date_hierarchy = 'created_at'

    # -------------------------------------------------------------------------
    # FIELDSETS
    # -------------------------------------------------------------------------

    fieldsets = (
        ('Información básica', {
            'fields': (
                'name',
                'slug',
                'is_active',
                'order'
            )
        }),
        ('Contenido', {
            'fields': (
                'short_description',
                'description',
                'icon'
            ),
            'classes': ('wide',)
        }),
        ('Imagen', {
            'fields': (
                'image',
                'image_preview'
            )
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
    # MÉTODOS DE VISUALIZACIÓN
    # -------------------------------------------------------------------------

    @display(description="Estado", boolean=True)
    def display_is_active(self, obj):
        return obj.is_active

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 8px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'

    def leads_count(self, obj):
        count = obj.leads.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; '
                'border-radius: 3px;">LEADS {}</span>',
                count
            )
        return '-'
    leads_count.short_description = 'Leads'

    # -------------------------------------------------------------------------
    # OPTIMIZACIÓN
    # -------------------------------------------------------------------------

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('leads')
