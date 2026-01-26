"""
===============================================================================
ARCHIVO: apps/leads/validators.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Define validadores personalizados para archivos y datos del módulo leads.
    Estos validadores añaden una capa de seguridad adicional a las validaciones
    estándar de Django, verificando no solo extensiones sino también contenido.

FUNCIONES PRINCIPALES:
    - validate_image_file: Valida imágenes (JPG, PNG, WEBP)
    - validate_pdf_file: Valida documentos PDF
    - validate_spanish_phone: Valida teléfonos españoles
    - validate_min_images_size: Valida tamaño mínimo de imágenes

FLUJO EN LA APLICACIÓN:
    1. Usuario sube archivo en formulario de contacto
    2. Django llama al validador configurado en el campo del modelo
    3. Si la validación falla, se lanza ValidationError
    4. El error se muestra al usuario en el formulario

SEGURIDAD - MAGIC BYTES:
    Los validadores de archivos verifican los "magic bytes" (primeros bytes)
    del archivo, no solo la extensión. Esto previene ataques donde un
    archivo malicioso se renombra con extensión legítima.

    Firmas conocidas:
    - JPEG: FF D8 FF
    - PNG: 89 50 4E 47 0D 0A 1A 0A
    - WEBP: RIFF....WEBP
    - PDF: %PDF-

PRINCIPIOS DE DISEÑO:
    - Defensa en profundidad: Múltiples capas de validación
    - Fail-safe: Rechazar si hay duda sobre la validez
    - Mensajes claros: Errores descriptivos para el usuario

RELACIÓN CON OTROS ARCHIVOS:
    - models.py: Los campos ImageField y FileField usan estos validadores
    - views.py: La vista contact_us también puede validar antes de guardar

===============================================================================
"""

import os

from django.core.exceptions import ValidationError


# =============================================================================
# VALIDADOR: IMÁGENES
# =============================================================================

def validate_image_file(file) -> None:
    """
    Valida que el archivo sea una imagen válida y segura.

    DESCRIPCIÓN:
        Realiza validación exhaustiva de archivos de imagen verificando
        extensión, tamaño y contenido real (magic bytes).

    PARÁMETROS:
        file: Objeto archivo de Django (InMemoryUploadedFile o similar).
              Debe tener atributos: name, size, read(), seek().

    VALIDACIONES:
        1. Tamaño máximo: 5MB
        2. Extensión permitida: jpg, jpeg, png, webp
        3. Magic bytes: Verifica que el contenido sea imagen real

    EXCEPCIONES:
        ValidationError: Si cualquier validación falla.

    EJEMPLO DE USO EN MODELO:
        >>> image = models.ImageField(
        ...     upload_to='leads/',
        ...     validators=[validate_image_file]
        ... )

    SEGURIDAD:
        Previene ataques de tipo:
        - Subida de archivos ejecutables renombrados como .jpg
        - Archivos maliciosos disfrazados de imágenes
        - Archivos excesivamente grandes (DoS)
    """
    # -------------------------------------------------------------------------
    # VALIDACIÓN 1: Tamaño máximo
    # -------------------------------------------------------------------------
    max_size = 5 * 1024 * 1024  # 5MB en bytes
    if file.size > max_size:
        raise ValidationError(
            f'La imagen no puede superar 5MB. '
            f'Tamaño actual: {file.size / 1024 / 1024:.2f}MB'
        )

    # -------------------------------------------------------------------------
    # VALIDACIÓN 2: Extensión del archivo
    # -------------------------------------------------------------------------
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    ext = os.path.splitext(file.name)[1][1:].lower()  # Extraer extensión sin punto
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Extensión no permitida: .{ext}. '
            f'Permitidas: {", ".join(allowed_extensions)}'
        )

    # -------------------------------------------------------------------------
    # VALIDACIÓN 3: Magic bytes (contenido real del archivo)
    # -------------------------------------------------------------------------
    # Leer los primeros 12 bytes para identificar el tipo de archivo
    file.seek(0)
    header = file.read(12)
    file.seek(0)  # IMPORTANTE: Volver al inicio para que Django pueda leer

    # Firmas de archivos de imagen conocidas
    image_signatures = {
        b'\xff\xd8\xff': 'JPEG',           # JPEG siempre empieza con FF D8 FF
        b'\x89PNG\r\n\x1a\n': 'PNG',       # PNG tiene firma específica de 8 bytes
        b'RIFF': 'WEBP',                   # WEBP usa contenedor RIFF
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


# =============================================================================
# VALIDADOR: PDF
# =============================================================================

def validate_pdf_file(file) -> None:
    """
    Valida que el archivo sea un PDF válido y seguro.

    DESCRIPCIÓN:
        Realiza validación de archivos PDF para presupuestos,
        verificando extensión, tamaño y contenido.

    PARÁMETROS:
        file: Objeto archivo de Django con atributos name, size, read(), seek().

    VALIDACIONES:
        1. Tamaño máximo: 10MB
        2. Extensión: solo .pdf
        3. Magic bytes: Debe empezar con %PDF-

    EXCEPCIONES:
        ValidationError: Si cualquier validación falla.

    EJEMPLO DE USO EN MODELO:
        >>> file = models.FileField(
        ...     upload_to='budgets/',
        ...     validators=[validate_pdf_file]
        ... )

    NOTA:
        Los PDFs pueden contener JavaScript malicioso.
        Esta validación solo verifica que sea un PDF real,
        no analiza el contenido interno. Para mayor seguridad
        en producción, considerar validación adicional con
        bibliotecas especializadas.
    """
    # -------------------------------------------------------------------------
    # VALIDACIÓN 1: Tamaño máximo
    # -------------------------------------------------------------------------
    max_size = 10 * 1024 * 1024  # 10MB en bytes
    if file.size > max_size:
        raise ValidationError(
            f'El PDF no puede superar 10MB. '
            f'Tamaño actual: {file.size / 1024 / 1024:.2f}MB'
        )

    # -------------------------------------------------------------------------
    # VALIDACIÓN 2: Extensión del archivo
    # -------------------------------------------------------------------------
    ext = os.path.splitext(file.name)[1][1:].lower()
    if ext != 'pdf':
        raise ValidationError(
            f'Solo se permiten archivos PDF. '
            f'Extensión detectada: .{ext}'
        )

    # -------------------------------------------------------------------------
    # VALIDACIÓN 3: Magic bytes (firma PDF)
    # -------------------------------------------------------------------------
    # Los PDF siempre empiezan con %PDF- seguido de la versión
    file.seek(0)
    header = file.read(5)
    file.seek(0)  # Volver al inicio

    if not header.startswith(b'%PDF-'):
        raise ValidationError(
            'El archivo no es un PDF válido. '
            'Asegúrate de subir un archivo PDF real.'
        )


# =============================================================================
# VALIDADOR: TELÉFONO ESPAÑOL
# =============================================================================

def validate_spanish_phone(value: str) -> None:
    """
    Valida que el número de teléfono sea válido para España.

    DESCRIPCIÓN:
        Verifica que el teléfono cumpla con el formato español,
        aceptando múltiples formatos de entrada y normalizando.

    PARÁMETROS:
        value (str): Número de teléfono a validar.

    FORMATOS ACEPTADOS:
        - Móviles: 6XX XXX XXX, 7XX XXX XXX
        - Fijos: 9XX XXX XXX
        - Con espacios: 612 345 678
        - Con guiones: 612-345-678
        - Con prefijo: +34 612345678, 0034612345678

    VALIDACIONES:
        1. Solo dígitos (después de limpiar)
        2. Exactamente 9 dígitos (sin prefijo)
        3. Empieza por 6, 7 o 9

    EXCEPCIONES:
        ValidationError: Si el formato no es válido.

    EJEMPLO DE USO:
        >>> validate_spanish_phone('612 345 678')  # OK
        >>> validate_spanish_phone('+34612345678')  # OK
        >>> validate_spanish_phone('123456789')  # Error: no empieza por 6,7,9
    """
    import re

    # -------------------------------------------------------------------------
    # PASO 1: Limpiar formato
    # -------------------------------------------------------------------------
    # Eliminar espacios, guiones, paréntesis
    cleaned = re.sub(r'[\s\-\(\)]', '', value)

    # -------------------------------------------------------------------------
    # PASO 2: Quitar prefijo internacional
    # -------------------------------------------------------------------------
    if cleaned.startswith('+34'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('0034'):
        cleaned = cleaned[4:]

    # -------------------------------------------------------------------------
    # PASO 3: Validar que solo contenga dígitos
    # -------------------------------------------------------------------------
    if not cleaned.isdigit():
        raise ValidationError('El teléfono solo debe contener números')

    # -------------------------------------------------------------------------
    # PASO 4: Validar longitud (9 dígitos para España)
    # -------------------------------------------------------------------------
    if len(cleaned) != 9:
        raise ValidationError(
            f'El teléfono debe tener 9 dígitos. Tiene: {len(cleaned)}'
        )

    # -------------------------------------------------------------------------
    # PASO 5: Validar primer dígito
    # -------------------------------------------------------------------------
    # 6XX: Móviles
    # 7XX: Móviles (asignación reciente)
    # 9XX: Fijos
    if cleaned[0] not in ['6', '7', '9']:
        raise ValidationError('El teléfono debe empezar por 6, 7 o 9')


# =============================================================================
# VALIDADOR: TAMAÑO MÍNIMO DE IMAGEN
# =============================================================================

def validate_min_images_size(file) -> None:
    """
    Valida que la imagen tenga un tamaño mínimo razonable.

    DESCRIPCIÓN:
        Previene la subida de imágenes extremadamente pequeñas
        que podrían ser placeholders, imágenes corruptas o
        intentos de spam.

    PARÁMETROS:
        file: Objeto archivo de Django con atributo size.

    VALIDACIONES:
        - Tamaño mínimo: 10KB

    EXCEPCIONES:
        ValidationError: Si la imagen es demasiado pequeña.

    PROPÓSITO:
        - Evitar imágenes de 1x1 pixel (tracking pixels)
        - Detectar archivos corruptos o vacíos
        - Asegurar que las imágenes tengan contenido útil

    NOTA:
        Este validador es complementario a validate_image_file.
        Se puede añadir como segundo validador si se requiere.
    """
    min_size = 10 * 1024  # 10KB en bytes

    if file.size < min_size:
        raise ValidationError(
            f'La imagen es demasiado pequeña ({file.size} bytes). '
            f'Debe tener al menos {min_size / 1024:.0f}KB'
        )
