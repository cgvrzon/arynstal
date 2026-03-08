"""
Settings package de Arynstal.

NO apuntar DJANGO_SETTINGS_MODULE a 'arynstal.settings' directamente.
Usar el modulo especifico del entorno:

    - arynstal.settings.development  (dev local, CI)
    - arynstal.settings.production   (servidor)

manage.py usa development por defecto.
wsgi.py/asgi.py usan production por defecto.
El servidor define DJANGO_SETTINGS_MODULE en .env para sobreescribir defaults.
"""
