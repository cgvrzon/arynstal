"""
Validadores personalizados para el módulo de leads.
Incluye validación de archivos, teléfonos, etc.
"""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import os


def validate_image_file(file):
    """
    Valida que el archivo sea una imagen válida.

    Verifica:
    - Tamaño máximo: 5MB
    - Extensión permitida: jpg, jpeg, png, webp
    - Magic bytes (primeros bytes del archivo)
    """
    # Validar tamaño (5MB máximo)
    max_size = 5 * 1024 * 1024  # 5MB en bytes
    if file.size > max_size:
        raise ValidationError(f'La imagen no puede superar 5MB. Tamaño actual: {file.size / 1024 / 1024:.2f}MB')

    # Validar extensión
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    ext = os.path.splitext(file.name)[1][1:].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'Extensión no permitida: .{ext}. Permitidas: {", ".join(allowed_extensions)}')

    # Validar magic bytes (primeros bytes del archivo)
    file.seek(0)
    header = file.read(12)
    file.seek(0)  # Volver al inicio

    # Firmas de archivos de imagen comunes
    image_signatures = {
        b'\xff\xd8\xff': 'JPEG',
        b'\x89PNG\r\n\x1a\n': 'PNG',
        b'RIFF': 'WEBP',  # WEBP empieza con RIFF
    }

    is_valid = False
    for signature, file_type in image_signatures.items():
        if header.startswith(signature):
            is_valid = True
            break

    if not is_valid:
        raise ValidationError(
            'El archivo no es una imagen válida. '
            'Asegúrate de subir archivos JPG, PNG o WEBP reales.'
        )


def validate_pdf_file(file):
    """
    Valida que el archivo sea un PDF válido.

    Verifica:
    - Tamaño máximo: 10MB
    - Extensión: .pdf
    - Magic bytes de PDF
    """
    # Validar tamaño (10MB máximo)
    max_size = 10 * 1024 * 1024  # 10MB en bytes
    if file.size > max_size:
        raise ValidationError(f'El PDF no puede superar 10MB. Tamaño actual: {file.size / 1024 / 1024:.2f}MB')

    # Validar extensión
    ext = os.path.splitext(file.name)[1][1:].lower()
    if ext != 'pdf':
        raise ValidationError(f'Solo se permiten archivos PDF. Extensión detectada: .{ext}')

    # Validar magic bytes (PDF siempre empieza con %PDF)
    file.seek(0)
    header = file.read(5)
    file.seek(0)  # Volver al inicio

    if not header.startswith(b'%PDF-'):
        raise ValidationError(
            'El archivo no es un PDF válido. '
            'Asegúrate de subir un archivo PDF real.'
        )


def validate_spanish_phone(value):
    """
    Valida que el teléfono sea válido para España.

    Acepta:
    - Móviles: 6XX XXX XXX o 7XX XXX XXX
    - Fijos: 9XX XXX XXX
    - Con espacios, guiones o sin separadores
    - Con o sin prefijo +34
    """
    import re

    # Limpiar el número (quitar espacios, guiones, paréntesis)
    cleaned = re.sub(r'[\s\-\(\)]', '', value)

    # Quitar prefijo internacional si existe
    if cleaned.startswith('+34'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('0034'):
        cleaned = cleaned[4:]

    # Validar que solo contenga dígitos
    if not cleaned.isdigit():
        raise ValidationError('El teléfono solo debe contener números')

    # Validar longitud (9 dígitos para España)
    if len(cleaned) != 9:
        raise ValidationError(f'El teléfono debe tener 9 dígitos. Tiene: {len(cleaned)}')

    # Validar que empiece con 6, 7 o 9
    if cleaned[0] not in ['6', '7', '9']:
        raise ValidationError('El teléfono debe empezar por 6, 7 o 9')


def validate_min_images_size(file):
    """
    Valida que la imagen tenga un tamaño mínimo razonable.
    Evita imágenes de 1x1 pixel o muy pequeñas.
    """
    # Tamaño mínimo: 10KB (evita imágenes diminutas o corruptas)
    min_size = 10 * 1024  # 10KB
    if file.size < min_size:
        raise ValidationError(
            f'La imagen es demasiado pequeña ({file.size} bytes). '
            f'Debe tener al menos {min_size / 1024:.0f}KB'
        )
