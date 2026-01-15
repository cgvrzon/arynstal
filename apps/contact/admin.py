"""
Admin de Contact - DEPRECADO

Esta app ha sido reemplazada por 'leads'.
Se mantiene solo para acceder a datos históricos.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """
    DEPRECADO: Los nuevos contactos se gestionan en Leads.

    Configuración del panel de administración para mensajes de contacto históricos.
    """
    list_display = (
        'id',
        'name',
        'email',
        'subject',
        'is_read_badge',
        'created_at'
    )
    list_filter = (
        'is_read',
        'created_at',
    )
    search_fields = (
        'name',
        'email',
        'subject',
        'message'
    )
    readonly_fields = ('created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        ('Información del remitente', {
            'fields': (
                'name',
                'email',
                'subject'
            )
        }),
        ('Mensaje', {
            'fields': (
                'message',
                'is_read'
            ),
            'classes': ('wide',)
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def is_read_badge(self, obj):
        """Muestra el estado de lectura con un badge"""
        if obj.is_read:
            return mark_safe(
                '<span style="background-color: #10B981; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">✓ Leído</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #EF4444; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">● Nuevo</span>'
            )
    is_read_badge.short_description = 'Estado'

    def mark_as_read(self, request, queryset):
        """Acción para marcar mensajes como leídos"""
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} mensaje(s) marcado(s) como leído(s).')
    mark_as_read.short_description = 'Marcar como leído'

    def mark_as_unread(self, request, queryset):
        """Acción para marcar mensajes como no leídos"""
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} mensaje(s) marcado(s) como no leído(s).')
    mark_as_unread.short_description = 'Marcar como no leído'
