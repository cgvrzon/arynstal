from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline as UnfoldTabularInline
from unfold.decorators import display

from .models import Project, ProjectImage


class ProjectImageInline(UnfoldTabularInline):
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
class ProjectAdmin(UnfoldModelAdmin):
    list_display = (
        'view_detail',
        'title',
        'service',
        'year',
        'display_is_active',
        'display_is_featured',
        'images_count',
        'updated_at',
    )
    list_display_links = None
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

    def view_detail(self, obj):
        url = reverse('admin:projects_project_change', args=[obj.pk])
        return format_html(
            '<a href="{}" title="Ver detalle" class="office-view-detail">'
            '<span class="material-symbols-outlined">visibility</span>'
            '</a>',
            url
        )
    view_detail.short_description = ''

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; '
                'border-radius: 8px;" />',
                obj.cover_image.url,
            )
        return 'Sin imagen'
    cover_preview.short_description = 'Vista previa portada'

    @display(description="Estado", boolean=True)
    def display_is_active(self, obj):
        return obj.is_active

    @display(description="Destacado", label={
        True: "warning",
        False: None,
    })
    def display_is_featured(self, obj):
        return obj.is_featured

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
