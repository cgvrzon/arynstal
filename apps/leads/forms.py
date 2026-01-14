"""
Formularios para la app de leads.
"""

from django import forms
from .models import Lead


class LeadForm(forms.ModelForm):
    """
    Formulario para crear un Lead desde el formulario de contacto público.

    Campos del formulario web:
    - nombre (name)
    - telefono (phone)
    - email
    - descripcion (description)
    - fotos[] (manejado aparte, no en este form)
    - privacidad (checkbox, validado en vista)
    """

    class Meta:
        model = Lead
        fields = ['name', 'phone', 'email', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personalizar widgets para mantener diseño del frontend
        self.fields['name'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300 text-sm sm:text-base',
            'placeholder': 'Ej: Juan Pérez García',
            'id': 'nombre'
        })

        self.fields['phone'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300 text-sm sm:text-base',
            'placeholder': 'Ej: 612345678',
            'id': 'telefono',
            'type': 'tel'
        })

        self.fields['email'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300 text-sm sm:text-base',
            'placeholder': 'Ej: juan@email.com',
            'id': 'email',
            'type': 'email'
        })

        self.fields['message'].widget = forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0D3B66] focus:border-transparent transition-all duration-300 resize-y text-sm sm:text-base',
            'placeholder': 'Describe tu proyecto: tipo de instalación, estado actual, necesidades específicas...',
            'rows': 6,
            'id': 'descripcion'
        })

    def clean_name(self):
        """Validar que el nombre tenga al menos 3 caracteres."""
        name = self.cleaned_data.get('name')
        if name and len(name) < 3:
            raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
        return name

    def clean_message(self):
        """Validar que el mensaje tenga al menos 20 caracteres."""
        message = self.cleaned_data.get('message')
        if message and len(message) < 20:
            raise forms.ValidationError('La descripción debe tener al menos 20 caracteres.')
        if message and len(message) > 1000:
            raise forms.ValidationError('La descripción no puede superar los 1000 caracteres.')
        return message
