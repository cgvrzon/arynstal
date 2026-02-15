# ARYNSTAL - Guía de Despliegue

> Guía paso a paso para desplegar la aplicación en producción.
>
> **Prerequisitos**: Leer primero `INFRAESTRUCTURA.md` para entender las decisiones de arquitectura, costes y servicios seleccionados.

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

1. Ir a [DonDominio](https://www.dondominio.com)
2. Buscar `arynstal.es`
3. Registrar (~12€/año)
4. **Importante en DonDominio**: Al registrar, seleccionar "Continuar sin añadir servicios" para evitar extras innecesarios (hosting, email, etc.)
5. **No configurar DNS en DonDominio** - lo haremos con Cloudflare

### 2.2 Cloudflare

1. Crear cuenta en [Cloudflare](https://cloudflare.com)
2. Añadir sitio `arynstal.es`
3. Cloudflare te dará dos nameservers, ejemplo:
   - `ada.ns.cloudflare.com`
   - `bob.ns.cloudflare.com`
4. Volver a DonDominio y cambiar los nameservers a los de Cloudflare
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

### 2.4 Brevo (Email Transaccional)

> Brevo gestiona los emails **automáticos** que envía Django (notificaciones de leads, confirmaciones). No es para correo corporativo.

1. Crear cuenta en [Brevo](https://www.brevo.com)
2. Ir a SMTP & API
3. Crear una API key para SMTP
4. Anotar las credenciales:
   - Host: `smtp-relay.brevo.com`
   - Puerto: `587`
   - Usuario: tu email de registro en Brevo
   - Password: la API key generada

### 2.5 Zoho Mail Free (Email Corporativo)

> Zoho gestiona el correo **corporativo** con dominio propio (info@arynstal.es, carlos@arynstal.es). Es para comunicación humana.

1. Ir a [Zoho Mail](https://www.zoho.com/mail/)
2. Seleccionar **Mail Free** (Forever Free plan, hasta 5 usuarios)
3. Registrarse con un email personal (será el admin)
4. Añadir dominio `arynstal.es`
5. Zoho pedirá verificar el dominio con un registro TXT en DNS
   - **Nota**: Este registro se configura en la sección 3 (DNS)
6. **No crear buzones todavía** - primero hay que configurar DNS (sección 3) y verificar el dominio (sección 11.1)

---

## 3. Configurar DNS

En el panel de Cloudflare, configurar los siguientes registros para `arynstal.es`:

### 3.1 Registros A (Web)

| Tipo | Nombre | Contenido | Proxy | TTL |
|------|--------|-----------|-------|-----|
| A | @ | IP_DEL_VPS | Proxied | Auto |
| A | www | IP_DEL_VPS | Proxied | Auto |

### 3.2 Registros MX (Zoho Mail)

> Los registros MX indican qué servidores reciben el correo de tu dominio. **NO deben estar proxied** (solo DNS).

| Tipo | Nombre | Contenido | Prioridad | Proxy | TTL |
|------|--------|-----------|-----------|-------|-----|
| MX | @ | mx.zoho.eu | 10 | DNS only | Auto |
| MX | @ | mx2.zoho.eu | 20 | DNS only | Auto |
| MX | @ | mx3.zoho.eu | 50 | DNS only | Auto |

### 3.3 SPF (Zoho + Brevo combinado)

> SPF indica qué servidores están autorizados a enviar email en nombre de tu dominio. **Un solo registro SPF** que incluye ambos servicios.

| Tipo | Nombre | Contenido | Proxy | TTL |
|------|--------|-----------|-------|-----|
| TXT | @ | `v=spf1 include:zoho.eu include:spf.brevo.com ~all` | DNS only | Auto |

**Nota**: Solo puede haber **un registro SPF** por dominio. Si necesitas añadir más servicios, agrégalos con `include:` adicionales en este mismo registro.

### 3.4 DKIM - Zoho

> DKIM firma los emails para que el destinatario pueda verificar que no han sido alterados. Zoho proporciona su propia clave DKIM.

1. En Zoho Mail Admin → Domain → Email Authentication → DKIM
2. Generar clave DKIM (selector: `zmail`)
3. Añadir el registro en Cloudflare:

| Tipo | Nombre | Contenido | Proxy | TTL |
|------|--------|-----------|-------|-----|
| TXT | `zmail._domainkey` | (valor proporcionado por Zoho) | DNS only | Auto |

### 3.5 DKIM - Brevo

> Brevo usa un selector DKIM diferente, así que no hay conflicto con Zoho.

1. En Brevo → Settings → Senders & Domains → Domains → Add domain `arynstal.es`
2. Brevo te dará un registro DKIM (selector: `mail`)
3. Añadir el registro en Cloudflare:

| Tipo | Nombre | Contenido | Proxy | TTL |
|------|--------|-----------|-------|-----|
| TXT | `mail._domainkey` | (valor proporcionado por Brevo) | DNS only | Auto |

### 3.6 DMARC

> DMARC indica a los servidores receptores qué hacer con emails que fallen SPF/DKIM. Empezar en modo monitorización (`p=none`).

| Tipo | Nombre | Contenido | Proxy | TTL |
|------|--------|-----------|-------|-----|
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:carlos@arynstal.es; fo=1` | DNS only | Auto |

**Fases DMARC**:
1. **Semana 1-4**: `p=none` (solo monitorizar, revisar reportes en carlos@)
2. **Mes 2+**: `p=quarantine` (emails sospechosos van a spam)
3. **Cuando todo esté estable**: `p=reject` (bloquear emails no autenticados)

### 3.7 Verificar DNS

Después de configurar todos los registros, esperar 5-15 minutos y verificar:

```bash
# Verificar registros A
dig arynstal.es A +short
dig www.arynstal.es A +short

# Verificar MX (Zoho)
dig arynstal.es MX +short
# Debe mostrar: mx.zoho.eu, mx2.zoho.eu, mx3.zoho.eu

# Verificar SPF
dig arynstal.es TXT +short
# Debe incluir: v=spf1 include:zoho.eu include:spf.brevo.com ~all

# Verificar DKIM
dig zmail._domainkey.arynstal.es TXT +short  # Zoho
dig mail._domainkey.arynstal.es TXT +short   # Brevo

# Verificar DMARC
dig _dmarc.arynstal.es TXT +short
```

**Herramientas online** para verificación más detallada:
- [MXToolbox](https://mxtoolbox.com/SuperTool.aspx) - verificar MX, SPF, DKIM, DMARC
- [DMARCian](https://dmarcian.com/dmarc-inspector/) - inspector DMARC
- [Mail Tester](https://www.mail-tester.com/) - test completo de entrega de email

### 3.8 Configuración SSL/TLS

1. Ir a SSL/TLS → Overview
2. Seleccionar **Full (strict)**

### 3.9 Configuración de seguridad

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
adduser --disabled-password --gecos "" YOUR_USER

# Añadir a grupo sudo (por si acaso)
usermod -aG sudo YOUR_USER

# Configurar SSH para el nuevo usuario
mkdir -p /home/YOUR_USER/.ssh
cp ~/.ssh/authorized_keys /home/YOUR_USER/.ssh/
chown -R YOUR_USER:YOUR_USER /home/YOUR_USER/.ssh
chmod 700 /home/YOUR_USER/.ssh
chmod 600 /home/YOUR_USER/.ssh/authorized_keys
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
CREATE USER YOUR_DB_USER WITH PASSWORD 'CONTRASEÑA_SEGURA_AQUI';

-- Crear base de datos
CREATE DATABASE arynstal OWNER YOUR_DB_USER;

-- Dar permisos
GRANT ALL PRIVILEGES ON DATABASE arynstal TO YOUR_DB_USER;

-- Salir
\q
```

### 6.2 Verificar conexión

```bash
psql -U YOUR_DB_USER -d arynstal -h localhost
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
chown -R YOUR_USER:YOUR_USER /var/www/arynstal
```

### 7.2 Clonar repositorio

```bash
# Cambiar al usuario de la aplicación
su - YOUR_USER

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
CSRF_TRUSTED_ORIGINS=arynstal.es,www.arynstal.es

# Base de datos
DB_NAME=arynstal
DB_USER=YOUR_DB_USER
DB_PASSWORD=CONTRASEÑA_DE_POSTGRESQL
DB_HOST=localhost
DB_PORT=5432

# Email transaccional (Brevo) - emails automáticos de Django
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@dominio.com
EMAIL_HOST_PASSWORD=tu-api-key-de-brevo
DEFAULT_FROM_EMAIL=Arynstal <noreply@arynstal.es>

# Notificaciones
LEAD_NOTIFICATION_EMAIL=your-email@example.com
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

El archivo `gunicorn.conf.py` ya está incluido en el repositorio. Verificar que está presente:

```bash
ls /var/www/arynstal/app/gunicorn.conf.py
```

Si necesitas ajustar algo, editarlo:

```bash
nano /var/www/arynstal/app/gunicorn.conf.py
```

Contenido esperado:

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
User=YOUR_USER
Group=YOUR_USER
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

### 11.1 Verificar Email Corporativo (Zoho)

Después de configurar los registros DNS (sección 3), volver a Zoho Mail Admin:

1. Ir a Zoho Mail Admin → Domain Settings → Domain Verification
2. Seleccionar verificación por **registro TXT** (ya configurado en DNS)
3. Hacer clic en "Verify" - Zoho comprobará el registro TXT
4. Verificar que los registros MX están correctos (Zoho lo comprueba automáticamente)

### 11.2 Crear Buzones en Zoho

Una vez verificado el dominio, crear los 5 buzones del plan Free:

| Buzón | Uso | Acceso |
|-------|-----|--------|
| `info@arynstal.es` | Email principal, contacto público | Carlos + madre (administrativa) |
| `carlos@arynstal.es` | IT/admin, reportes DMARC | Carlos |
| `nombre1@arynstal.es` | Personal (familiar) | Familiar 1 |
| `nombre2@arynstal.es` | Personal (familiar) | Familiar 2 |
| `nombre3@arynstal.es` | Personal (familiar) | Familiar 3 |

**Pasos para cada buzón**:
1. Zoho Mail Admin → Users → Add User
2. Rellenar nombre y crear contraseña
3. El usuario recibirá instrucciones de acceso

**Nota**: `info@` es el email que aparece en la web y formularios. Carlos y la administrativa gestionan este buzón. Considerar configurar un alias o acceso compartido.

### 11.3 Test Email Corporativo

Verificar que Zoho funciona correctamente:

1. **Webmail**: Ir a [mail.zoho.eu](https://mail.zoho.eu) → Iniciar sesión con `info@arynstal.es`
2. **Enviar test**: Enviar un email desde `info@arynstal.es` a un Gmail personal
3. **Recibir test**: Enviar un email desde Gmail a `info@arynstal.es`
4. **Verificar headers**: En Gmail, al recibir el email de Zoho, hacer clic en "Mostrar original" y comprobar que SPF y DKIM pasan

**Configuración IMAP** (para clientes de correo):

| Parámetro | Valor |
|-----------|-------|
| Servidor entrante (IMAP) | `imappro.zoho.eu` |
| Puerto IMAP | 993 (SSL) |
| Servidor saliente (SMTP) | `smtppro.zoho.eu` |
| Puerto SMTP | 465 (SSL) |
| Autenticación | Email completo + contraseña |

### 11.4 Autenticar Dominio en Brevo

1. En Brevo → Settings → Senders & Domains → Domains
2. Verificar que `arynstal.es` aparece como verificado
3. Comprobar que DKIM (selector `mail`) está validado
4. Si no está verificado, revisar el registro DKIM en Cloudflare (sección 3.5)

### 11.5 Probar Email Transaccional (Django)

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
    'Arynstal <noreply@arynstal.es>',
    ['your-email@example.com'],
    fail_silently=False,
)
```

**Verificaciones**:
- El email llega a la bandeja de entrada (no spam)
- El remitente aparece como "Arynstal" con `noreply@arynstal.es`
- En Gmail → "Mostrar original": SPF = pass, DKIM = pass

### 11.6 Troubleshooting Email

**Emails de Django van a spam**:
1. Verificar SPF: `dig arynstal.es TXT +short` → debe incluir `spf.brevo.com`
2. Verificar DKIM en Brevo: Settings → Domains → comprobar estado
3. Verificar DMARC: `dig _dmarc.arynstal.es TXT +short`
4. Usar [Mail Tester](https://www.mail-tester.com/) para puntuación completa

**Zoho no recibe emails**:
1. Verificar MX: `dig arynstal.es MX +short` → debe mostrar `mx.zoho.eu`
2. Verificar que los registros MX NO están proxied en Cloudflare
3. Comprobar que el dominio está verificado en Zoho Admin

**Django no puede enviar (ConnectionError/TimeoutError)**:
1. Verificar credenciales en `.env`: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
2. Verificar que el puerto 587 está abierto: `telnet smtp-relay.brevo.com 587`
3. Verificar en Brevo que la API key está activa
4. Comprobar logs: `tail -20 /var/www/arynstal/logs/django_errors.log`

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
DB_USER="YOUR_DB_USER"
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

- [ ] DNS apuntando al servidor (registros A)
- [ ] DNS email configurado (MX, SPF, DKIM, DMARC)
- [ ] SSL funcionando (https://arynstal.es)
- [ ] Página de inicio carga correctamente
- [ ] Formulario de contacto funciona
- [ ] Se recibe email de notificación (via Brevo)
- [ ] Email corporativo funciona (Zoho: info@arynstal.es)
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
sudo chown -R YOUR_USER:YOUR_USER /var/www/arynstal/app/staticfiles/
```

### Problema: Error de base de datos

```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Verificar conexión
psql -U YOUR_DB_USER -d arynstal -h localhost

# Verificar variables de entorno
cat /var/www/arynstal/app/.env | grep DB_
```

### Problema: Emails no se envían

Ver sección [11.6 Troubleshooting Email](#116-troubleshooting-email) para diagnóstico detallado.

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
| 1.2 | 2026-02-10 | Sección 0 (decisiones técnicas), Zoho Mail Free, DNS completa (MX, SPF, DKIM, DMARC), sección 11 reescrita (email corporativo + transaccional) |
| 1.3 | 2026-02-11 | Sección 0 migrada a INFRAESTRUCTURA.md — DEPLOY_GUIDE queda puramente procedimental |

---

*Documento complementario a `INFRAESTRUCTURA.md`*
