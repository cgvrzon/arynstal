# Plan de revisión de código - Arynstal

**Objetivo:** Revisar el código del proyecto antes de subir la página a producción, detectando posibles invenciones, deuda técnica y sobreingeniería.

**Estado:** En curso  
**Última actualización:** Enero 2026

---

## Checklist de revisión por app

### 1. App `leads`

| Archivo | Revisado | Notas |
|---------|----------|-------|
| `models.py` | ✅ | Modelos correctos. Lead, LeadImage, Budget, LeadLog. FK a `services.Service` OK. |
| `forms.py` | ✅ | LeadForm solo name, phone, email, message. Validaciones coherentes. |
| `validators.py` | ✅ | Eliminado import no usado `FileExtensionValidator`. Pendiente: `validate_spanish_phone` y `validate_min_images_size` no usados; WEBP solo comprueba `RIFF`. |
| `signals.py` | ✅ | Logs creación y cambios. Variable global `_lead_previous_state` documentada. |
| `notifications.py` | ✅ | **Corregido:** `lead_url` vía `reverse('admin:leads_lead_change', ...)` y URL absoluta con `COMPANY_INFO['WEBSITE']`. |
| `admin.py` | ⚠️ | **Logs duplicados:** al guardar desde admin, tanto `save_model` como los signals crean LeadLog. Pendiente unificar. |
| `views.py` | ✅ | Solo `from django.shortcuts import render` (leads no expone vistas propias). |
| `management/commands/migrate_contacts_to_leads.py` | ✅ | **Obsoleto:** ya no importa web/leads; devuelve mensaje claro y sale. |

### 2. App `services`

| Archivo | Revisado | Notas |
|---------|----------|-------|
| `models.py` | ✅ | Service con slug, validate_image_file. Correcto. |
| `admin.py` | ✅ | ModelAdmin estándar. |
| `views.py` | ✅ | Solo render; el listado dinámico podría venir después. |

### 3. App `users`

| Archivo | Revisado | Notas |
|---------|----------|-------|
| `models.py` | ✅ | UserProfile, roles, métodos de permisos. Correcto. |
| `signals.py` | ✅ | Crea UserProfile al crear User. `get_or_create` evita duplicados. |
| `admin.py` | Pendiente | Revisar uso de UserProfile en admin. |
| `views.py` | ✅ | Solo import render; sin vistas propias. |

### 4. App `web`

| Archivo | Revisado | Notas |
|---------|----------|-------|
| `views.py` | ✅ | **Corregido:** se valida cada imagen con `validate_image_file` antes de crear `LeadImage`. |
| `urls.py` | ✅ | Rutas correctas. robots/sitemap vía `STATICFILES_DIRS[0]`. |
| `forms.py` | - | No existe; formulario en leads. |
| `models.py` | ✅ | Sin modelos (decisión documentada). |
| `management/commands/seed_database.py` | ✅ | Usa `apps.*` correctamente. |

### 5. Templates y emails

| Archivo | Revisado | Notas |
|---------|----------|-------|
| `emails/lead_admin_notification.html` | ✅ | **Corregido:** usa `lead.service` y `lead.service.name`; `lead_url` viene de notifications (reverse + WEBSITE). |
| `pages/contact.html` | ✅ | Honeypot, fotos, privacidad. Formulario no incluye `service` (form solo name, phone, email, message). |

### 6. Configuración y dependencias

| Elemento | Revisado | Notas |
|----------|----------|-------|
| `requirements/base.txt` | ✅ | Django, Pillow, django-ratelimit, sqlparse. Paquetes reales (PyPI). |
| `requirements/production.txt` | ✅ | psycopg2, gunicorn, whitenoise, python-dotenv, sentry-sdk, django-csp. |
| `FORM_SECURITY` | ✅ | Rate limit 5/h, honeypot. Vista usa `block=False` y maneja a mano; config `block: True` no se usa. |
| `NOTIFICATIONS['LEAD']` | ✅ | ADMIN_EMAIL, ENABLED, SEND_CUSTOMER_CONFIRMATION. |

---

## Resumen de hallazgos

### Críticos (arreglar antes de producción)

1. ~~**URL admin en emails**~~ ✅ Corregido: `reverse` + `COMPANY_INFO['WEBSITE']`.
2. ~~**Template email admin**~~ ✅ Corregido: `lead.service` y `lead.service.name`.
3. ~~**Validación de imágenes en contacto**~~ ✅ Corregido: `validate_image_file` en la vista antes de crear `LeadImage`.
4. ~~**Comando `migrate_contacts_to_leads`**~~ ✅ Obsoleto: mensaje claro, sin imports rotos.

### Importantes (recomendable arreglar)

5. **Logs duplicados en admin:** Al guardar un lead desde admin, se crean logs tanto en `save_model` como en signals. Unificar criterio (p. ej. solo signals o solo admin) para evitar duplicados.
6. **Validador WEBP:** Comprobar también la firma `WEBP` en el contenedor RIFF, no solo `RIFF`, para no aceptar otros formatos RIFF.

### Deuda técnica / limpieza

7. **`validators.py`:** ~~Import no usado `FileExtensionValidator`~~ ✅ Eliminado. Pendiente: valorar eliminar o usar `validate_spanish_phone` y `validate_min_images_size`.
8. **`Budget.clean()`:** `valid_until` debe ser futura; puede impedir guardar presupuestos antiguos al editarlos. Valorar relajar o excluir en solo-lectura.

### Tests y lint

- **Tests:** 101 tests pasan (`pytest`).
- **Lint (flake8):** Varios F401 (imports no usados), E226 (espacios en operadores), E402 (imports no al inicio). Los `import apps.*.signals` en `apps.py` son deliberados (registro por side-effect); considerar `# noqa` o excepción en .flake8.

---

## Plan de acción sugerido

1. ~~**Corregir notificaciones y template email**~~ ✅ Hecho.
2. ~~**Validar imágenes en `contact_us`**~~ ✅ Hecho.
3. ~~**Decidir sobre `migrate_contacts_to_leads`**~~ ✅ Marcado obsoleto.
4. **Evitar logs duplicados:** Unificar creación de LeadLog en admin vs signals (pendiente).
5. **Limpieza en `validators`:** Valorar eliminar `validate_spanish_phone` y `validate_min_images_size` si no se usan; afinar WEBP (pendiente).

---

## Cómo usar este plan

- Ir tachando ítems del checklist a medida que se revisan o corrigen.
- Actualizar “Notas” y “Resumen de hallazgos” si se encuentran más puntos.
- No considerar la revisión cerrada hasta que los **críticos** estén resueltos y los tests sigan pasando.
