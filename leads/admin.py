from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Lead, LeadImage, Budget, LeadLog


class LeadImageInline(admin.TabularInline):
    """
    Permite ver y editar las imágenes asociadas a un lead
    directamente desde la página del lead.
    """
    model = LeadImage
    extra = 0
    readonly_fields = ('uploaded_at', 'image_preview')
    fields = ('image_preview', 'image', 'uploaded_at')
    can_delete = True
    max_num = 5  # Máximo 5 imágenes por lead

    def image_preview(self, obj):
        """Muestra una miniatura de la imagen"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; border-radius: 4px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


class BudgetInline(admin.TabularInline):
    """
    Permite gestionar presupuestos directamente desde el lead.
    """
    model = Budget
    extra = 0
    readonly_fields = ('reference', 'created_at', 'created_by')
    fields = ('reference', 'description', 'amount', 'status', 'valid_until', 'file', 'created_at', 'created_by')
    can_delete = False  # No permitir eliminar presupuestos desde aquí

    def get_queryset(self, request):
        """Optimiza las consultas"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('created_by')
        return queryset


class LeadLogInline(admin.TabularInline):
    """
    Muestra el historial de acciones del lead (solo lectura).
    """
    model = LeadLog
    extra = 0
    readonly_fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    can_delete = False
    max_num = 20  # Mostrar máximo las últimas 20 acciones

    def has_add_permission(self, request, obj=None):
        """No permitir añadir logs manualmente (se crean automáticamente)"""
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para leads.
    """
    list_display = (
        'id',
        'name',
        'phone',
        'email',
        'service',
        'status_badge',
        'urgency_badge',
        'source_badge',
        'images_count',
        'budgets_count',
        'created_at',
        'assigned_to'
    )
    list_filter = (
        'status',
        'source',
        'urgency',
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
                'urgency',
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

    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'nuevo': '#10B981',       # Verde brillante
            'contactado': '#3B82F6',  # Azul
            'presupuestado': '#F59E0B',  # Naranja
            'cerrado': '#6B7280',     # Gris
            'descartado': '#EF4444',  # Rojo
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def urgency_badge(self, obj):
        """Muestra la urgencia con un badge"""
        if obj.urgency == 'urgente':
            return mark_safe(
                '<span style="background-color: #DC2626; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold; font-size: 11px;">🔥 URGENTE</span>'
            )
        return mark_safe(
            '<span style="color: #6B7280; font-size: 11px;">Normal</span>'
        )
    urgency_badge.short_description = 'Urgencia'

    def source_badge(self, obj):
        """Muestra el origen con un icono"""
        icons = {
            'web': '🌐',
            'telefono': '📞',
            'recomendacion': '👥',
            'otro': '📋',
        }
        icon = icons.get(obj.source, '📋')
        return format_html(
            '<span style="font-size: 14px;" title="{}">{}</span>',
            obj.get_source_display(),
            icon
        )
    source_badge.short_description = 'Origen'

    def images_count(self, obj):
        """Muestra el número de imágenes adjuntas"""
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #E0E8F2; padding: 2px 8px; border-radius: 3px; font-size: 11px;">📷 {}</span>',
                count
            )
        return '-'
    images_count.short_description = 'Imágenes'

    def budgets_count(self, obj):
        """Muestra el número de presupuestos"""
        count = obj.budgets.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #FEF3C7; padding: 2px 8px; border-radius: 3px; font-size: 11px;">💰 {}</span>',
                count
            )
        return '-'
    budgets_count.short_description = 'Presupuestos'

    def get_queryset(self, request):
        """Optimiza las consultas para evitar N+1 queries"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('service', 'assigned_to').prefetch_related('images', 'budgets')
        return queryset

    def save_model(self, request, obj, form, change):
        """Guarda el modelo y registra en LeadLog si hay cambios"""
        if change:
            # Detectar cambios en el estado
            old_obj = Lead.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                LeadLog.objects.create(
                    lead=obj,
                    user=request.user,
                    action='status_changed',
                    old_value=old_obj.get_status_display(),
                    new_value=obj.get_status_display()
                )
            if old_obj.assigned_to != obj.assigned_to:
                LeadLog.objects.create(
                    lead=obj,
                    user=request.user,
                    action='assigned',
                    old_value=str(old_obj.assigned_to) if old_obj.assigned_to else 'Sin asignar',
                    new_value=str(obj.assigned_to) if obj.assigned_to else 'Sin asignar'
                )
        else:
            # Nuevo lead creado desde el admin
            LeadLog.objects.create(
                lead=obj,
                user=request.user,
                action='created',
                new_value='Lead creado desde el admin'
            )

        super().save_model(request, obj, form, change)


@admin.register(LeadImage)
class LeadImageAdmin(admin.ModelAdmin):
    """
    Panel de administración para las imágenes de leads (opcional).
    """
    list_display = (
        'id',
        'lead',
        'image_preview',
        'uploaded_at'
    )
    list_filter = ('uploaded_at',)
    readonly_fields = ('uploaded_at', 'image_preview')
    search_fields = ('lead__name', 'lead__email')

    def image_preview(self, obj):
        """Muestra una miniatura de la imagen"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 4px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """
    Panel de administración para presupuestos.
    """
    list_display = (
        'reference',
        'lead',
        'amount',
        'status_badge',
        'valid_until',
        'created_at',
        'created_by'
    )
    list_filter = (
        'status',
        'created_at',
        'valid_until'
    )
    search_fields = (
        'reference',
        'lead__name',
        'lead__email',
        'description'
    )
    readonly_fields = (
        'reference',
        'created_at',
        'created_by'
    )
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
            'fields': (
                'created_at',
                'created_by'
            ),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'borrador': '#9CA3AF',    # Gris
            'enviado': '#3B82F6',     # Azul
            'aceptado': '#10B981',    # Verde
            'rechazado': '#EF4444',   # Rojo
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        """Asigna el usuario que crea el presupuesto"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadLog)
class LeadLogAdmin(admin.ModelAdmin):
    """
    Panel de administración para los logs de leads (solo lectura).
    """
    list_display = (
        'lead',
        'action',
        'user',
        'old_value',
        'new_value',
        'created_at'
    )
    list_filter = (
        'action',
        'created_at',
        'user'
    )
    search_fields = (
        'lead__name',
        'lead__email',
        'old_value',
        'new_value'
    )
    readonly_fields = (
        'lead',
        'user',
        'action',
        'old_value',
        'new_value',
        'created_at'
    )
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """No permitir añadir logs manualmente"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar logs (auditoría)"""
        return False
