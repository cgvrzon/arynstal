# Stack Orpheus - Cleanup Guide

> Guia para revertir el codigo didactico (Stack Orpheus) del proyecto Arynstal.
> Docker se mantiene (infraestructura real). Solo se eliminan Celery y DRF.

---

## Que es Stack Orpheus

Stack Orpheus es una serie de ejercicios formativos integrados directamente
en el proyecto Arynstal para aprender tecnologias en contexto real:

- **Modulo 02 - Celery**: Tareas asincronas con Redis (notificaciones email)
- **Modulo 03 - DRF**: API REST con Django REST Framework

El codigo esta marcado con comentarios `[STACK-ORPHEUS:MODULO]` para
facilitar su identificacion y eliminacion.

---

## Encontrar todos los flags

```bash
# Todos los flags
grep -rn "STACK-ORPHEUS" --include="*.py" --include="*.txt" .

# Solo Celery
grep -rn "STACK-ORPHEUS:CELERY" --include="*.py" --include="*.txt" .

# Solo DRF
grep -rn "STACK-ORPHEUS:DRF" --include="*.py" --include="*.txt" .
```

---

## Modulo 02 - Celery

### Archivos a eliminar (completos)

| Archivo | Contenido |
|---------|-----------|
| `arynstal/celery.py` | Configuracion de la app Celery |
| `apps/leads/tasks.py` | Tareas asincronas (notificaciones) |

### Bloques a revertir

#### `arynstal/__init__.py`

Eliminar todo el contenido (import de celery_app). El archivo queda vacio.

#### `requirements/base.txt`

Eliminar:
```
celery[redis]>=5.4
flower>=2.0
```

#### `arynstal/settings/base.py`

Eliminar la seccion 15 completa (CELERY_BROKER_URL hasta CELERY_BEAT_SCHEDULE).

#### `arynstal/settings/development.py`

Eliminar:
```python
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

#### `arynstal/settings/production.py`

Eliminar la seccion CELERY completa (ALWAYS_EAGER + comentarios de activacion).

#### `arynstal/settings/docker.py`

Eliminar:
```python
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
```

#### `apps/web/views.py`

Revertir el try/except `.delay()` a llamada directa:
```python
# ANTES (Celery):
try:
    from apps.leads.tasks import send_new_lead_notifications
    send_new_lead_notifications.delay(lead.id)
except Exception:
    notify_new_lead(lead)

# DESPUES (cleanup):
notify_new_lead(lead)
```

#### `apps/leads/admin.py` (2 bloques)

Revertir asignacion de tecnico:
```python
# ANTES (Celery):
try:
    from apps.leads.tasks import send_lead_assigned_notification
    send_lead_assigned_notification.delay(obj.id, obj.assigned_to.id)
except Exception:
    notify_lead_assigned(obj, obj.assigned_to)

# DESPUES (cleanup):
notify_lead_assigned(obj, obj.assigned_to)
```

Revertir notificacion de nota:
```python
# ANTES (Celery):
try:
    from apps.leads.tasks import send_note_added_notification
    send_note_added_notification.delay(obj.id, request.user.id)
except Exception:
    notify_note_added(obj, request.user)

# DESPUES (cleanup):
notify_note_added(obj, request.user)
```

---

## Modulo 03 - DRF

### Archivos a eliminar (completos)

| Archivo | Contenido |
|---------|-----------|
| `arynstal/api_urls.py` | Router con endpoints de la API |
| `apps/projects/serializers.py` | Serializers de proyectos |
| `apps/projects/api_views.py` | ViewSets de proyectos |
| `apps/projects/test_api.py` | Tests de la API de proyectos |
| `apps/services/serializers.py` | Serializer de servicios |
| `apps/services/api_views.py` | ViewSet de servicios |
| `apps/services/test_api.py` | Tests de la API de servicios |
| `apps/leads/serializers.py` | Serializers de leads y budgets |
| `apps/leads/api_views.py` | ViewSets de leads y budgets |
| `apps/leads/test_api.py` | Tests de la API de leads |
| `apps/leads/permissions.py` | Permisos DRF custom |

### Bloques a revertir

#### `requirements/base.txt`

Eliminar:
```
djangorestframework>=3.15
django-filter>=24.0
django-cors-headers>=4.0
```

#### `arynstal/settings/base.py`

1. Eliminar de INSTALLED_APPS:
```python
'rest_framework',
'django_filters',
'corsheaders',
```

2. Eliminar de MIDDLEWARE:
```python
'corsheaders.middleware.CorsMiddleware',
```

3. Eliminar secciones 17 (REST_FRAMEWORK) y 18 (CORS_ALLOWED_ORIGINS) completas.

#### `arynstal/settings/development.py`

Eliminar:
```python
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]
```

#### `arynstal/settings/docker.py`

Eliminar:
```python
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]
```

#### `arynstal/urls.py`

Eliminar la linea:
```python
path('api/v1/', include('arynstal.api_urls')),
```

#### `apps/leads/signals.py`

Revertir la condicion:
```python
# ANTES (DRF):
if created and instance.source in ('web', 'api'):

# DESPUES (cleanup):
if created and instance.source == 'web':
```

#### `apps/leads/models.py`

Eliminar de SOURCE_CHOICES:
```python
('api', 'API REST'),
```

### Migracion reversa

Despues de eliminar `('api', 'API REST')` de SOURCE_CHOICES:

```bash
python manage.py makemigrations leads
python manage.py migrate
```

Tambien eliminar la migracion didactica:
- `apps/leads/migrations/0003_add_api_source_choice.py`

**Nota**: Si ya hay leads con `source='api'` en la BD, actualizarlos antes:
```python
Lead.objects.filter(source='api').update(source='web')
```

---

## Verificacion post-cleanup

```bash
# Chequeo de Django
python manage.py check --deploy

# Tests (deben pasar todos excepto los test_api.py eliminados)
pytest -q

# Verificar que no quedan flags
grep -rn "STACK-ORPHEUS" --include="*.py" --include="*.txt" .
# Resultado esperado: sin resultados
```

---

## Nota sobre Docker

Los archivos de Docker (`docker-compose.yml`, `Dockerfile`, `.env.docker`,
`arynstal/settings/docker.py`) **se mantienen**. Son infraestructura real
del proyecto, no material didactico.

Al hacer cleanup de Celery, eliminar del `docker-compose.yml` solo los
servicios `worker`, `beat` y `flower` (redis se mantiene si se usa para cache).
