"""
===============================================================================
ARCHIVO: apps/services/models.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define el modelo Service que representa el catálogo de servicios
    que ofrece Arynstal. Este catálogo es gestionado desde el admin
    y se muestra en la página pública de servicios.

FUNCIONES PRINCIPALES:
    - Service: Modelo único para el catálogo de servicios

FLUJO EN LA APLICACIÓN:
    1. Admin crea/edita servicios desde /admynstal/
    2. Vista services() carga Service.objects.filter(is_active=True)
    3. Template services.html renderiza el listado
    4. Usuarios pueden seleccionar un servicio en el formulario de contacto
    5. Lead.service almacena la referencia al servicio seleccionado

RELACIÓN CON OTROS MODELOS:
    Service ←── Lead.service (1:N)
    Un servicio puede tener múltiples leads interesados.
    Si se elimina un servicio, los leads mantienen service=NULL.

CARACTERÍSTICAS:
    - Slug auto-generado para URLs amigables (SEO)
    - Campo order para controlar el orden de visualización
    - is_active para ocultar servicios sin eliminarlos
    - Imagen opcional con validación de seguridad

===============================================================================
"""

from django.db import models
from django.utils.text import slugify
from apps.leads.validators import validate_image_file


# =============================================================================
# MODELO: SERVICE
# =============================================================================

class Service(models.Model):
    """
    Representa un servicio del catálogo de Arynstal.

    DESCRIPCIÓN:
        Define cada tipo de servicio que la empresa ofrece:
        aerotermia, aire acondicionado, domótica, instalaciones
        eléctricas, reformas, etc.

    CAMPOS PRINCIPALES:
        - name: Nombre del servicio
        - slug: URL amigable (auto-generado)
        - description: Descripción completa
        - short_description: Descripción corta para listados
        - is_active: Controla visibilidad en la web
        - order: Orden de aparición

    USOS EN LA APLICACIÓN:
        1. Página de servicios: Lista todos los activos
        2. Formulario de contacto: Selector de servicio
        3. Admin leads: Filtro por servicio
        4. Estadísticas: Leads por tipo de servicio

    EJEMPLO DE USO:
        >>> service = Service.objects.create(
        ...     name='Aerotermia',
        ...     description='Instalación de sistemas de aerotermia...',
        ...     is_active=True,
        ...     order=1
        ... )
        >>> print(service.slug)  # 'aerotermia'
    """

    # -------------------------------------------------------------------------
    # CAMPOS DE IDENTIFICACIÓN
    # -------------------------------------------------------------------------

    name = models.CharField(
        max_length=100,
        verbose_name='Nombre del servicio'
    )

    slug = models.SlugField(
        unique=True,
        verbose_name='URL amigable'
        # NOTA: Se auto-genera en save() si está vacío
    )

    # -------------------------------------------------------------------------
    # CAMPOS DE CONTENIDO
    # -------------------------------------------------------------------------

    description = models.TextField(
        verbose_name='Descripción'
        # Descripción completa para la página de detalle del servicio
    )

    short_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descripción corta',
        help_text='Para listados y SEO'
        # Se usa en cards, meta descriptions, etc.
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Icono',
        help_text='Nombre del icono (opcional)'
        # Permite usar iconos de librerías como Font Awesome, Heroicons, etc.
    )

    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        verbose_name='Imagen representativa',
        validators=[validate_image_file],
        help_text='Máximo 5MB. Formatos: JPG, PNG, WEBP'
        # Se guarda en: MEDIA_ROOT/services/nombre_imagen.jpg
    )

    # -------------------------------------------------------------------------
    # CAMPOS DE CONTROL
    # -------------------------------------------------------------------------

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Mostrar en la web'
        # Permite ocultar servicios sin eliminarlos
        # Útil para servicios estacionales o descontinuados
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el sitio'
        # Menor número = aparece primero
        # Permite reorganizar servicios sin editar código
    )

    # -------------------------------------------------------------------------
    # TIMESTAMPS
    # -------------------------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN META
    # -------------------------------------------------------------------------

    class Meta:
        ordering = ['order', 'name']  # Primero por orden, luego alfabético
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    # -------------------------------------------------------------------------
    # MÉTODOS
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        """Representación en texto: 'Aerotermia'"""
        return self.name

    def save(self, *args, **kwargs):
        """
        Guarda el servicio, generando slug automáticamente si no existe.

        PROPÓSITO:
            Asegurar que cada servicio tenga un slug único para URLs.

        ALGORITMO:
            1. Si no hay slug, generarlo desde el nombre
            2. slugify() convierte 'Aire Acondicionado' → 'aire-acondicionado'
            3. Guardar el modelo

        NOTA:
            El campo slug tiene unique=True, por lo que si hay conflicto
            Django lanzará IntegrityError. En producción, considerar
            añadir sufijo numérico para evitar conflictos.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
