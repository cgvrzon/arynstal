"""
===============================================================================
ARCHIVO: apps/leads/admin.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configura el panel de administración de Django para la gestión de leads.
    Define cómo se visualizan, filtran y editan los leads, imágenes,
    presupuestos y logs desde el backend /gestion-interna/.

FUNCIONES PRINCIPALES:
    - LeadAdmin: Administración completa de leads con inlines
    - LeadImageAdmin: Gestión de imágenes adjuntas
    - BudgetAdmin: Gestión de presupuestos
    - LeadLogAdmin: Visualización de auditoría (solo lectura)

FLUJO EN LA APLICACIÓN:
    1. Usuario admin accede a /gestion-interna/
    2. Ve listado de leads con filtros, badges y contadores
    3. Accede al detalle de un lead (fieldsets organizados)
    4. Gestiona imágenes y presupuestos desde inlines
    5. Los cambios se registran automáticamente en LeadLog

CARACTERÍSTICAS UX DEL ADMIN:
    - Badges de colores para estados y urgencias
    - Iconos para origen del lead
    - Contadores de imágenes y presupuestos
    - Fieldsets colapsables para datos técnicos
    - Autocomplete en campos relacionales
    - Optimización de queries (select_related, prefetch_related)

PRINCIPIOS DE DISEÑO:
    - DRY: Métodos de badge reutilizables
    - Optimización: Evitar N+1 queries en listados
    - UX: Información visual rápida con badges e iconos
    - Seguridad: Logs de auditoría automáticos

===============================================================================
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Lead, LeadImage, Budget, LeadLog


# =============================================================================
# INLINES - MODELOS RELACIONADOS EDITABLES DENTRO DEL LEAD
# =============================================================================
# Los inlines permiten editar modelos relacionados (imágenes, presupuestos, logs)
# directamente desde la página de edición del lead padre.


class LeadImageInline(admin.TabularInline):
    """
    Inline para gestionar imágenes adjuntas a un lead.

    DESCRIPCIÓN:
        Muestra las imágenes del lead en formato tabla con vista previa.
        Permite añadir, ver y eliminar imágenes sin salir del lead.

    CARACTERÍSTICAS:
        - Vista previa en miniatura (150x150px)
        - Máximo 5 imágenes por lead (validado también en modelo)
        - Fecha de subida en solo lectura

    UBICACIÓN:
        Se muestra en la página de edición del Lead (LeadAdmin).
    """
    model = LeadImage
    extra = 0  # No mostrar filas vacías adicionales
    readonly_fields = ('uploaded_at', 'image_preview')
    fields = ('image_preview', 'image', 'uploaded_at')
    can_delete = True
    max_num = 5  # Límite máximo de imágenes

    def image_preview(self, obj):
        """
        Genera HTML para mostrar miniatura de la imagen.

        PARÁMETROS:
            obj (LeadImage): Instancia de la imagen a previsualizar.

        RETORNA:
            str: HTML seguro con la etiqueta <img> o texto "Sin imagen".

        USO:
            Se muestra automáticamente en la columna 'Vista previa' del inline.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; '
                'border-radius: 4px;" />',
                obj.image.url
            )
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'


class BudgetInline(admin.TabularInline):
    """
    Inline para gestionar presupuestos asociados a un lead.

    DESCRIPCIÓN:
        Permite ver y crear presupuestos directamente desde el lead.
        La referencia se genera automáticamente al guardar.

    CARACTERÍSTICAS:
        - Referencia y fecha en solo lectura
        - No permite eliminar (integridad de datos)
        - Optimizado con select_related para el creador

    UBICACIÓN:
        Se muestra en la página de edición del Lead (LeadAdmin).
    """
    model = Budget
    extra = 0
    readonly_fields = ('reference', 'created_at', 'created_by')
    fields = (
        'reference', 'description', 'amount', 'status',
        'valid_until', 'file', 'created_at', 'created_by'
    )
    can_delete = False  # Preservar historial de presupuestos

    def get_queryset(self, request):
        """
        Optimiza las consultas añadiendo select_related.

        PROPÓSITO:
            Evitar N+1 queries al cargar el campo created_by.

        RETORNA:
            QuerySet: Presupuestos con usuario precargado.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by')


class LeadLogInline(admin.TabularInline):
    """
    Inline para visualizar el historial de acciones del lead.

    DESCRIPCIÓN:
        Muestra los logs de auditoría en formato cronológico.
        Es completamente de solo lectura (no añadir, no eliminar).

    CARACTERÍSTICAS:
        - Solo lectura total (auditoría no modificable)
        - Máximo 20 entradas visibles (las más recientes)
        - No permite añadir logs manualmente

    PROPÓSITO:
        Permitir al admin ver el historial de cambios sin salir del lead.

    UBICACIÓN:
        Se muestra al final de la página de edición del Lead.
    """
    model = LeadLog
    extra = 0
    readonly_fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    fields = ('action', 'user', 'old_value', 'new_value', 'created_at')
    can_delete = False
    max_num = 20  # Limitar para no sobrecargar la página

    def has_add_permission(self, request, obj=None):
        """
        Deshabilita la creación manual de logs.

        PROPÓSITO:
            Los logs se crean automáticamente mediante signals.
            Crearlos manualmente rompería la integridad de la auditoría.

        RETORNA:
            bool: Siempre False.
        """
        return False


# =============================================================================
# ADMIN: LEAD (MODELO PRINCIPAL)
# =============================================================================
# Configuración principal del panel de administración para leads.
# Es el modelo central del CRM y tiene la configuración más compleja.

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """
    Panel de administración para el modelo Lead.

    DESCRIPCIÓN:
        Configuración completa para la gestión de leads desde el admin.
        Incluye listado optimizado, filtros, búsqueda, fieldsets organizados
        e inlines para modelos relacionados.

    CARACTERÍSTICAS PRINCIPALES:
        - Listado con badges visuales de estado, urgencia y origen
        - Filtros por estado, origen, urgencia, fecha, asignado y servicio
        - Búsqueda por nombre, email, teléfono, mensaje y ubicación
        - Fieldsets organizados por categoría (colapsables)
        - Inlines para imágenes, presupuestos y logs
        - Autocomplete para servicio y usuario asignado
        - Auditoría automática de cambios

    OPTIMIZACIONES:
        - select_related: servicio y asignado
        - prefetch_related: imágenes y presupuestos
        - date_hierarchy: navegación rápida por fechas
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL LISTADO
    # -------------------------------------------------------------------------

    list_display = (
        'id',
        'name',
        'phone',
        'email',
        'service',
        'status_badge',      # Badge de color para estado
        'urgency_badge',     # Badge para urgencia
        'source_badge',      # Icono de origen
        'images_count',      # Contador de imágenes
        'budgets_count',     # Contador de presupuestos
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

    # -------------------------------------------------------------------------
    # FIELDSETS - ORGANIZACIÓN DEL FORMULARIO DE EDICIÓN
    # -------------------------------------------------------------------------
    # Los fieldsets agrupan campos relacionados y permiten colapsar secciones
    # que no se usan frecuentemente (RGPD, metadatos).

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
            'classes': ('wide',)  # Campos más anchos
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
            'classes': ('collapse',)  # Colapsado por defecto
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
    # MÉTODOS DE VISUALIZACIÓN - BADGES E ICONOS
    # -------------------------------------------------------------------------
    # Estos métodos generan HTML para mostrar información visual en el listado.

    def status_badge(self, obj):
        """
        Genera un badge de color según el estado del lead.

        PARÁMETROS:
            obj (Lead): Instancia del lead.

        RETORNA:
            str: HTML seguro con span estilizado.

        COLORES:
            - Nuevo: Verde (#10B981)
            - Contactado: Azul (#3B82F6)
            - Presupuestado: Naranja (#F59E0B)
            - Cerrado: Gris (#6B7280)
            - Descartado: Rojo (#EF4444)
        """
        colors = {
            'nuevo': '#10B981',
            'contactado': '#3B82F6',
            'presupuestado': '#F59E0B',
            'cerrado': '#6B7280',
            'descartado': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def urgency_badge(self, obj):
        """
        Genera un badge para la urgencia del lead.

        PARÁMETROS:
            obj (Lead): Instancia del lead.

        RETORNA:
            str: HTML con badge rojo si urgente, texto gris si normal.
        """
        if obj.urgency == 'urgente':
            return mark_safe(
                '<span style="background-color: #DC2626; color: white; '
                'padding: 2px 8px; border-radius: 3px; font-weight: bold; '
                'font-size: 11px;">URGENTE</span>'
            )
        return mark_safe(
            '<span style="color: #6B7280; font-size: 11px;">Normal</span>'
        )
    urgency_badge.short_description = 'Urgencia'

    def source_badge(self, obj):
        """
        Genera un icono según el origen del lead.

        PARÁMETROS:
            obj (Lead): Instancia del lead.

        RETORNA:
            str: HTML con emoji representativo del origen.

        ICONOS:
            - Web: Globo
            - Teléfono: Auricular
            - Recomendación: Personas
            - Otro: Documento
        """
        icons = {
            'web': 'WEB',
            'telefono': 'TEL',
            'recomendacion': 'REC',
            'otro': 'OTRO',
        }
        icon = icons.get(obj.source, 'OTRO')
        return format_html(
            '<span style="font-size: 11px; background-color: #E5E7EB; '
            'padding: 2px 6px; border-radius: 3px;" title="{}">{}</span>',
            obj.get_source_display(),
            icon
        )
    source_badge.short_description = 'Origen'

    def images_count(self, obj):
        """
        Muestra contador de imágenes adjuntas con badge.

        PARÁMETROS:
            obj (Lead): Instancia del lead.

        RETORNA:
            str: Badge con contador o guión si no hay imágenes.

        NOTA:
            Usa prefetch_related para evitar queries adicionales.
        """
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
        """
        Muestra contador de presupuestos con badge.

        PARÁMETROS:
            obj (Lead): Instancia del lead.

        RETORNA:
            str: Badge con contador o guión si no hay presupuestos.
        """
        count = obj.budgets.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #FEF3C7; padding: 2px 8px; '
                'border-radius: 3px; font-size: 11px;">PRES {}</span>',
                count
            )
        return '-'
    budgets_count.short_description = 'Presupuestos'

    # -------------------------------------------------------------------------
    # OPTIMIZACIÓN DE QUERIES
    # -------------------------------------------------------------------------

    def get_queryset(self, request):
        """
        Optimiza las consultas del listado para evitar N+1 queries.

        PROPÓSITO:
            El listado muestra servicio, asignado, imágenes y presupuestos.
            Sin optimización, cada fila generaría 4 queries adicionales.

        OPTIMIZACIONES:
            - select_related: Carga servicio y asignado en una sola query
            - prefetch_related: Carga imágenes y presupuestos en 2 queries

        RETORNA:
            QuerySet: Leads con relaciones precargadas.
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'service', 'assigned_to'
        ).prefetch_related(
            'images', 'budgets'
        )

    # -------------------------------------------------------------------------
    # AUDITORÍA AUTOMÁTICA
    # -------------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        """
        Guarda el lead y registra cambios en LeadLog.

        PROPÓSITO:
            Mantener un historial de auditoría de todas las modificaciones
            realizadas desde el panel de administración.

        PARÁMETROS:
            request: Request HTTP con información del usuario
            obj (Lead): Instancia del lead a guardar
            form: Formulario con los datos
            change (bool): True si es edición, False si es creación

        FLUJO:
            1. Si es edición, obtener estado anterior
            2. Comparar campos críticos (status, assigned_to)
            3. Crear LeadLog por cada cambio detectado
            4. Si es creación, registrar log de creación
            5. Guardar el modelo

        NOTA:
            Los signals (log_lead_changes) también detectan cambios, pero
            al guardar desde admin usamos _logging_handled_in_admin para
            que no creen logs: solo los creamos aquí (con request.user).
            Así evitamos duplicados.
        """
        if change:
            # Marcar que los logs se crean aquí (evitar duplicados en signals)
            obj._logging_handled_in_admin = True
            # Obtener estado anterior para comparar
            old_obj = Lead.objects.get(pk=obj.pk)

            # Detectar cambio de estado
            if old_obj.status != obj.status:
                LeadLog.objects.create(
                    lead=obj,
                    user=request.user,
                    action='status_changed',
                    old_value=old_obj.get_status_display(),
                    new_value=obj.get_status_display()
                )

            # Detectar cambio de asignación
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
        if change:
            if getattr(obj, '_logging_handled_in_admin', False):
                delattr(obj, '_logging_handled_in_admin')


# =============================================================================
# ADMIN: LEADIMAGE
# =============================================================================
# Panel separado para gestión de imágenes (opcional, principalmente se usan inlines)

@admin.register(LeadImage)
class LeadImageAdmin(admin.ModelAdmin):
    """
    Panel de administración para imágenes de leads.

    DESCRIPCIÓN:
        Permite gestionar imágenes de forma independiente.
        Útil para ver todas las imágenes del sistema o buscar por lead.

    NOTA:
        El uso principal es desde el inline en LeadAdmin.
        Este admin es complementario para casos especiales.
    """
    list_display = ('id', 'lead', 'image_preview', 'uploaded_at')
    list_filter = ('uploaded_at',)
    readonly_fields = ('uploaded_at', 'image_preview')
    search_fields = ('lead__name', 'lead__email')

    def image_preview(self, obj):
        """Genera miniatura de 200x200px para el listado."""
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
# Panel completo para gestión de presupuestos

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """
    Panel de administración para presupuestos.

    DESCRIPCIÓN:
        Gestión completa de presupuestos con filtros por estado,
        fecha y validez. Permite adjuntar PDFs y asignar automáticamente
        la referencia única.

    CARACTERÍSTICAS:
        - Referencia auto-generada (solo lectura)
        - Badge de color por estado
        - Navegación por fecha (date_hierarchy)
        - Autocomplete para selección de lead
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

    def status_badge(self, obj):
        """
        Genera badge de color según estado del presupuesto.

        COLORES:
            - Borrador: Gris (#9CA3AF)
            - Enviado: Azul (#3B82F6)
            - Aceptado: Verde (#10B981)
            - Rechazado: Rojo (#EF4444)
        """
        colors = {
            'borrador': '#9CA3AF',
            'enviado': '#3B82F6',
            'aceptado': '#10B981',
            'rechazado': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        """
        Asigna automáticamente el usuario creador en nuevos presupuestos.

        PROPÓSITO:
            Registrar quién creó cada presupuesto para trazabilidad.

        FLUJO:
            1. Si es nuevo presupuesto, asignar request.user a created_by
            2. Guardar el modelo (la referencia se genera en Budget.save())
        """
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# ADMIN: LEADLOG (AUDITORÍA)
# =============================================================================
# Panel de solo lectura para consultar el historial de acciones

@admin.register(LeadLog)
class LeadLogAdmin(admin.ModelAdmin):
    """
    Panel de administración para logs de auditoría.

    DESCRIPCIÓN:
        Visualización del historial completo de acciones sobre leads.
        Completamente de solo lectura para preservar la integridad
        de la auditoría.

    CARACTERÍSTICAS:
        - No permite crear ni eliminar registros
        - Filtros por acción, fecha y usuario
        - Búsqueda por lead y valores
        - Navegación por fecha

    PROPÓSITO:
        Permite auditar quién hizo qué y cuándo en el sistema.
        Útil para resolver disputas o analizar el flujo de trabajo.
    """
    list_display = (
        'lead',
        'action',
        'user',
        'old_value',
        'new_value',
        'created_at'
    )
    list_filter = ('action', 'created_at', 'user')
    search_fields = ('lead__name', 'lead__email', 'old_value', 'new_value')
    readonly_fields = (
        'lead', 'user', 'action',
        'old_value', 'new_value', 'created_at'
    )
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Deshabilita creación manual de logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Deshabilita eliminación de logs (preservar auditoría)."""
        return False
