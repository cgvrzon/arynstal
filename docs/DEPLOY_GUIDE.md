# ARYNSTAL - Guía de Despliegue

> Guía paso a paso para desplegar la aplicación en producción.
>
> **Prerequisitos**: Leer primero `INFRAESTRUCTURA.md`

---

## Índice

1. [Preparación Local](#1-preparación-local)
2. [Contratar Servicios](#2-contratar-servicios)
3. [Configurar DNS](#3-configurar-dns)
4. [Configurar Servidor](#4-configurar-servidor)
5. [Instalar Dependencias](#5-instalar-dependencias)
6. [Configurar PostgreSQL](#6-configurar-postgresql)
7. [Desplegar Aplicación](#7-desplegar-aplicación)
8. [Configurar Gunicorn](#8-configurar-gunicorn)
9. [Configurar Nginx](#9-configurar-nginx)
10. [Configurar SSL](#10-configurar-ssl)
11. [Configurar Email](#11-configurar-email)
12. [Configurar Backups](#12-configurar-backups)
13. [Go-Live](#13-go-live)
14. [Post-Despliegue](#14-post-despliegue)

---

## 1. Preparación Local

### 1.1 Generar SECRET_KEY de producción

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Guardar el resultado** - lo necesitarás para el archivo `.env` del servidor.

### 1.2 Verificar que el proyecto está listo

```bash
# En tu máquina local
cd ~/DjangoProyectos/arynstal
source venv/bin/activate

# Verificar
python manage.py check --deploy
python manage.py test

# Asegurar que requirements está actualizado
pip freeze > requirements/production-freeze.txt
```

### 1.3 Subir código a repositorio Git

Si aún no tienes el código en un repositorio:

```bash
# Opción GitHub
gh repo create arynstal --private

# O manualmente
git remote add origin git@github.com:tu-usuario/arynstal.git
git push -u origin main
```

---

## 2. Contratar Servicios

### 2.1 Dominio

1. Ir a [Dondominio](https://www.dondominio.com) o [Porkbun](https://porkbun.com)
2. Buscar `arynstal.es`
3. Registrar (~9€/año)
4. **No configurar DNS todavía** - lo haremos con Cloudflare

### 2.2 Cloudflare

1. Crear cuenta en [Cloudflare](https://cloudflare.com)
2. Añadir sitio `arynstal.es`
3. Cloudflare te dará dos nameservers, ejemplo:
   - `ada.ns.cloudflare.com`
   - `bob.ns.cloudflare.com`
4. Volver al registrador de dominio y cambiar los nameservers a los de Cloudflare
5. Esperar propagación (puede tardar hasta 24h, normalmente 1-2h)

### 2.3 VPS Hetzner

1. Crear cuenta en [Hetzner Cloud](https://console.hetzner.cloud)
2. Crear nuevo proyecto "Arynstal"
3. Crear servidor:
   - **Ubicación**: Falkenstein (FSN1) o Nuremberg (NBG1)
   - **Imagen**: Ubuntu 24.04
   - **Tipo**: CX22 (2 vCPU, 4 GB RAM)
   - **SSH Key**: Añadir tu clave pública
   - **Nombre**: `arynstal-prod`
4. Anotar la IP pública del servidor

### 2.4 Brevo (Email)

1. Crear cuenta en [Brevo](https://www.brevo.com)
2. Ir a SMTP & API
3. Crear una API key para SMTP
4. Anotar las credenciales:
   - Host: `smtp-relay.brevo.com`
   - Puerto: `587`
   - Usuario: tu email
   - Password: la API key generada

---

## 3. Configurar DNS

En el panel de Cloudflare:

### 3.1 Registros DNS

| Tipo | Nombre | Contenido | Proxy |
|------|--------|-----------|-------|
| A | @ | IP_DEL_VPS | ✅ Proxied |
| A | www | IP_DEL_VPS | ✅ Proxied |

### 3.2 Configuración SSL/TLS

1. Ir a SSL/TLS → Overview
2. Seleccionar **Full (strict)**

### 3.3 Configuración de seguridad

1. Ir a Security → Settings
2. Security Level: **Medium**
3. Challenge Passage: **30 minutes**

---

## 4. Configurar Servidor

### 4.1 Conectar por SSH

```bash
ssh root@IP_DEL_VPS
```

### 4.2 Actualizar sistema

```bash
apt update && apt upgrade -y
```

### 4.3 Crear usuario para la aplicación

```bash
# Crear usuario
adduser --disabled-password --gecos "" arynstal

# Añadir a grupo sudo (por si acaso)
usermod -aG sudo arynstal

# Configurar SSH para el nuevo usuario
mkdir -p /home/arynstal/.ssh
cp ~/.ssh/authorized_keys /home/arynstal/.ssh/
chown -R arynstal:arynstal /home/arynstal/.ssh
chmod 700 /home/arynstal/.ssh
chmod 600 /home/arynstal/.ssh/authorized_keys
```

### 4.4 Configurar Firewall

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status
```

### 4.5 (Opcional) Configurar Fail2ban

```bash
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 5. Instalar Dependencias

```bash
# Python y herramientas de desarrollo
apt install python3 python3-pip python3-venv python3-dev -y

# PostgreSQL
apt install postgresql postgresql-contrib libpq-dev -y

# Nginx
apt install nginx -y

# Certbot para SSL
apt install certbot python3-certbot-nginx -y

# Git
apt install git -y

# Herramientas útiles
apt install htop ncdu -y
```

---

## 6. Configurar PostgreSQL

### 6.1 Crear base de datos y usuario

```bash
sudo -u postgres psql
```

```sql
-- Crear usuario
CREATE USER arynstal_user WITH PASSWORD 'CONTRASEÑA_SEGURA_AQUI';

-- Crear base de datos
CREATE DATABASE arynstal OWNER arynstal_user;

-- Dar permisos
GRANT ALL PRIVILEGES ON DATABASE arynstal TO arynstal_user;

-- Salir
\q
```

### 6.2 Verificar conexión

```bash
psql -U arynstal_user -d arynstal -h localhost
# Introducir contraseña cuando pregunte
# Si conecta, escribir \q para salir
```

---

## 7. Desplegar Aplicación

### 7.1 Crear estructura de directorios

```bash
mkdir -p /var/www/arynstal
mkdir -p /var/www/arynstal/logs
mkdir -p /var/www/arynstal/backups
chown -R arynstal:arynstal /var/www/arynstal
```

### 7.2 Clonar repositorio

```bash
# Cambiar al usuario arynstal
su - arynstal

# Clonar
cd /var/www/arynstal
git clone https://github.com/TU_USUARIO/arynstal.git app

# O si es privado y usas SSH
git clone git@github.com:TU_USUARIO/arynstal.git app
```

### 7.3 Crear entorno virtual

```bash
cd /var/www/arynstal/app
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/production.txt
```

### 7.4 Configurar variables de entorno

```bash
nano /var/www/arynstal/app/.env
```

Contenido del archivo `.env`:

```bash
# Django
DJANGO_ENV=production
SECRET_KEY=tu-secret-key-generada-antes
DEBUG=False
ALLOWED_HOSTS=arynstal.es,www.arynstal.es

# Base de datos
DB_NAME=arynstal
DB_USER=arynstal_user
DB_PASSWORD=CONTRASEÑA_DE_POSTGRESQL
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@dominio.com
EMAIL_HOST_PASSWORD=tu-api-key-de-brevo
DEFAULT_FROM_EMAIL=Arynstal <info@arynstal.es>

# Notificaciones
LEAD_NOTIFICATION_EMAIL=garzoncl01@gmail.com
```

### 7.5 Aplicar migraciones y collectstatic

```bash
source venv/bin/activate
cd /var/www/arynstal/app

# Migraciones
python manage.py migrate

# Archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario
python manage.py createsuperuser
```

### 7.6 Verificar que funciona

```bash
python manage.py check --deploy
```

---

## 8. Configurar Gunicorn

### 8.1 Crear archivo de configuración

```bash
nano /var/www/arynstal/app/gunicorn.conf.py
```

Contenido:

```python
# Gunicorn configuration file

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
```

### 8.2 Crear servicio systemd

```bash
sudo nano /etc/systemd/system/arynstal.service
```

Contenido:

```ini
[Unit]
Description=Arynstal Django Application
After=network.target postgresql.service

[Service]
User=arynstal
Group=arynstal
WorkingDirectory=/var/www/arynstal/app
Environment="PATH=/var/www/arynstal/app/venv/bin"
EnvironmentFile=/var/www/arynstal/app/.env
ExecStart=/var/www/arynstal/app/venv/bin/gunicorn \
    --config /var/www/arynstal/app/gunicorn.conf.py \
    arynstal.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 8.3 Iniciar servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable arynstal
sudo systemctl start arynstal
sudo systemctl status arynstal
```

---

## 9. Configurar Nginx

### 9.1 Crear configuración del sitio

```bash
sudo nano /etc/nginx/sites-available/arynstal
```

Contenido:

```nginx
upstream arynstal_app {
    server unix:/var/www/arynstal/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name arynstal.es www.arynstal.es;

    # Logs
    access_log /var/www/arynstal/logs/nginx-access.log;
    error_log /var/www/arynstal/logs/nginx-error.log;

    # Archivos estáticos
    location /static/ {
        alias /var/www/arynstal/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Archivos media
    location /media/ {
        alias /var/www/arynstal/app/media/;
        expires 7d;
    }

    # Favicon
    location /favicon.ico {
        alias /var/www/arynstal/app/staticfiles/img/favicon.ico;
        expires 30d;
    }

    # Robots y Sitemap
    location /robots.txt {
        alias /var/www/arynstal/app/staticfiles/robots.txt;
    }

    location /sitemap.xml {
        alias /var/www/arynstal/app/staticfiles/sitemap.xml;
    }

    # Aplicación Django
    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_pass http://arynstal_app;
    }

    # Límite de tamaño de subida (para imágenes)
    client_max_body_size 20M;
}
```

### 9.2 Activar sitio

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/arynstal /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 10. Configurar SSL

### 10.1 Obtener certificado (si no usas Cloudflare SSL)

> **Nota**: Si usas Cloudflare con SSL Full (strict), el certificado se gestiona automáticamente. Este paso es opcional.

```bash
sudo certbot --nginx -d arynstal.es -d www.arynstal.es
```

### 10.2 Verificar renovación automática

```bash
sudo certbot renew --dry-run
```

---

## 11. Configurar Email

### 11.1 Probar envío de emails

```bash
cd /var/www/arynstal/app
source venv/bin/activate

python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test desde Arynstal',
    'Este es un email de prueba del servidor de producción.',
    'info@arynstal.es',
    ['garzoncl01@gmail.com'],
    fail_silently=False,
)
```

Si recibes el email, la configuración es correcta.

---

## 12. Configurar Backups

### 12.1 Crear script de backup

```bash
sudo nano /var/www/arynstal/backup.sh
```

Contenido:

```bash
#!/bin/bash

# Configuración
BACKUP_DIR="/var/www/arynstal/backups"
DB_NAME="arynstal"
DB_USER="arynstal_user"
RETENTION_DAYS=7

# Crear backup con fecha
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/arynstal_$DATE.sql.gz"

# Backup de PostgreSQL
PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_FILE

# Verificar que se creó
if [ -f "$BACKUP_FILE" ]; then
    echo "Backup creado: $BACKUP_FILE"

    # Eliminar backups antiguos
    find $BACKUP_DIR -name "arynstal_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Backups antiguos eliminados"
else
    echo "ERROR: Backup falló"
    exit 1
fi
```

### 12.2 Dar permisos y programar

```bash
chmod +x /var/www/arynstal/backup.sh

# Añadir a crontab
sudo crontab -e
```

Añadir línea (backup diario a las 3:00 AM):

```
0 3 * * * /var/www/arynstal/backup.sh >> /var/www/arynstal/logs/backup.log 2>&1
```

### 12.3 Probar backup

```bash
/var/www/arynstal/backup.sh
ls -la /var/www/arynstal/backups/
```

---

## 13. Go-Live

### 13.1 Checklist final

- [ ] DNS apuntando al servidor
- [ ] SSL funcionando (https://arynstal.es)
- [ ] Página de inicio carga correctamente
- [ ] Formulario de contacto funciona
- [ ] Se recibe email de notificación
- [ ] Panel admin accesible en /admynstal/
- [ ] Archivos estáticos cargan (CSS, JS, imágenes)
- [ ] No hay errores en logs

### 13.2 Verificar logs

```bash
# Logs de aplicación
tail -f /var/www/arynstal/logs/gunicorn-error.log

# Logs de Nginx
tail -f /var/www/arynstal/logs/nginx-error.log

# Logs del sistema
sudo journalctl -u arynstal -f
```

### 13.3 Test de carga básico

```bash
# Desde tu máquina local
curl -I https://arynstal.es
# Debería devolver HTTP/2 200
```

---

## 14. Post-Despliegue

### 14.1 Comandos útiles

```bash
# Reiniciar aplicación
sudo systemctl restart arynstal

# Ver estado
sudo systemctl status arynstal

# Ver logs en tiempo real
sudo journalctl -u arynstal -f

# Reiniciar Nginx
sudo systemctl restart nginx

# Actualizar código
cd /var/www/arynstal/app
git pull
source venv/bin/activate
pip install -r requirements/production.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart arynstal
```

### 14.2 Script de actualización

Crear `/var/www/arynstal/deploy.sh`:

```bash
#!/bin/bash
set -e

cd /var/www/arynstal/app

echo "==> Actualizando código..."
git pull

echo "==> Activando entorno virtual..."
source venv/bin/activate

echo "==> Instalando dependencias..."
pip install -r requirements/production.txt

echo "==> Aplicando migraciones..."
python manage.py migrate

echo "==> Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Reiniciando servicio..."
sudo systemctl restart arynstal

echo "==> Despliegue completado!"
```

```bash
chmod +x /var/www/arynstal/deploy.sh
```

### 14.3 Monitorización básica

Instalar y configurar Uptime Kuma (opcional):

```bash
# En el servidor o en otra máquina
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1
```

Configurar para monitorizar:
- `https://arynstal.es` (HTTP 200)
- `https://arynstal.es/admynstal/` (HTTP 200/302)

---

## Troubleshooting

### Problema: 502 Bad Gateway

```bash
# Verificar que Gunicorn está corriendo
sudo systemctl status arynstal

# Verificar socket
ls -la /var/www/arynstal/gunicorn.sock

# Reiniciar servicios
sudo systemctl restart arynstal
sudo systemctl restart nginx
```

### Problema: Static files no cargan

```bash
# Verificar que existen
ls /var/www/arynstal/app/staticfiles/

# Re-ejecutar collectstatic
cd /var/www/arynstal/app
source venv/bin/activate
python manage.py collectstatic --noinput

# Verificar permisos
sudo chown -R arynstal:arynstal /var/www/arynstal/app/staticfiles/
```

### Problema: Error de base de datos

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Verificar conexión
psql -U arynstal_user -d arynstal -h localhost

# Verificar variables de entorno
cat /var/www/arynstal/app/.env | grep DB_
```

### Problema: Emails no se envían

```bash
# Probar desde shell de Django
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@test.com', ['to@test.com'])

# Verificar credenciales en .env
cat /var/www/arynstal/app/.env | grep EMAIL
```

---

## Resumen de Archivos de Configuración

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `.env` | `/var/www/arynstal/app/.env` | Variables de entorno |
| `gunicorn.conf.py` | `/var/www/arynstal/app/gunicorn.conf.py` | Config Gunicorn |
| `arynstal.service` | `/etc/systemd/system/arynstal.service` | Servicio systemd |
| `arynstal` | `/etc/nginx/sites-available/arynstal` | Config Nginx |
| `backup.sh` | `/var/www/arynstal/backup.sh` | Script de backup |
| `deploy.sh` | `/var/www/arynstal/deploy.sh` | Script de deploy |

---

## Historial de Revisiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-01-15 | Documento inicial |
| 1.1 | 2026-01-26 | Añadida sección de historial |

---

*Documento complementario a `INFRAESTRUCTURA.md`*
