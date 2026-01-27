"""
===============================================================================
ARCHIVO: apps/services/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configura el panel de administración de Django para el modelo Service.
    Permite gestionar el catálogo de servicios que se muestra en la web.

FUNCIONES PRINCIPALES:
    - ServiceAdmin: Administración completa de servicios

FLUJO EN LA APLICACIÓN:
    1. Admin accede a /admynstal/services/service/
    2. Ve listado de servicios con orden editable
    3. Puede añadir/editar/desactivar servicios
    4. Los cambios se reflejan automáticamente en la web pública

CARACTERÍSTICAS UX:
    - Slug auto-generado desde el nombre
    - Orden editable directamente en el listado
    - Vista previa de imagen
    - Badge visual para estado activo/inactivo
    - Contador de leads por servicio

===============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Service


# =============================================================================
# ADMIN: SERVICE
# =============================================================================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Panel de administración para el catálogo de servicios.

    DESCRIPCIÓN:
        Permite gestionar los servicios que ofrece Arynstal.
        Incluye funcionalidades para ordenar, activar/desactivar
        y asociar imágenes a cada servicio.

    CARACTERÍSTICAS:
        - Listado con orden editable inline
        - Slug auto-generado (prepopulated_fields)
        - Vista previa de imagen
        - Contador de leads asociados
        - Filtros por estado y fecha
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL LISTADO
    # -------------------------------------------------------------------------

    list_display = (
        'order',              # Editable directamente
        'name',
        'slug',
        'is_active_badge',    # Badge visual de estado
        'created_at',
        'leads_count'         # Contador de leads relacionados
    )

    list_display_links = ('name',)  # Solo el nombre es clickable
    list_editable = ('order',)      # Orden editable en el listado
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

    # Auto-genera el slug mientras se escribe el nombre
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

    def is_active_badge(self, obj) -> str:
        """
        Genera badge visual para el estado activo/inactivo.

        PARÁMETROS:
            obj (Service): Instancia del servicio.

        RETORNA:
            str: HTML con badge verde (activo) o rojo (inactivo).
        """
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: #10B981; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                'Activo</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #EF4444; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                'Inactivo</span>'
            )
    is_active_badge.short_description = 'Estado'

    def image_preview(self, obj) -> str:
        """
        Genera vista previa de la imagen del servicio.

        PARÁMETROS:
            obj (Service): Instancia del servicio.

        RETORNA:
            str: HTML con la imagen o texto "Sin imagen".

        USO:
            Se muestra en el formulario de edición del servicio.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 8px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'

    def leads_count(self, obj) -> str:
        """
        Muestra el número de leads asociados al servicio.

        PARÁMETROS:
            obj (Service): Instancia del servicio.

        RETORNA:
            str: Badge con contador o guión si no hay leads.

        PROPÓSITO:
            Permite identificar qué servicios generan más interés.
            Útil para análisis de demanda y decisiones de marketing.
        """
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
        """
        Optimiza las consultas precargando leads relacionados.

        PROPÓSITO:
            Evitar N+1 queries al mostrar leads_count en el listado.

        RETORNA:
            QuerySet: Servicios con leads precargados.
        """
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('leads')
