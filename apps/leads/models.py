from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime


def lead_image_path(instance, filename):
    """Genera ruta para imágenes de leads: leads/2025/01/filename.jpg"""
    date = timezone.now()
    return f'leads/{date.year}/{date.month:02d}/{filename}'


def budget_file_path(instance, filename):
    """Genera ruta para archivos de presupuestos: budgets/2025/01/filename.pdf"""
    date = timezone.now()
    return f'budgets/{date.year}/{date.month:02d}/{filename}'


class Lead(models.Model):
    """
    Núcleo del sistema. Representa cada persona que solicita información o presupuesto.
    Equivalente mejorado del antiguo ContactRequest.
    """
    STATUS_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('contactado', 'Contactado'),
        ('presupuestado', 'Presupuestado'),
        ('cerrado', 'Cerrado'),
        ('descartado', 'Descartado'),
    ]

    SOURCE_CHOICES = [
        ('web', 'Formulario web'),
        ('telefono', 'Llamada telefónica'),
        ('recomendacion', 'Recomendación'),
        ('otro', 'Otro'),
    ]

    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgente', 'Urgente'),
    ]

    CONTACT_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('whatsapp', 'WhatsApp'),
    ]

    # Información del cliente
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre completo'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono'
    )
    location = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Ubicación',
        help_text='Ciudad o zona'
    )

    # Relación con servicio
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Servicio de interés',
        related_name='leads'
    )

    # Descripción de la solicitud
    message = models.TextField(
        verbose_name='Mensaje/Descripción'
    )

    # Metadatos del lead
    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
        default='web',
        verbose_name='Origen'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='nuevo',
        verbose_name='Estado'
    )

    # Gestión interna
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Asignado a',
        related_name='assigned_leads'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas internas'
    )

    # Campos adicionales recomendados
    privacy_accepted = models.BooleanField(
        default=False,
        verbose_name='Privacidad aceptada',
        help_text='Aceptación RGPD'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='IP del visitante (anti-spam)'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User Agent',
        help_text='Navegador del visitante'
    )
    preferred_contact = models.CharField(
        max_length=20,
        choices=CONTACT_CHOICES,
        default='email',
        verbose_name='Contacto preferido'
    )
    urgency = models.CharField(
        max_length=20,
        choices=URGENCY_CHOICES,
        default='normal',
        blank=True,
        verbose_name='Urgencia'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de entrada'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificación'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()} ({self.created_at.strftime('%d/%m/%Y')})"

    def clean(self):
        """Validaciones personalizadas"""
        # Validar nombre
        if len(self.name) < 2:
            raise ValidationError({'name': 'El nombre debe tener al menos 2 caracteres'})

        # Validar teléfono
        phone_digits = ''.join(filter(str.isdigit, self.phone))
        if not (9 <= len(phone_digits) <= 15):
            raise ValidationError({'phone': 'El teléfono debe tener entre 9 y 15 dígitos'})

        # Validar mensaje
        if len(self.message) < 20:
            raise ValidationError({'message': 'El mensaje debe tener al menos 20 caracteres'})

    def get_images_count(self):
        """Retorna el número de imágenes adjuntas"""
        return self.images.count()
    get_images_count.short_description = 'Imágenes'

    def get_budgets_count(self):
        """Retorna el número de presupuestos asociados"""
        return self.budgets.count()
    get_budgets_count.short_description = 'Presupuestos'


class LeadImage(models.Model):
    """
    Imágenes adjuntas a un lead.
    Fotos de instalaciones existentes, problemas, etc.
    """
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Lead'
    )
    image = models.ImageField(
        upload_to=lead_image_path,
        verbose_name='Imagen'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de subida'
    )

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = 'Imagen de lead'
        verbose_name_plural = 'Imágenes de leads'

    def __str__(self):
        return f"Imagen de {self.lead.name} ({self.uploaded_at.strftime('%d/%m/%Y')})"

    def clean(self):
        """Validar que no se superen las 5 imágenes por lead"""
        if self.lead and self.lead.images.count() >= 5 and not self.pk:
            raise ValidationError('No se pueden adjuntar más de 5 imágenes por lead')


class Budget(models.Model):
    """
    Presupuestos asociados a leads.
    Permite seguimiento de propuestas y control financiero.
    """
    STATUS_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='Lead'
    )
    reference = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Referencia',
        help_text='Código único: ARYN-2025-001'
    )
    description = models.TextField(
        verbose_name='Descripción del trabajo'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Importe (€)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='borrador',
        verbose_name='Estado'
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name='Válido hasta'
    )
    file = models.FileField(
        upload_to=budget_file_path,
        blank=True,
        verbose_name='Archivo PDF',
        help_text='Presupuesto en PDF'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Creado por',
        related_name='created_budgets'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'

    def __str__(self):
        return f"{self.reference} - {self.lead.name} ({self.amount}€)"

    def save(self, *args, **kwargs):
        """Auto-generar referencia si no existe"""
        if not self.reference:
            year = datetime.now().year
            # Obtener el último número de presupuesto del año
            last_budget = Budget.objects.filter(
                reference__startswith=f'ARYN-{year}-'
            ).order_by('-reference').first()

            if last_budget:
                last_number = int(last_budget.reference.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.reference = f'ARYN-{year}-{new_number:03d}'

        super().save(*args, **kwargs)

    def clean(self):
        """Validaciones personalizadas"""
        # Validar que el importe sea positivo
        if self.amount and self.amount <= 0:
            raise ValidationError({'amount': 'El importe debe ser mayor que 0'})

        # Validar que valid_until sea fecha futura
        if self.valid_until and self.valid_until < timezone.now().date():
            raise ValidationError({'valid_until': 'La fecha de validez debe ser futura'})


class LeadLog(models.Model):
    """
    Registro de auditoría para leads.
    Registra automáticamente todas las acciones sobre un lead.
    """
    ACTION_CHOICES = [
        ('created', 'Creado'),
        ('status_changed', 'Estado cambiado'),
        ('assigned', 'Asignado'),
        ('noted', 'Nota añadida'),
        ('updated', 'Actualizado'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Lead'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Quién realizó la acción'
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name='Acción'
    )
    old_value = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Valor anterior'
    )
    new_value = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Valor nuevo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de lead'
        verbose_name_plural = 'Logs de leads'

    def __str__(self):
        return f"{self.lead.name} - {self.get_action_display()} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"
