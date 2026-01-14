from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from .models import ContactRequest


class ContactRequestForm(forms.ModelForm):
    """
    Formulario para solicitudes de presupuesto.
    Incluye validaciones tanto de campos de texto como de imágenes.
    """

    # Campo adicional para manejar múltiples imágenes
    # Nota: El atributo 'multiple' se añade directamente en el template HTML
    images = forms.FileField(
        widget=forms.FileInput(attrs={
            'accept': 'image/jpeg,image/png,image/jpg,image/webp',
            'id': 'fotos'
        }),
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
        help_text='Máximo 5 fotos. JPG, PNG o WEBP. Máximo 5MB cada una.',
        label='Fotografías (opcional)'
    )

    # Campo checkbox de privacidad (no se guarda en BD, solo valida)
    privacidad = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'Debes aceptar la política de privacidad'
        },
        label='Acepto la política de privacidad'
    )

    class Meta:
        model = ContactRequest
        fields = ['nombre', 'telefono', 'email', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300',
                'placeholder': 'Ej: Juan Pérez García'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300',
                'placeholder': 'Ej: 612345678',
                'pattern': '[0-9]{9,15}'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300',
                'placeholder': 'Ej: juan@email.com'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300 resize-y',
                'rows': 6,
                'placeholder': 'Describe tu proyecto: tipo de instalación, estado actual, necesidades específicas...'
            }),
        }
        labels = {
            'nombre': 'Nombre completo *',
            'telefono': 'Teléfono *',
            'email': 'Email *',
            'descripcion': 'Descripción del proyecto *',
        }
        help_texts = {
            'descripcion': 'Mínimo 20 caracteres. Sé lo más específico posible.',
        }

    def clean_nombre(self):
        """Valida el campo nombre"""
        nombre = self.cleaned_data.get('nombre', '').strip()

        if not nombre:
            raise ValidationError('El nombre es obligatorio')

        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres')

        if len(nombre) > 100:
            raise ValidationError('El nombre no puede superar 100 caracteres')

        # Validar que solo contenga letras y espacios
        if not all(c.isalpha() or c.isspace() for c in nombre):
            raise ValidationError('El nombre solo puede contener letras y espacios')

        return nombre

    def clean_telefono(self):
        """Valida el campo teléfono"""
        telefono = self.cleaned_data.get('telefono', '').strip()

        if not telefono:
            raise ValidationError('El teléfono es obligatorio')

        # Eliminar espacios y guiones si los hay
        telefono_limpio = telefono.replace(' ', '').replace('-', '')

        if not telefono_limpio.isdigit():
            raise ValidationError('El teléfono solo puede contener números')

        if not (9 <= len(telefono_limpio) <= 15):
            raise ValidationError('El teléfono debe tener entre 9 y 15 dígitos')

        return telefono_limpio

    def clean_email(self):
        """Valida el campo email"""
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise ValidationError('El email es obligatorio')

        # Django ya valida el formato con EmailField, pero añadimos validación extra
        if len(email) > 254:
            raise ValidationError('El email es demasiado largo')

        return email

    def clean_descripcion(self):
        """Valida el campo descripción"""
        descripcion = self.cleaned_data.get('descripcion', '').strip()

        if not descripcion:
            raise ValidationError('La descripción del proyecto es obligatoria')

        if len(descripcion) < 20:
            raise ValidationError('La descripción debe tener al menos 20 caracteres')

        if len(descripcion) > 1000:
            raise ValidationError('La descripción no puede superar los 1000 caracteres')

        return descripcion

    def clean_images(self):
        """Valida las imágenes adjuntas"""
        files = self.files.getlist('images')

        # Si no hay archivos, no hay nada que validar
        if not files:
            return files

        # Validar número máximo de archivos
        if len(files) > 5:
            raise ValidationError('Solo puedes subir un máximo de 5 imágenes')

        # Validar cada archivo
        MAX_SIZE = 5 * 1024 * 1024  # 5MB en bytes
        ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']

        for file in files:
            # Validar tipo MIME
            if file.content_type not in ALLOWED_TYPES:
                raise ValidationError(
                    f'{file.name}: Solo se permiten archivos JPG, PNG o WEBP'
                )

            # Validar tamaño
            if file.size > MAX_SIZE:
                size_mb = file.size / (1024 * 1024)
                raise ValidationError(
                    f'{file.name}: El tamaño ({size_mb:.1f}MB) supera el máximo permitido (5MB)'
                )

        return files
