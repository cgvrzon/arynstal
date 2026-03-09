from datetime import date

from PIL import Image

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.leads.validators import validate_image_file
from apps.services.models import Service

# Dimensiones mínimas para imágenes de proyectos (ancho x alto)
MIN_COVER_WIDTH = 800
MIN_COVER_HEIGHT = 400
MIN_IMAGE_WIDTH = 600
MIN_IMAGE_HEIGHT = 400
MIN_DESCRIPTION_LENGTH = 50


class Project(models.Model):
    """Proyecto realizado por Arynstal, visible en la galería pública."""

    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Nombre del proyecto. Breve y descriptivo (ej: "Aerotermia en chalet adosado").',
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='URL amigable',
    )
    description = models.TextField(
        verbose_name='Descripción',
        help_text='Detalla el trabajo realizado: funciones, tareas, materiales, soluciones tecnicas. Se muestra al abrir el proyecto en la web.',
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name='Servicio',
    )
    cover_image = models.ImageField(
        upload_to='projects/%Y/%m/',
        validators=[validate_image_file],
        verbose_name='Imagen de portada',
        help_text='Imagen principal del grid. Min 800x400px. Máx 5MB. JPG, PNG, WEBP.',
    )

    # Detalles para el modal
    area = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Superficie',
        help_text='Ej: 2.500 m²',
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Duración',
        help_text='Ej: 6 meses',
    )
    year = models.PositiveIntegerField(
        verbose_name='Año',
        help_text='Año de realización del proyecto',
    )
    client = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Cliente',
        help_text='Nombre del cliente o empresa. Dejar vacio si es confidencial.',
    )

    # Control
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Mostrar en la galería pública',
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Destacado',
        help_text='Aparece primero en la galería',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')

    class Meta:
        ordering = ['-is_featured', 'order', '-year']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}

        if self.year and self.year > date.today().year:
            errors['year'] = f'El año no puede ser futuro ({self.year}).'

        if self.description and len(self.description.strip()) < MIN_DESCRIPTION_LENGTH:
            errors['description'] = (
                f'La descripción debe tener al menos {MIN_DESCRIPTION_LENGTH} caracteres '
                f'para mostrar el trabajo realizado con detalle.'
            )

        if self.cover_image:
            try:
                img = Image.open(self.cover_image)
                w, h = img.size
                if w < MIN_COVER_WIDTH or h < MIN_COVER_HEIGHT:
                    errors['cover_image'] = (
                        f'La portada debe ser al menos {MIN_COVER_WIDTH}x{MIN_COVER_HEIGHT}px. '
                        f'La imagen subida es {w}x{h}px.'
                    )
            except Exception:
                pass  # validate_image_file ya cubre archivos corruptos

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:90]
            slug = base_slug
            counter = 2
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug[:85]}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_details_list(self):
        """Lista de detalles para el modal (solo los que tienen valor)."""
        details = []
        if self.area:
            details.append(f'Superficie: {self.area}')
        if self.duration:
            details.append(f'Duración: {self.duration}')
        if self.year:
            details.append(f'Año: {self.year}')
        if self.client:
            details.append(f'Cliente: {self.client}')
        return details

    def get_all_image_urls(self):
        """URLs de portada + imágenes adicionales, en orden."""
        urls = [self.cover_image.url]
        urls.extend(
            img.image.url
            for img in self.images.all().order_by('order', 'id')
        )
        return urls


class ProjectImage(models.Model):
    """Imagen adicional de un proyecto (galería del carousel)."""

    MAX_IMAGES_PER_PROJECT = 9

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Proyecto',
    )
    image = models.ImageField(
        upload_to='projects/%Y/%m/',
        validators=[validate_image_file],
        verbose_name='Imagen',
        help_text='Min 600x400px. Máx 5MB. JPG, PNG, WEBP.',
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Texto alternativo',
        help_text='Describe la imagen brevemente (ej: "Vista del salon con suelo radiante"). Mejora accesibilidad y SEO.',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Subido',
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Imagen del proyecto'
        verbose_name_plural = 'Imágenes del proyecto'

    def __str__(self):
        return f'{self.project.title} - Imagen {self.order}'

    def clean(self):
        super().clean()
        errors = {}

        if not self.pk:
            count = ProjectImage.objects.filter(project=self.project).count()
            if count >= self.MAX_IMAGES_PER_PROJECT:
                raise ValidationError(
                    f'Máximo {self.MAX_IMAGES_PER_PROJECT} imágenes adicionales '
                    f'por proyecto (+ portada = {self.MAX_IMAGES_PER_PROJECT + 1} total).'
                )

        if self.image:
            try:
                img = Image.open(self.image)
                w, h = img.size
                if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
                    errors['image'] = (
                        f'La imagen debe ser al menos {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}px. '
                        f'La imagen subida es {w}x{h}px.'
                    )
            except Exception:
                pass

        if errors:
            raise ValidationError(errors)
