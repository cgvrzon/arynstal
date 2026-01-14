from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para servicios.
    """
    list_display = (
        'order',
        'name',
        'slug',
        'is_active_badge',
        'created_at',
        'leads_count'
    )
    list_display_links = ('name',)
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
    prepopulated_fields = {
        'slug': ('name',)
    }
    readonly_fields = (
        'created_at',
        'updated_at',
        'image_preview'
    )
    list_editable = ('order',)
    list_per_page = 25
    date_hierarchy = 'created_at'

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

    def is_active_badge(self, obj):
        """Muestra el estado activo con un badge de color"""
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: #10B981; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Activo</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #EF4444; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✗ Inactivo</span>'
            )
    is_active_badge.short_description = 'Estado'

    def image_preview(self, obj):
        """Muestra una vista previa de la imagen"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'

    def leads_count(self, obj):
        """Muestra el número de leads asociados"""
        count = obj.leads.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; border-radius: 3px;">👥 {}</span>',
                count
            )
        return '-'
    leads_count.short_description = 'Leads'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('leads')
        return queryset
