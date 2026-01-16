"""
===============================================================================
ARCHIVO: apps/leads/forms.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define los formularios Django para la creación de leads desde el frontend.
    Actúa como capa de validación y presentación entre el HTML y los modelos.

FUNCIONES PRINCIPALES:
    - LeadForm: Formulario ModelForm para capturar datos del cliente

FLUJO EN LA APLICACIÓN:
    1. Usuario accede a /contact/ (web/views.py → contact_us)
    2. Vista renderiza el template con LeadForm vacío
    3. Usuario rellena y envía el formulario (POST)
    4. LeadForm valida los datos (clean_* methods)
    5. Si es válido, se guarda el Lead en BD
    6. Si hay errores, se muestran en el template

PRINCIPIOS DE DISEÑO:
    - Separación de responsabilidades: El form valida, la vista procesa
    - DRY: Los widgets se configuran en __init__ para evitar repetición
    - Validación en capas: Form + Model + BD

RELACIÓN CON OTROS ARCHIVOS:
    - models.py: LeadForm hereda de Lead (ModelForm)
    - views.py: contact_us() instancia y procesa LeadForm
    - templates/pages/contact.html: Renderiza los campos del form

NOTA SOBRE IMÁGENES:
    Las imágenes adjuntas (fotos[]) se manejan directamente en la vista,
    no en este formulario, para mayor flexibilidad en la validación.

===============================================================================
"""

from django import forms
from .models import Lead


# =============================================================================
# FORMULARIO: LEADFORM
# =============================================================================
# Formulario principal para la captación de leads desde el frontend público.
# Utiliza ModelForm de Django para vincular automáticamente con el modelo Lead.

class LeadForm(forms.ModelForm):
    """
    Formulario para crear un Lead desde la página de contacto pública.

    DESCRIPCIÓN:
        Captura los datos básicos del cliente interesado en los servicios.
        Hereda de ModelForm para aprovechar las validaciones del modelo
        y la generación automática de campos.

    CAMPOS INCLUIDOS:
        - name: Nombre completo del cliente
        - phone: Número de teléfono de contacto
        - email: Correo electrónico
        - message: Descripción del proyecto o necesidad

    CAMPOS EXCLUIDOS (manejados en la vista):
        - service: Selección de servicio (opcional, se añade en vista)
        - fotos[]: Imágenes adjuntas (validadas en vista)
        - privacy_accepted: Checkbox RGPD (validado en vista)
        - ip_address, user_agent: Datos técnicos (capturados en vista)

    WIDGETS PERSONALIZADOS:
        Todos los campos utilizan clases Tailwind CSS para mantener
        la coherencia con el diseño del frontend Vite.

    EJEMPLO DE USO EN VISTA:
        >>> form = LeadForm(request.POST)
        >>> if form.is_valid():
        >>>     lead = form.save(commit=False)
        >>>     lead.source = 'web'
        >>>     lead.save()
    """

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN META
    # -------------------------------------------------------------------------
    # Define qué modelo usar y qué campos incluir en el formulario.

    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'message']
        # NOTE: Solo incluimos los campos que el usuario rellena directamente.
        # Otros campos (status, source, assigned_to) se asignan en la vista.

    # -------------------------------------------------------------------------
    # MÉTODO: __init__
    # -------------------------------------------------------------------------

    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario con widgets personalizados.

        PROPÓSITO:
            Configurar los atributos HTML de cada campo para que coincidan
            con el diseño del frontend. Incluye clases Tailwind, placeholders
            e IDs específicos para JavaScript.

        PARÁMETROS:
            *args: Argumentos posicionales (data del POST, files, etc.)
            **kwargs: Argumentos nombrados (instance, prefix, etc.)

        WIDGETS CONFIGURADOS:
            - Clases Tailwind para estilos consistentes
            - Placeholders con ejemplos orientativos
            - IDs para vinculación con labels y JavaScript
            - Tipos HTML5 (tel, email) para validación nativa del navegador

        FLUJO:
            1. Llamar al __init__ del padre para inicialización estándar
            2. Iterar sobre los campos y personalizar sus widgets
            3. Los widgets se aplican al renderizar en el template
        """
        super().__init__(*args, **kwargs)

        # ---------------------------------------------------------------------
        # Campo: name (Nombre completo)
        # ---------------------------------------------------------------------
        # Clases Tailwind para input con focus ring y transiciones.
        # ID 'nombre' coincide con el label del template.

        self.fields['name'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg '
                     'focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent '
                     'transition-all duration-300 text-sm sm:text-base',
            'placeholder': 'Ej: Juan Pérez García',
            'id': 'nombre'
        })

        # ---------------------------------------------------------------------
        # Campo: phone (Teléfono)
        # ---------------------------------------------------------------------
        # type='tel' activa el teclado numérico en móviles.
        # ID 'telefono' para JavaScript de validación en tiempo real.

        self.fields['phone'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg '
                     'focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent '
                     'transition-all duration-300 text-sm sm:text-base',
            'placeholder': 'Ej: 612345678',
            'id': 'telefono',
            'type': 'tel'
        })

        # ---------------------------------------------------------------------
        # Campo: email (Correo electrónico)
        # ---------------------------------------------------------------------
        # type='email' activa validación HTML5 nativa del navegador.

        self.fields['email'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg '
                     'focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent '
                     'transition-all duration-300 text-sm sm:text-base',
            'placeholder': 'Ej: juan@email.com',
            'id': 'email',
            'type': 'email'
        })

        # ---------------------------------------------------------------------
        # Campo: message (Descripción del proyecto)
        # ---------------------------------------------------------------------
        # Textarea con altura fija (6 rows) y redimensionable verticalmente.
        # Placeholder extenso para guiar al usuario sobre qué información dar.

        self.fields['message'].widget = forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg '
                     'focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent '
                     'transition-all duration-300 resize-y text-sm sm:text-base',
            'placeholder': 'Describe tu proyecto: tipo de instalación, '
                           'estado actual, necesidades específicas...',
            'rows': 6,
            'id': 'descripcion'
        })

    # -------------------------------------------------------------------------
    # MÉTODOS DE VALIDACIÓN PERSONALIZADOS
    # -------------------------------------------------------------------------
    # Los métodos clean_<campo> se ejecutan después de la validación básica.
    # Permiten añadir reglas de negocio específicas.

    def clean_name(self) -> str:
        """
        Valida el campo nombre con reglas de negocio.

        VALIDACIONES:
            - Longitud mínima: 3 caracteres (evita iniciales o abreviaturas)

        RETORNA:
            str: El nombre validado y limpio.

        EXCEPCIONES:
            ValidationError: Si el nombre es demasiado corto.

        NOTA:
            El modelo Lead.clean() también valida (mín 2 chars).
            Aquí somos más estrictos (mín 3) para el formulario web.
        """
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError(
                'El nombre debe tener al menos 3 caracteres.'
            )
        return name

    def clean_message(self) -> str:
        """
        Valida el campo mensaje con reglas de negocio.

        VALIDACIONES:
            - Longitud mínima: 20 caracteres (evita mensajes vacíos o spam)
            - Longitud máxima: 1000 caracteres (evita texto excesivo)

        RETORNA:
            str: El mensaje validado y limpio.

        EXCEPCIONES:
            ValidationError: Si el mensaje es demasiado corto o largo.

        PROPÓSITO:
            Asegurar que el cliente proporcione suficiente información
            para que el equipo pueda evaluar la solicitud sin necesidad
            de contactar inmediatamente para más detalles.
        """
        message = self.cleaned_data.get('message')

        # Validar longitud mínima
        if message and len(message) < 20:
            raise forms.ValidationError(
                'La descripción debe tener al menos 20 caracteres.'
            )

        # Validar longitud máxima
        if message and len(message) > 1000:
            raise forms.ValidationError(
                'La descripción no puede superar los 1000 caracteres.'
            )

        return message
