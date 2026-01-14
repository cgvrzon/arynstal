"""
Selector de configuración según el entorno.

Por defecto usa 'development'. Para producción, establecer:
    export DJANGO_ENV=production

O en el .env:
    DJANGO_ENV=production
"""

import os

# Detectar el entorno (por defecto: development)
environment = os.environ.get('DJANGO_ENV', 'development')

# Cargar la configuración correspondiente
if environment == 'production':
    from .production import *
    print('🚀 Django running in PRODUCTION mode')
else:
    from .development import *
    print('🔧 Django running in DEVELOPMENT mode')
