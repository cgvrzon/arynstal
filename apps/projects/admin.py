from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Project, ProjectImage


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    max_num = ProjectImage.MAX_IMAGES_PER_PROJECT
    fields = ('image', 'image_preview', 'alt_text', 'order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; border-radius: 4px;" />',
                obj.image.url,
            )
        return '-'
    image_preview.short_description = 'Vista previa'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'title',
        'service',
        'year',
        'is_active_badge',
        'is_featured_badge',
        'images_count',
        'updated_at',
    )
    list_display_links = ('title',)
    list_editable = ('order',)
    list_filter = ('is_active', 'is_featured', 'service', 'year')
    search_fields = ('title', 'description', 'client')
    list_per_page = 25
    date_hierarchy = 'created_at'

    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['service']
    readonly_fields = ('created_at', 'updated_at', 'cover_preview')

    fieldsets = (
        ('Información básica', {
            'fields': ('title', 'slug', 'service', 'description'),
        }),
        ('Imagen de portada', {
            'fields': ('cover_image', 'cover_preview'),
        }),
        ('Detalles del proyecto', {
            'fields': ('area', 'duration', 'year', 'client'),
        }),
        ('Control', {
            'fields': ('is_active', 'is_featured', 'order'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [ProjectImageInline]

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; '
                'border-radius: 8px;" />',
                obj.cover_image.url,
            )
        return 'Sin imagen'
    cover_preview.short_description = 'Vista previa portada'

    def is_active_badge(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: #10B981; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                'Activo</span>'
            )
        return mark_safe(
            '<span style="background-color: #EF4444; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
            'Inactivo</span>'
        )
    is_active_badge.short_description = 'Estado'

    def is_featured_badge(self, obj):
        if obj.is_featured:
            return mark_safe(
                '<span style="background-color: #F59E0B; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-weight: 600; '
                'font-size: 11px;">DESTACADO</span>'
            )
        return '-'
    is_featured_badge.short_description = 'Destacado'

    def images_count(self, obj):
        count = obj.images.count() + 1  # +1 por la portada
        return format_html(
            '<span style="background-color: #E0E8F2; padding: 2px 8px; '
            'border-radius: 3px;">{} img</span>',
            count,
        )
    images_count.short_description = 'Imágenes'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'service'
        ).prefetch_related('images')
