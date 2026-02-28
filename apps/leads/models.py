"""
===============================================================================
ARCHIVO: apps/leads/models.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Este archivo define los modelos de datos principales del sistema CRM.
    Es el núcleo de la aplicación donde se almacena toda la información
    de clientes potenciales (leads), sus imágenes adjuntas, presupuestos
    generados y el historial de acciones (auditoría).

FUNCIONES PRINCIPALES:
    - Lead: Modelo principal que representa a un cliente potencial
    - LeadImage: Almacena imágenes adjuntas a cada lead
    - Budget: Gestiona presupuestos asociados a leads
    - LeadLog: Registro de auditoría automática de acciones

FLUJO EN LA APLICACIÓN:
    1. Usuario envía formulario de contacto (web/views.py → contact_us)
    2. Se crea un Lead con estado 'nuevo' y origen 'web'
    3. Se adjuntan imágenes si las hay (LeadImage)
    4. Se disparan signals para crear LeadLog automáticamente
    5. Personal de oficina gestiona el lead desde el admin
    6. Se crean presupuestos (Budget) cuando procede
    7. Cada cambio queda registrado en LeadLog

RELACIONES ENTRE MODELOS:
    Lead ──┬── LeadImage (1:N) - Un lead puede tener hasta 5 imágenes
           ├── Budget (1:N) - Un lead puede tener múltiples presupuestos
           ├── LeadLog (1:N) - Historial completo de acciones
           └── Service (N:1) - Cada lead puede estar asociado a un servicio

DEPENDENCIAS:
    - apps.services.models.Service: Para la relación con servicios
    - apps.leads.validators: Validadores de archivos (imágenes, PDFs)
    - django.contrib.auth.models.User: Para asignación y auditoría

===============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from .validators import validate_image_file, validate_pdf_file


# =============================================================================
# FUNCIONES AUXILIARES - RUTAS DE ARCHIVOS
# =============================================================================
# Estas funciones generan rutas organizadas por fecha para almacenar archivos.
# Facilitan la organización y el mantenimiento del sistema de archivos.

def lead_image_path(instance, filename):
    """
    Genera la ruta de almacenamiento para imágenes de leads.

    PROPÓSITO:
        Organizar las imágenes en carpetas por año/mes para evitar
        directorios con demasiados archivos y facilitar backups.

    PARÁMETROS:
        instance (LeadImage): Instancia del modelo LeadImage que se está guardando.
                              Permite acceder al lead asociado si fuera necesario.
        filename (str): Nombre original del archivo subido por el usuario.

    RETORNA:
        str: Ruta relativa donde se guardará el archivo.
             Ejemplo: 'leads/2025/01/foto_instalacion.jpg'

    FLUJO:
        1. Se llama automáticamente cuando Django guarda un ImageField
        2. Obtiene la fecha actual para crear la estructura de carpetas
        3. Retorna la ruta que Django usará en MEDIA_ROOT

    UBICACIÓN EN EL SISTEMA:
        Los archivos se guardan en: MEDIA_ROOT/leads/YYYY/MM/filename
        En desarrollo: media/leads/2025/01/filename.jpg
    """
    date = timezone.now()
    return f'leads/{date.year}/{date.month:02d}/{filename}'


def budget_file_path(instance, filename):
    """
    Genera la ruta de almacenamiento para archivos PDF de presupuestos.

    PROPÓSITO:
        Organizar los PDFs de presupuestos en carpetas por año/mes.
        Separados de las imágenes de leads para mejor organización.

    PARÁMETROS:
        instance (Budget): Instancia del modelo Budget que se está guardando.
                           Permite acceder al lead y referencia si fuera necesario.
        filename (str): Nombre original del archivo PDF subido.

    RETORNA:
        str: Ruta relativa donde se guardará el archivo.
             Ejemplo: 'budgets/2025/01/presupuesto_aerotermia.pdf'

    UBICACIÓN EN EL SISTEMA:
        Los archivos se guardan en: MEDIA_ROOT/budgets/YYYY/MM/filename
    """
    date = timezone.now()
    return f'budgets/{date.year}/{date.month:02d}/{filename}'


# =============================================================================
# MODELO PRINCIPAL: LEAD
# =============================================================================
# El Lead es el núcleo del sistema CRM. Representa a cada persona que
# solicita información o presupuesto a través del formulario web,
# llamada telefónica u otros canales.

class Lead(models.Model):
    """
    MODELO: Lead (Cliente Potencial)

    DESCRIPCIÓN:
        Representa a cada persona interesada en los servicios de Arynstal.
        Almacena sus datos de contacto, el servicio de interés, el mensaje
        descriptivo y toda la información necesaria para el seguimiento comercial.

    CICLO DE VIDA DE UN LEAD:
        nuevo → contactado → presupuestado → cerrado
                    ↓              ↓
               descartado     descartado

    CAMPOS PRINCIPALES:
        - Información del cliente: name, email, phone, location
        - Solicitud: service, message
        - Gestión: status, source, assigned_to, notes
        - Seguridad/RGPD: privacy_accepted, ip_address, user_agent
        - Preferencias: preferred_contact, urgency

    ÍNDICES DE BASE DE DATOS:
        - (status, created_at): Para filtrar leads por estado ordenados por fecha
        - (email): Para búsquedas rápidas y detección de duplicados
    """

    # -------------------------------------------------------------------------
    # CONSTANTES - OPCIONES DE CAMPOS
    # -------------------------------------------------------------------------
    # Definidas como listas de tuplas para los campos choices de Django.
    # El primer elemento es el valor almacenado en BD, el segundo es la etiqueta visible.

    STATUS_CHOICES = [
        ('nuevo', 'Nuevo'),              # Lead recién llegado, sin gestionar
        ('contactado', 'Contactado'),    # Se ha contactado con el cliente
        ('presupuestado', 'Presupuestado'),  # Se ha enviado presupuesto
        ('cerrado', 'Cerrado'),          # Trabajo realizado o contratado
        ('descartado', 'Descartado'),    # Lead no viable (no interesado, spam, etc.)
    ]

    SOURCE_CHOICES = [
        ('web', 'Formulario web'),       # Enviado desde la página de contacto
        ('telefono', 'Llamada telefónica'),  # Recibido por teléfono
        ('recomendacion', 'Recomendación'),  # Cliente referido por otro
        ('otro', 'Otro'),                # Otros canales (ferias, redes sociales, etc.)
    ]

    URGENCY_CHOICES = [
        ('normal', 'Normal'),            # Solicitud estándar
        ('urgente', 'Urgente'),          # Cliente con necesidad inmediata
    ]

    CONTACT_CHOICES = [
        ('email', 'Email'),              # Prefiere contacto por email
        ('phone', 'Teléfono'),           # Prefiere llamada telefónica
        ('whatsapp', 'WhatsApp'),        # Prefiere mensajería WhatsApp
    ]

    # -------------------------------------------------------------------------
    # SECCIÓN 1: INFORMACIÓN DEL CLIENTE
    # -------------------------------------------------------------------------
    # Datos personales necesarios para identificar y contactar al cliente.
    # Estos campos son obligatorios (excepto location) y se validan en clean().

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

    # -------------------------------------------------------------------------
    # SECCIÓN 2: RELACIÓN CON SERVICIO
    # -------------------------------------------------------------------------
    # Vincula el lead con un servicio específico del catálogo.
    # Es opcional porque el cliente puede no saber qué servicio necesita.

    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,  # Si se elimina el servicio, el lead permanece
        null=True,
        blank=True,
        verbose_name='Servicio de interés',
        related_name='leads'  # Permite: servicio.leads.all()
    )

    # -------------------------------------------------------------------------
    # SECCIÓN 3: DESCRIPCIÓN DE LA SOLICITUD
    # -------------------------------------------------------------------------
    # El mensaje del cliente describiendo lo que necesita.
    # Campo fundamental para entender el alcance del trabajo.

    message = models.TextField(
        verbose_name='Mensaje/Descripción'
    )

    # -------------------------------------------------------------------------
    # SECCIÓN 4: METADATOS DEL LEAD
    # -------------------------------------------------------------------------
    # Información sobre el origen y estado actual del lead.
    # Fundamental para el seguimiento y las estadísticas.

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

    # -------------------------------------------------------------------------
    # SECCIÓN 5: GESTIÓN INTERNA
    # -------------------------------------------------------------------------
    # Campos para el equipo de oficina. Permite asignar leads a empleados
    # y añadir notas privadas de seguimiento.

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # Si se elimina el usuario, el lead permanece
        null=True,
        blank=True,
        verbose_name='Asignado a',
        related_name='assigned_leads'  # Permite: usuario.assigned_leads.all()
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas internas'
    )

    # -------------------------------------------------------------------------
    # SECCIÓN 6: CAMPOS DE SEGURIDAD Y RGPD
    # -------------------------------------------------------------------------
    # Información técnica para cumplimiento legal y detección de spam.
    # ip_address y user_agent ayudan a identificar envíos sospechosos.

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

    # -------------------------------------------------------------------------
    # SECCIÓN 7: PREFERENCIAS DE CONTACTO
    # -------------------------------------------------------------------------
    # Cómo y con qué urgencia el cliente desea ser contactado.

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

    # -------------------------------------------------------------------------
    # SECCIÓN 8: TIMESTAMPS
    # -------------------------------------------------------------------------
    # Fechas automáticas de creación y última modificación.
    # auto_now_add: Se establece al crear, no se modifica después.
    # auto_now: Se actualiza cada vez que se guarda el modelo.

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de entrada'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificación'
    )

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DEL MODELO (Meta)
    # -------------------------------------------------------------------------

    class Meta:
        ordering = ['-created_at']  # Más recientes primero
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            # Índice compuesto para consultas frecuentes del admin
            # Ejemplo: Lead.objects.filter(status='nuevo').order_by('-created_at')
            models.Index(fields=['status', 'created_at']),
            # Índice para búsqueda por email (detección de duplicados)
            models.Index(fields=['email']),
        ]

    # -------------------------------------------------------------------------
    # MÉTODOS DEL MODELO
    # -------------------------------------------------------------------------

    def __str__(self):
        """
        Representación en texto del lead para el admin y logs.
        Formato: "Juan Pérez - Nuevo (15/01/2025)"
        """
        return f"{self.name} - {self.get_status_display()} ({self.created_at.strftime('%d/%m/%Y')})"

    def clean(self):
        """
        Validaciones personalizadas del modelo.

        PROPÓSITO:
            Asegurar la integridad de los datos antes de guardar.
            Se ejecuta automáticamente en formularios y desde el admin.

        VALIDACIONES:
            1. Nombre: Mínimo 2 caracteres
            2. Teléfono: Entre 9 y 15 dígitos
            3. Mensaje: Mínimo 20 caracteres (evita spam y mensajes vacíos)

        EXCEPCIONES:
            ValidationError: Si alguna validación falla, con el campo específico.

        FLUJO:
            1. Se llama desde LeadForm.is_valid() o admin save
            2. Valida cada campo secuencialmente
            3. Si falla, lanza ValidationError que se muestra al usuario
        """
        # Validar nombre mínimo
        if len(self.name) < 2:
            raise ValidationError({'name': 'El nombre debe tener al menos 2 caracteres'})

        # Validar teléfono (extraer solo dígitos para flexibilidad de formato)
        phone_digits = ''.join(filter(str.isdigit, self.phone))
        if not (9 <= len(phone_digits) <= 15):
            raise ValidationError({'phone': 'El teléfono debe tener entre 9 y 15 dígitos'})

        # Validar mensaje mínimo
        if len(self.message) < 20:
            raise ValidationError({'message': 'El mensaje debe tener al menos 20 caracteres'})

    def get_images_count(self):
        """
        Retorna el número de imágenes adjuntas al lead.

        USO:
            Se muestra en el listado del admin como columna.
            Permite ver rápidamente qué leads tienen documentación visual.

        RETORNA:
            int: Cantidad de LeadImage asociados a este lead.
        """
        return self.images.count()
    get_images_count.short_description = 'Imágenes'  # Etiqueta en admin

    def get_budgets_count(self):
        """
        Retorna el número de presupuestos asociados al lead.

        USO:
            Se muestra en el listado del admin como columna.
            Permite identificar leads con presupuestos pendientes.

        RETORNA:
            int: Cantidad de Budget asociados a este lead.
        """
        return self.budgets.count()
    get_budgets_count.short_description = 'Presupuestos'  # Etiqueta en admin


# =============================================================================
# MODELO: LEADIMAGE
# =============================================================================
# Almacena imágenes adjuntas por los clientes en el formulario de contacto.
# Permite documentar visualmente el estado de instalaciones, problemas, etc.

class LeadImage(models.Model):
    """
    MODELO: LeadImage (Imagen de Lead)

    DESCRIPCIÓN:
        Almacena las imágenes que los clientes adjuntan al enviar
        el formulario de contacto. Útil para que el técnico vea
        el estado actual de una instalación antes de visitarla.

    RESTRICCIONES:
        - Máximo 5 imágenes por lead (validado en clean())
        - Formatos permitidos: JPG, PNG, WEBP
        - Tamaño máximo: 5MB por imagen
        - Validación de magic bytes (seguridad contra archivos maliciosos)

    RELACIÓN:
        Pertenece a un Lead (ForeignKey con CASCADE).
        Si se elimina el lead, se eliminan sus imágenes.
    """

    # Relación con el lead padre
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,  # Eliminar imágenes si se elimina el lead
        related_name='images',     # Permite: lead.images.all()
        verbose_name='Lead'
    )

    # Campo de imagen con validación
    image = models.ImageField(
        upload_to=lead_image_path,  # Función que genera la ruta
        verbose_name='Imagen',
        validators=[validate_image_file],  # Valida tipo y tamaño
        help_text='Máximo 5MB. Formatos: JPG, PNG, WEBP'
    )

    # Timestamp de subida
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de subida'
    )

    class Meta:
        ordering = ['uploaded_at']  # Más antiguas primero (orden de subida)
        verbose_name = 'Imagen de lead'
        verbose_name_plural = 'Imágenes de leads'

    def __str__(self):
        """Representación: 'Imagen de Juan Pérez (15/01/2025)'"""
        return f"Imagen de {self.lead.name} ({self.uploaded_at.strftime('%d/%m/%Y')})"

    def clean(self):
        """
        Valida que no se excedan las 5 imágenes por lead.

        LÓGICA:
            - Solo valida en creación (no en actualización, por eso self.pk)
            - Cuenta las imágenes existentes del lead
            - Si ya hay 5, rechaza la nueva

        EXCEPCIÓN:
            ValidationError si se intenta subir más de 5 imágenes.
        """
        if self.lead and self.lead.images.count() >= 5 and not self.pk:
            raise ValidationError('No se pueden adjuntar más de 5 imágenes por lead')


# =============================================================================
# MODELO: BUDGET
# =============================================================================
# Gestiona los presupuestos generados para cada lead.
# Permite seguimiento del proceso comercial y control financiero.

class Budget(models.Model):
    """
    MODELO: Budget (Presupuesto)

    DESCRIPCIÓN:
        Representa un presupuesto enviado a un cliente potencial.
        Permite hacer seguimiento de propuestas económicas y su estado.
        Genera referencias únicas automáticamente (ARYN-2025-001).

    CICLO DE VIDA:
        borrador → enviado → aceptado
                      ↓
                  rechazado

    CARACTERÍSTICAS:
        - Referencia auto-generada única por año
        - Soporte para archivo PDF adjunto
        - Fecha de validez configurable
        - Trazabilidad de quién lo creó
    """

    STATUS_CHOICES = [
        ('borrador', 'Borrador'),    # En preparación, no enviado
        ('enviado', 'Enviado'),      # Enviado al cliente
        ('aceptado', 'Aceptado'),    # Cliente ha aceptado
        ('rechazado', 'Rechazado'),  # Cliente ha rechazado
    ]

    # -------------------------------------------------------------------------
    # RELACIÓN CON LEAD
    # -------------------------------------------------------------------------

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,  # Eliminar presupuestos si se elimina el lead
        related_name='budgets',    # Permite: lead.budgets.all()
        verbose_name='Lead'
    )

    # -------------------------------------------------------------------------
    # DATOS DEL PRESUPUESTO
    # -------------------------------------------------------------------------

    reference = models.CharField(
        max_length=20,
        unique=True,               # No puede haber duplicados
        verbose_name='Referencia',
        help_text='Código único: ARYN-2025-001'
    )
    description = models.TextField(
        verbose_name='Descripción del trabajo'
    )
    amount = models.DecimalField(
        max_digits=10,             # Hasta 99.999.999,99€
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

    # -------------------------------------------------------------------------
    # ARCHIVO PDF
    # -------------------------------------------------------------------------

    file = models.FileField(
        upload_to=budget_file_path,  # Función que genera la ruta
        blank=True,
        verbose_name='Archivo PDF',
        validators=[validate_pdf_file],  # Valida tipo y tamaño
        help_text='Presupuesto en PDF. Máximo 10MB'
    )

    # -------------------------------------------------------------------------
    # AUDITORÍA
    # -------------------------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # Mantener presupuesto si se elimina usuario
        null=True,
        verbose_name='Creado por',
        related_name='created_budgets'  # Permite: usuario.created_budgets.all()
    )

    class Meta:
        ordering = ['-created_at']  # Más recientes primero
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'

    def __str__(self):
        """Representación: 'ARYN-2025-001 - Juan Pérez (8500.00€)'"""
        return f"{self.reference} - {self.lead.name} ({self.amount}€)"

    def save(self, *args, **kwargs):
        """
        Guarda el presupuesto, generando referencia automática si no existe.

        PROPÓSITO:
            Asegurar que cada presupuesto tenga una referencia única
            siguiendo el formato: ARYN-{AÑO}-{NÚMERO_SECUENCIAL}

        ALGORITMO DE GENERACIÓN:
            1. Si ya tiene referencia, no hacer nada
            2. Obtener el año actual
            3. Buscar el último presupuesto del año
            4. Incrementar el número o empezar en 001
            5. Generar la referencia con formato padded (001, 002, etc.)

        EJEMPLO:
            - Primer presupuesto de 2025: ARYN-2025-001
            - Siguiente: ARYN-2025-002
            - Primer presupuesto de 2026: ARYN-2026-001

        PARÁMETROS:
            *args, **kwargs: Argumentos estándar de Django save()
        """
        if not self.reference:
            year = datetime.now().year

            # Buscar el último presupuesto del año actual
            last_budget = Budget.objects.filter(
                reference__startswith=f'ARYN-{year}-'
            ).order_by('-reference').first()

            if last_budget:
                # Extraer el número y sumar 1
                last_number = int(last_budget.reference.split('-')[-1])
                new_number = last_number + 1
            else:
                # Primer presupuesto del año
                new_number = 1

            # Generar referencia con número padded a 3 dígitos
            self.reference = f'ARYN-{year}-{new_number:03d}'

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validaciones personalizadas del presupuesto.

        VALIDACIONES:
            1. Importe debe ser positivo (mayor que 0)
            2. Fecha de validez debe ser futura (si se especifica)

        EXCEPCIONES:
            ValidationError con el campo específico que falló.
        """
        # Validar importe positivo
        if self.amount and self.amount <= 0:
            raise ValidationError({'amount': 'El importe debe ser mayor que 0'})

        # Validar fecha futura
        if self.valid_until and self.valid_until < timezone.now().date():
            raise ValidationError({'valid_until': 'La fecha de validez debe ser futura'})


# =============================================================================
# MODELO: LEADLOG
# =============================================================================
# Sistema de auditoría automática. Registra todas las acciones sobre leads.
# Se alimenta mediante signals (ver signals.py).

class LeadLog(models.Model):
    """
    MODELO: LeadLog (Registro de Auditoría)

    DESCRIPCIÓN:
        Registra automáticamente todas las acciones realizadas sobre un lead.
        Permite trazabilidad completa: quién hizo qué y cuándo.
        Se crea automáticamente mediante signals (ver signals.py).

    TIPOS DE ACCIONES:
        - created: Lead creado (desde web o admin)
        - status_changed: Cambio de estado (nuevo → contactado, etc.)
        - assigned: Lead asignado a un empleado
        - noted: Nota interna añadida
        - updated: Otros campos modificados

    USO EN AUDITORÍAS:
        Permite responder preguntas como:
        - ¿Cuándo se contactó con este cliente?
        - ¿Quién cambió el estado a 'descartado'?
        - ¿Cuántas veces se ha modificado este lead?
    """

    ACTION_CHOICES = [
        ('created', 'Creado'),
        ('status_changed', 'Estado cambiado'),
        ('assigned', 'Asignado'),
        ('noted', 'Nota añadida'),
        ('updated', 'Actualizado'),
    ]

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,  # Eliminar logs si se elimina el lead
        related_name='logs',       # Permite: lead.logs.all()
        verbose_name='Lead'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # Mantener log si se elimina usuario
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Quién realizó la acción'
    )

    # -------------------------------------------------------------------------
    # DATOS DE LA ACCIÓN
    # -------------------------------------------------------------------------

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
        ordering = ['-created_at']  # Más recientes primero
        verbose_name = 'Log de lead'
        verbose_name_plural = 'Logs de leads'

    def __str__(self):
        """Representación: 'Juan Pérez - Estado cambiado (15/01/2025 10:30)'"""
        return f"{self.lead.name} - {self.get_action_display()} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"
