from django.db import models
from django.contrib.auth.models import User


def contact_image_path(instance, filename):
    """
    Genera la ruta donde se guardarán las imágenes:
    media/contactos/2025/01/nombre-archivo.jpg
    """
    from datetime import datetime
    date = datetime.now()
    return f'contactos/{date.year}/{date.month:02d}/{filename}'


class ContactRequest(models.Model):
    """
    Modelo para almacenar las solicitudes de presupuesto
    que llegan desde el formulario de contacto.
    """
    STATUS_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('contactado', 'Contactado'),
        ('presupuestado', 'Presupuestado'),
        ('cerrado', 'Cerrado'),
        ('descartado', 'Descartado'),
    ]

    # Datos del cliente (del formulario)
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre completo'
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    descripcion = models.TextField(
        verbose_name='Descripción del proyecto'
    )

    # Gestión interna
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='nuevo',
        verbose_name='Estado'
    )
    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Asignado a',
        related_name='assigned_requests'
    )
    internal_notes = models.TextField(
        blank=True,
        verbose_name='Notas internas'
    )

    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de presupuesto'
        verbose_name_plural = 'Solicitudes de presupuesto'

    def __str__(self):
        return f"{self.nombre} - {self.get_status_display()} ({self.created_at.strftime('%d/%m/%Y')})"

    def get_image_count(self):
        """Retorna el número de imágenes adjuntas"""
        return self.images.count()
    get_image_count.short_description = 'Imágenes'


class ContactRequestImage(models.Model):
    """
    Modelo para almacenar las imágenes adjuntas a una solicitud de presupuesto.
    Relación 1 a N con ContactRequest.
    """
    contact_request = models.ForeignKey(
        ContactRequest,
        related_name='images',
        on_delete=models.CASCADE,
        verbose_name='Solicitud'
    )
    image = models.ImageField(
        upload_to=contact_image_path,
        verbose_name='Imagen'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de subida'
    )

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = 'Imagen adjunta'
        verbose_name_plural = 'Imágenes adjuntas'

    def __str__(self):
        return f"Imagen de {self.contact_request.nombre} ({self.uploaded_at.strftime('%d/%m/%Y')})"
