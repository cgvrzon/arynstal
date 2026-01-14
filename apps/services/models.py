from django.db import models
from django.utils.text import slugify


class Service(models.Model):
    """
    Catálogo de servicios que ofrece Arynstal.
    Solo lectura para el público, editable desde el admin.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre del servicio'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='URL amigable'
    )
    description = models.TextField(
        verbose_name='Descripción'
    )
    # Campos adicionales recomendados por el documento
    short_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descripción corta',
        help_text='Para listados y SEO'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Icono',
        help_text='Nombre del icono (opcional)'
    )
    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        verbose_name='Imagen representativa'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Mostrar en la web'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el sitio'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generar slug si no existe"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
