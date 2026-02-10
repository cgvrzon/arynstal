# gunicorn.conf.py
# Configuración de Gunicorn para producción.
# Referencia: https://docs.gunicorn.org/en/stable/settings.html

# Servidor
bind = "unix:/var/www/arynstal/gunicorn.sock"
workers = 3
worker_class = "sync"
timeout = 120

# Logging
accesslog = "/var/www/arynstal/logs/gunicorn-access.log"
errorlog = "/var/www/arynstal/logs/gunicorn-error.log"
loglevel = "info"

# Proceso
daemon = False
pidfile = "/var/www/arynstal/gunicorn.pid"

# Seguridad
limit_request_line = 4094
limit_request_fields = 100
