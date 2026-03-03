from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SetPasswordAfterActivationForm(forms.Form):
    """
    Formulario para cambio opcional de contraseña tras activación de cuenta.

    Valida que ambas contraseñas coincidan y cumplan los validadores
    configurados en AUTH_PASSWORD_VALIDATORS.
    """

    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Mínimo 8 caracteres. No puede ser solo números ni demasiado común.',
    )
    new_password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')

        if password1 and self.user:
            try:
                validate_password(password1, user=self.user)
            except ValidationError as e:
                self.add_error('new_password1', e)

        return cleaned_data
