"""
Selector de configuración según el entorno.

Por defecto usa 'development'. Para otros entornos, establecer:
    export DJANGO_ENV=production    # Servidor de producción
    export DJANGO_ENV=docker        # Desarrollo local con Docker

O en el archivo .env correspondiente:
    DJANGO_ENV=production
    DJANGO_ENV=docker
"""

import os

# Detectar el entorno (por defecto: development)
environment = os.environ.get('DJANGO_ENV', 'development')

# Cargar la configuración correspondiente
if environment == 'production':
    from .production import *  # noqa: F403
    print('🚀 Django running in PRODUCTION mode')
elif environment == 'docker':
    from .docker import *  # noqa: F403
    print('🐳 Django running in DOCKER mode')
else:
    from .development import *  # noqa: F403
    print('🔧 Django running in DEVELOPMENT mode')
