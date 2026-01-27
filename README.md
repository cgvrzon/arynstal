# Arynstal - Sistema CRM

[![CI](https://github.com/cgvrzon/arynstal/actions/workflows/ci.yml/badge.svg)](https://github.com/cgvrzon/arynstal/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema CRM (Customer Relationship Management) para gestión de leads e instalaciones, desarrollado para **Arynstal SL**, empresa de instalaciones y reformas en Barcelona.

## Características

- **Gestión de Leads**: Captura y seguimiento de solicitudes de clientes
- **Panel de Administración**: Interface completa para gestionar leads, presupuestos y usuarios
- **Formulario de Contacto**: Con protección anti-spam (rate limiting + honeypot)
- **Sistema de Notificaciones**: Emails automáticos para admin y clientes
- **Catálogo de Servicios**: Servicios configurables desde el admin
- **Auditoría Completa**: Historial de cambios en cada lead
- **Roles de Usuario**: Admin, Oficina, Técnico de campo

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Django 6.0, Python 3.12 |
| Base de datos | PostgreSQL (prod) / SQLite (dev) |
| Frontend | HTML5, Tailwind CSS, Vite |
| Servidor | Gunicorn, Nginx |
| CI/CD | GitHub Actions |
| Monitoreo | Sentry |

## Instalación Rápida

### Requisitos

- Python 3.12+
- pip
- virtualenv (recomendado)

### Desarrollo Local

```bash
# Clonar el repositorio
git clone https://github.com/cgvrzon/arynstal.git
cd arynstal

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements/development.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Poblar con datos de prueba (opcional)
python manage.py seed_database

# Iniciar servidor de desarrollo
python manage.py runserver
```

Acceder a:
- Web: http://localhost:8000
- Admin: http://localhost:8000/admynstal/

## Estructura del Proyecto

```
arynstal/
├── apps/
│   ├── leads/          # CRM: Lead, Budget, LeadLog
│   ├── services/       # Catálogo de servicios
│   ├── users/          # Perfiles con roles
│   └── web/            # Vistas públicas
├── arynstal/
│   └── settings/       # Configuración (base/dev/prod)
├── templates/          # Templates HTML
├── static/             # CSS, JS, imágenes
├── docs/               # Documentación
│   ├── DEPLOY_GUIDE.md
│   ├── INFRAESTRUCTURA.md
│   ├── ANALISIS_FILOSOFIAS_WEB.md
│   ├── HISTORIAL_AUDITORIAS_LIGHTHOUSE.md
│   └── PLAN_REVISION_CODIGO.md
└── requirements/       # Dependencias por entorno
```

## Comandos Útiles

```bash
# Ejecutar tests
pytest

# Ejecutar tests con coverage
pytest --cov=apps --cov-report=html

# Linting
flake8 apps/ arynstal/

# Poblar base de datos
python manage.py seed_database
python manage.py seed_database --clear  # Limpiar y recrear

# Verificar configuración de producción
python manage.py check --deploy
```

## Despliegue

Ver [docs/DEPLOY_GUIDE.md](docs/DEPLOY_GUIDE.md) para instrucciones detalladas de despliegue en producción.

### Variables de Entorno Requeridas (Producción)

```bash
SECRET_KEY=<clave-secreta-de-50-caracteres>
ALLOWED_HOSTS=arynstal.es,www.arynstal.es
DB_PASSWORD=<contraseña-postgresql>
EMAIL_HOST_USER=<email-smtp>
EMAIL_HOST_PASSWORD=<contraseña-smtp>
SENTRY_DSN=<dsn-de-sentry>  # Opcional
```

## Testing

El proyecto incluye tests unitarios y de integración:

```bash
# Todos los tests
pytest

# Solo tests de una app
pytest apps/leads/

# Con verbose
pytest -v

# Generar reporte de coverage
pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

## Seguridad

- ✅ Protección CSRF
- ✅ Rate limiting (5 requests/hora por IP)
- ✅ Honeypot anti-bot
- ✅ Validación de archivos (magic bytes)
- ✅ Headers de seguridad (HSTS, CSP, X-Frame-Options)
- ✅ Passwords hasheados (PBKDF2)
- ✅ SQL injection prevention (ORM)
- ✅ XSS prevention (template escaping)

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [DEPLOY_GUIDE.md](docs/DEPLOY_GUIDE.md) | Guía paso a paso para despliegue |
| [INFRAESTRUCTURA.md](docs/INFRAESTRUCTURA.md) | Análisis de opciones de hosting |
| [ANALISIS_FILOSOFIAS_WEB.md](docs/ANALISIS_FILOSOFIAS_WEB.md) | Filosofías y mejores prácticas implementadas |
| [HISTORIAL_AUDITORIAS_LIGHTHOUSE.md](docs/HISTORIAL_AUDITORIAS_LIGHTHOUSE.md) | Auditorías de rendimiento |
| [PLAN_REVISION_CODIGO.md](docs/PLAN_REVISION_CODIGO.md) | Checklist de revisión pre-producción |
| [.env.example](.env.example) | Variables de entorno |

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## Autor

**@cgvrzon**

---

*Desarrollado con Django*
