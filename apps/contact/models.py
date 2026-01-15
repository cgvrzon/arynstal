"""
App contact - DEPRECADA

Esta app ha sido reemplazada por la app 'leads'.
Se mantiene por compatibilidad con datos existentes.
NO usar para nuevo desarrollo.

Para gestionar contactos, usar apps.leads.models.Lead
"""
import warnings
from django.db import models


class ContactMessage(models.Model):
    """
    DEPRECADO: Usar Lead en su lugar.

    Mensajes genéricos del formulario de contacto.
    Para consultas que no son solicitudes de presupuesto.

    .. deprecated::
        Esta clase está obsoleta. Usar `apps.leads.models.Lead` para
        nuevos contactos. Esta clase se mantiene solo para acceder
        a datos históricos.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Asunto'
    )
    message = models.TextField(
        verbose_name='Mensaje'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Leído'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de envío'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje de contacto'
        verbose_name_plural = 'Mensajes de contacto'

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.created_at.strftime('%d/%m/%Y')})"

    def mark_as_read(self):
        """Marca el mensaje como leído"""
        self.is_read = True
        self.save()

    def mark_as_unread(self):
        """Marca el mensaje como no leído"""
        self.is_read = False
        self.save()
