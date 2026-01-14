from django.contrib import admin
from django.utils.html import format_html
from .models import ContactRequest, ContactRequestImage


class ContactRequestImageInline(admin.TabularInline):
    """
    Permite ver y editar las imágenes asociadas a una solicitud
    directamente desde la página de la solicitud.
    """
    model = ContactRequestImage
    extra = 0  # No mostrar filas vacías adicionales
    readonly_fields = ('uploaded_at', 'image_preview')
    fields = ('image_preview', 'image', 'uploaded_at')
    can_delete = True

    def image_preview(self, obj):
        """Muestra una miniatura de la imagen"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para solicitudes de presupuesto.
    """
    list_display = (
        'id',
        'nombre',
        'telefono',
        'email',
        'status_badge',
        'image_count',
        'created_at',
        'assigned_to'
    )
    list_filter = (
        'status',
        'created_at',
        'assigned_to'
    )
    search_fields = (
        'nombre',
        'email',
        'telefono',
        'descripcion'
    )
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    list_per_page = 25
    date_hierarchy = 'created_at'
    inlines = [ContactRequestImageInline]

    fieldsets = (
        ('Información del cliente', {
            'fields': (
                'nombre',
                'telefono',
                'email',
                'descripcion'
            )
        }),
        ('Gestión interna', {
            'fields': (
                'status',
                'assigned_to',
                'internal_notes'
            ),
            'classes': ('wide',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'nuevo': '#10B981',      # Verde
            'contactado': '#3B82F6',  # Azul
            'presupuestado': '#F59E0B',  # Naranja
            'cerrado': '#6B7280',     # Gris
            'descartado': '#EF4444',  # Rojo
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def image_count(self, obj):
        """Muestra el número de imágenes adjuntas"""
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; border-radius: 3px;">📷 {}</span>',
                count
            )
        return '-'
    image_count.short_description = 'Imágenes'

    def get_queryset(self, request):
        """Optimiza las consultas para evitar N+1 queries"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('assigned_to').prefetch_related('images')
        return queryset


@admin.register(ContactRequestImage)
class ContactRequestImageAdmin(admin.ModelAdmin):
    """
    Panel de administración para las imágenes (opcional, normalmente se gestionan inline).
    """
    list_display = (
        'id',
        'contact_request',
        'image_preview',
        'uploaded_at'
    )
    list_filter = ('uploaded_at',)
    readonly_fields = ('uploaded_at', 'image_preview')

    def image_preview(self, obj):
        """Muestra una miniatura de la imagen"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


# Personalización del sitio admin
admin.site.site_header = "Arynstal SL - Administración"
admin.site.site_title = "Arynstal Admin"
admin.site.index_title = "Panel de control"
