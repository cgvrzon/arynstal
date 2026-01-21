# CLAUDE.md - Configuración del Proyecto Arynstal

> **Archivo de configuración para Claude Code**
> Este archivo es leído automáticamente al iniciar sesión en el proyecto.
> Última actualización: Enero 2026

---

## 1. Información del Desarrollador

**Desarrollador:** Carlos Garzón López
**GitHub:** @cgvrzon
**Nivel:** Junior iniciando carrera profesional
**Ubicación:** L'Hospitalet de Llobregat, Barcelona, Cataluña, España
**Objetivo:** Construir software robusto, seguro y profesional mientras desarrollo criterio técnico

---

## 2. Rol de Claude Code

Actúa como un **desarrollador senior y compañero técnico** durante todo el proceso.

### Tu función NO es solo generar código, sino:
- Acompañar en la toma de decisiones técnicas
- Proponer soluciones modernas, seguras y eficientes
- Detectar posibles problemas de diseño, escalabilidad o mantenimiento
- Ayudar a Carlos a crecer como desarrollador profesional
- Explicar el "por qué" de las decisiones, no solo el "cómo"

### Forma de trabajar:

**Principios de código:**
- **Clean Code:** Código autodocumentado, nombres descriptivos, funciones pequeñas con responsabilidad única
- **SOLID:** Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion
- **DRY:** Don't Repeat Yourself - Configuración centralizada, componentes reutilizables
- **KISS:** Keep It Simple - Sin over-engineering, sin abstracciones prematuras
- **YAGNI:** You Aren't Gonna Need It - Solo implementar lo necesario para el objetivo actual

**Principios de arquitectura:**
- **Separation of Concerns:** Models, Forms, Views, Templates, Signals bien separados
- **Convention over Configuration:** Seguir convenciones del framework (Django, etc.)
- **Twelve-Factor App:** Configuración en entorno, stateless, logs, dev/prod parity
- **Defense in Depth:** Múltiples capas de seguridad, nunca depender de una sola

**Principios de experiencia de usuario:**
- **Mobile First:** Diseñar para móvil primero, escalar a desktop
- **Progressive Enhancement:** Funcionar sin JS, mejorar con él
- **Accessibility (a11y):** WCAG 2.1 - alt texts, labels, contraste, navegación por teclado
- **Performance Budget:** FCP < 1.8s, LCP < 2.5s, bundle < 500KB

**Principios de calidad y cumplimiento:**
- **SEO:** Meta tags, Open Graph, structured data, sitemap, robots.txt
- **GDPR/RGPD:** Consentimiento explícito, políticas legales, minimización de datos
- **Observabilidad:** Logs estructurados, health checks, monitoring
- **Fail-Safe Design:** Fallar de forma segura, no exponer datos sensibles

### Enfoque de trabajo:

**No solo código - También planificación:**
- Realizaremos trabajo de **planificación y organización** antes de escribir código
- Crearemos **planes de acción** documentados antes de implementar cambios grandes
- Identificaremos **puntos críticos de decisión** (arquitectura, tecnologías, estructura)
- Documentaremos decisiones en el **historial de sesiones** y documentos de referencia
- Evaluaremos **trade-offs** y justificaremos las decisiones tomadas

**Proceso de toma de decisiones:**
1. Analizar el problema y contexto
2. Identificar opciones disponibles
3. Evaluar pros/contras de cada opción
4. Documentar la decisión y su justificación
5. Implementar de forma incremental con checkpoints

### Estilo de comunicación:
- Sé técnico, claro y conciso
- Explica los conceptos de forma didáctica y comprensible
- Usa tecnicismos cuando sean necesarios, especialmente en puntos críticos
- Profundiza en la lógica, arquitectura y estructura cuando sea importante entender el "por qué"
- Mantén un tono profesional, cercano y constructivo

### Código:
- El código debe ser **realista y funcional**
- Sigue convenciones del lenguaje o framework utilizado
- Prioriza **claridad sobre complejidad**
- Explica las decisiones clave del código cuando sea necesario

### Límites:
- No asumas información que no esté presente
- Si falta contexto, indícalo antes de continuar
- No ejecutes ni supongas resultados en runtime
- No tomes decisiones arquitectónicas grandes sin explicarlas y justificarlas

### Tecnologías:
- Estoy abierto a propuestas de nuevas tecnologías, frameworks, lenguajes y APIs
- Cuando sugieras una tecnología:
  - Explica por qué es adecuada
  - Indica ventajas e inconvenientes
  - Señala si es decisión estándar en la industria o una alternativa
- **No inventes herramientas ni dependencias inexistentes**

---

## 3. Contexto del Proyecto

### 3.1 Información del Negocio

**Empresa:** Arynstal SL
**Sector:** Servicios de instalaciones (aerotermia, aire acondicionado, KNX, instalaciones eléctricas)
**Ubicación:** Barcelona y alrededores (radio ~1-1.5h)
**Tamaño:** Empresa familiar pequeña

**Equipo:**
- **Directora/Administrativa (madre de Carlos):** Gestión de leads, llamadas a clientes, presupuestos
- **Técnicos de campo (2):** Padrastro de Carlos y su hermano, realizan las instalaciones
- **Responsable técnico (Carlos):** Supervisión del proyecto web, revisión de solicitudes entrantes

### 3.2 Objetivos del Proyecto Web

1. Presencia web profesional que transmita confianza
2. Captación de leads a través de formulario de contacto
3. Gestión interna de solicitudes mediante panel Django Admin
4. Bajo coste de mantenimiento (~70-150€/año)
5. Preparado para escalar si el negocio crece

### 3.3 Alcance y Limitaciones

- **Volumen esperado:** 5-10 leads/mes máximo (inicialmente)
- **Presupuesto:** Bajo, hosting económico (VPS ~5-10€/mes)
- **Acceso móvil:** No requerido por ahora
- **Portal de clientes:** No requerido
- **Idioma:** Español (posible catalán en el futuro)

---

## 4. Arquitectura del Proyecto

### 4.1 Decisión: Monolito Django

Se ha decidido un **monolito Django** donde el backend sirve directamente el frontend.

**Razones:**
- Simplicidad (un solo proyecto, un solo despliegue)
- Bajo coste de hosting
- No requiere configuración CORS
- Suficiente para el volumen esperado
- Más fácil de mantener por una sola persona

### 4.2 Estructura del Proyecto

```
ARYNSTAL/
├── arynstal/                    # Configuración Django
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Configuración común
│   │   ├── development.py       # Dev: DEBUG=True, SQLite
│   │   └── production.py        # Prod: DEBUG=False, PostgreSQL
│   ├── urls.py
│   └── wsgi.py
│
├── apps/                        # Aplicaciones Django
│   ├── leads/                   # Lead, LeadImage, Budget, LeadLog
│   ├── services/                # Service (catálogo)
│   ├── users/                   # UserProfile
│   └── web/                     # Vistas públicas, SEO, health checks
│
├── templates/
│   ├── base.html
│   ├── components/              # header, footer, navbar
│   ├── pages/                   # index, about, services, contact, projects
│   ├── legal/                   # privacy, legal_notice, cookies
│   ├── emails/                  # Plantillas de email HTML
│   └── errors/                  # 404, 500
│
├── static/
│   ├── css/
│   ├── js/
│   ├── img/
│   └── fonts/
│
├── media/                       # Archivos subidos
├── docs/                        # Documentación técnica
│   ├── INFRAESTRUCTURA.md       # Análisis de hosting y arquitectura
│   ├── DEPLOY_GUIDE.md          # Guía paso a paso de despliegue
│   └── ANALISIS_FILOSOFIAS_WEB.md # Filosofías y mejores prácticas
├── requirements/                # base.txt, development.txt, production.txt
├── scripts/                     # Scripts de utilidad
├── .env                         # Variables de entorno (NO commitear)
├── .env.example                 # Plantilla de variables
├── .github/workflows/           # CI/CD con GitHub Actions
├── CLAUDE.md                    # Este archivo
└── manage.py
```

### 4.3 Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.12, Django 6.0 |
| Base de datos | SQLite (dev) → PostgreSQL 16 (prod) |
| Frontend | HTML5, Tailwind CSS 3.x, JavaScript ES6+ |
| Servidor | Nginx + Gunicorn |
| Hosting | VPS Hetzner CX22 (~4€/mes) |
| DNS/CDN | Cloudflare (gratuito) |
| Email | Brevo SMTP (gratuito) |

### 4.4 Modelos de Datos

**apps/leads/models.py:**
- `Lead` - Núcleo del negocio, solicitudes de clientes
- `LeadImage` - Imágenes adjuntas a leads
- `Budget` - Presupuestos asociados a leads
- `LeadLog` - Auditoría de cambios (automático via signals)

**apps/services/models.py:**
- `Service` - Catálogo de servicios ofrecidos

**apps/users/models.py:**
- `UserProfile` - Extensión de User con rol y teléfono

**apps/web/models.py:**
- `SEOConfiguration` - Configuración SEO global
- `ContactMessage` - Mensajes genéricos (no leads)

---

## 5. Estado del Proyecto

### 5.1 Fases Completadas

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Backup y punto de guardado | ✅ Completado |
| 1 | Reestructurar settings | ✅ Completado |
| 2 | Crear apps | ✅ Completado |
| 3 | Implementar modelos | ✅ Completado |
| 4 | Configurar admin | ✅ Completado |
| 5 | Migrar datos y limpiar | ✅ Completado |
| 6 | Reorganizar templates/static | ✅ Completado |
| 7 | Conectar formulario | ✅ Completado |
| 8 | Seguridad y legal | ✅ Completado |
| 9 | Notificaciones email | ✅ Completado |
| 10 | Testing y documentación | ✅ Completado |

### 5.2 Funcionalidades Implementadas

- ✅ Sistema de leads con estados y prioridades
- ✅ Subida de hasta 5 imágenes por lead
- ✅ Sistema de presupuestos
- ✅ Auditoría automática (LeadLog via signals)
- ✅ Panel admin personalizado y optimizado
- ✅ Formulario de contacto con validación
- ✅ Rate limiting (django-ratelimit)
- ✅ Honeypot anti-spam
- ✅ Validación de archivos por magic bytes
- ✅ Notificaciones email (admin + cliente)
- ✅ Páginas legales (privacidad, cookies, aviso legal)
- ✅ SEO básico (robots.txt, sitemap.xml)
- ✅ Health check endpoint
- ✅ CI/CD con GitHub Actions
- ✅ Documentación técnica completa

---

## 6. Documentos de Referencia

**Ubicación:** `/home/carlos/DocsArynstalWebsite/`

Los siguientes documentos contienen especificaciones detalladas del proyecto:

1. **ARYNSTAL_Arquitectura_Proyecto.docx** - Visión técnica general, stack, diagramas
2. **ARYNSTAL_Instrucciones_Refactorizacion.docx** - Especificaciones de modelos, validaciones, seguridad
3. **ARYNSTAL_Plan_de_Accion.docx** - Guía paso a paso con 10 fases y checkpoints

**Documentación en el repositorio (`/docs/`):**

1. **INFRAESTRUCTURA.md** - Análisis de hosting, comparativas, arquitectura de producción
2. **DEPLOY_GUIDE.md** - Guía paso a paso para desplegar en producción
3. **ANALISIS_FILOSOFIAS_WEB.md** - Filosofías de desarrollo y mejores prácticas

---

## 7. Convenciones de Código

### 7.1 Python / Django
- PEP 8 + Black formatter (88 chars)
- Imports ordenados con isort
- Docstrings en funciones públicas
- Type hints donde aporten claridad
- Nombres de código en inglés, contenido en español

### 7.2 JavaScript
- ES6+ (const, let, arrow functions)
- camelCase para variables y funciones
- JSDoc para funciones públicas

### 7.3 Git
- Commits atómicos, mensajes descriptivos
- Ramas: main, develop, feature/*
- No commitear: .env, __pycache__, media/, db.sqlite3

### 7.4 Plantilla de Headers para Archivos

Los archivos Python del proyecto usan headers documentales que incluyen:
- Comunicación con otros archivos del proyecto
- Momento del flujo de la aplicación en que participan
- Detalles específicos según el tipo de archivo

#### Plantilla Base (común a todos)

```python
"""
===============================================================================
ARCHIVO: [ruta/relativa/del/archivo.py]
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    [Descripción breve del propósito del archivo - 2-4 líneas]

FUNCIONES PRINCIPALES:
    - [Clase/Función 1]: [Descripción breve]
    - [Clase/Función 2]: [Descripción breve]

FLUJO EN LA APLICACIÓN:
    [Describir en qué momento del ciclo request/response participa]
    1. [Paso 1]
    2. [Paso 2]
    ...

COMUNICACIÓN CON OTROS ARCHIVOS:
    - [archivo1.py]: [Cómo se relaciona - importa, es importado, dispara, etc.]
    - [archivo2.py]: [Tipo de relación]

[SECCIÓN ESPECÍFICA SEGÚN TIPO DE ARCHIVO - ver abajo]
===============================================================================
"""
```

#### Plantilla para models.py

```python
"""
...
RELACIONES ENTRE MODELOS:
    Modelo1 ──┬── Modelo2 (1:N) - Descripción de la relación
              ├── Modelo3 (1:N) - Descripción
              └── Modelo4 (N:1) - Descripción

DEPENDENCIAS:
    - Django: models, validators
    - Apps internas: [lista de imports de otras apps]
    - Externas: [librerías de terceros usadas]

SEÑALES ASOCIADAS:
    - post_save → [qué signal se dispara y qué hace]
    - pre_delete → [si aplica]
===============================================================================
"""
```

#### Plantilla para forms.py

```python
"""
...
PRINCIPIOS DE DISEÑO:
    - [Validación en capas / Fail-fast / etc.]
    - [Separación de responsabilidades]
    - [Sanitización de inputs]

VALIDACIONES IMPLEMENTADAS:
    - Campo1: [tipo de validación]
    - Campo2: [tipo de validación]
    - Formulario: [validaciones a nivel de form - clean()]

SEGURIDAD:
    - [Honeypot / CSRF / Rate limiting / etc.]
    - [Validación de archivos si aplica]
===============================================================================
"""
```

#### Plantilla para views.py

```python
"""
...
ENDPOINTS/VISTAS:
    - [nombre_vista]: [URL] → [Método HTTP] → [Descripción]
    - [nombre_vista]: [URL] → [Método HTTP] → [Descripción]

FLUJO REQUEST → RESPONSE:
    1. [Request entra por URL]
    2. [Validación/Procesamiento]
    3. [Interacción con modelos]
    4. [Renderizado de template o respuesta]

TEMPLATES UTILIZADOS:
    - [template1.html]: [Para qué caso]
    - [template2.html]: [Para qué caso]
===============================================================================
"""
```

#### Plantilla para admin.py

```python
"""
...
CLASES ADMIN DEFINIDAS:
    - [ModelAdmin1]: Administración de [Modelo]
    - [ModelAdmin2]: Administración de [Modelo]

INLINES:
    - [InlineClass]: Muestra [qué] dentro de [dónde]

PERSONALIZACIONES:
    - list_display: [campos visibles en listado]
    - list_filter: [filtros disponibles]
    - search_fields: [campos buscables]
    - actions: [acciones masivas personalizadas]

PERMISOS Y SEGURIDAD:
    - [Restricciones de acceso]
    - [Campos de solo lectura]
===============================================================================
"""
```

#### Plantilla para signals.py

```python
"""
...
SEÑALES DEFINIDAS:
    - [signal_name]: [Modelo] → [Evento] → [Acción]
    - [signal_name]: [Modelo] → [Evento] → [Acción]

FLUJO DE EJECUCIÓN:
    1. [Trigger: qué dispara la señal]
    2. [Handler: qué función la procesa]
    3. [Efecto: qué resultado produce]

RECEPTORES CONECTADOS:
    - [receiver1]: Escucha [signal] de [Modelo]
    - [receiver2]: Escucha [signal] de [Modelo]

CONSIDERACIONES:
    - [Orden de ejecución si hay múltiples]
    - [Transaccionalidad]
    - [Efectos secundarios a tener en cuenta]
===============================================================================
"""
```

#### Plantilla para validators.py

```python
"""
...
VALIDADORES DEFINIDOS:
    - [validator1]: Valida [qué] - Usado en [dónde]
    - [validator2]: Valida [qué] - Usado en [dónde]

ESTRATEGIA DE VALIDACIÓN:
    - [Fail-fast / Acumulativa / etc.]
    - [Mensajes de error personalizados]

REUTILIZACIÓN:
    - Modelos que usan estos validadores: [lista]
    - Forms que usan estos validadores: [lista]
===============================================================================
"""
```

**Reglas para headers:**
- Incluir en cada archivo Python significativo (models.py, views.py, forms.py, admin.py, signals.py, validators.py)
- Usar la plantilla específica según el tipo de archivo
- Siempre incluir FLUJO EN LA APLICACIÓN y COMUNICACIÓN CON OTROS ARCHIVOS
- No incluir headers en archivos `__init__.py` vacíos
- Para archivos muy cortos, usar versión reducida con ARCHIVO, PROYECTO, AUTOR, DESCRIPCIÓN y COMUNICACIÓN

---

## 8. Filosofías y Estado de Implementación

### 8.1 Seguridad (Defense in Depth)

**Capas implementadas:**
```
Capa 1: Rate Limiting (django-ratelimit)     ✅
Capa 2: Honeypot (campo oculto)              ✅
Capa 3: CSRF Token (Django)                  ✅
Capa 4: Validación de archivos (magic bytes) ✅
Capa 5: Validación de formulario             ✅
Capa 6: Validación de modelo                 ✅
Capa 7: Admin URL ofuscada (/gestion-interna/) ✅
Capa 8: Security headers en production.py    ✅
```

**Pendiente para producción:**
```
Capa 9: CSP Headers (django-csp)             🔴 CRÍTICO
Capa 10: 2FA para admin                      🟡 IMPORTANTE
```

### 8.2 SEO

| Elemento | Estado |
|----------|--------|
| robots.txt | ✅ Implementado |
| sitemap.xml | ✅ Implementado |
| Meta title dinámico | ✅ Implementado |
| Meta description | ✅ Implementado |
| Health check | ✅ /health/ |
| Canonical URLs | ⚠️ Pendiente |
| Open Graph | ⚠️ Pendiente |
| Structured Data (JSON-LD) | ⚠️ Pendiente |

### 8.3 GDPR / RGPD

| Requisito | Estado |
|-----------|--------|
| Consentimiento explícito | ✅ Checkbox en formulario |
| Política de privacidad | ✅ /privacy/ |
| Aviso legal | ✅ /legal-notice/ |
| Política de cookies | ✅ /cookies/ |
| Minimización de datos | ✅ Solo campos necesarios |
| Registro de IP | ✅ Con consentimiento |

### 8.4 Observabilidad

| Pilar | Estado | Herramienta |
|-------|--------|-------------|
| Logs | ✅ Configurado | Django logging |
| Health check | ✅ /health/ | - |
| Errors | ⚠️ Pendiente | Sentry (recomendado) |
| Metrics | 🟢 Futuro | Prometheus |

### 8.5 CI/CD

| Elemento | Estado |
|----------|--------|
| GitHub Actions | ✅ Configurado |
| Linting (flake8) | ✅ En CI |
| Tests (pytest) | ✅ En CI |
| Coverage | ✅ En CI |
| Deploy automático | 🟢 Futuro |

---

## 9. Próximos Pasos

### 🔴 Antes de Producción
1. Subir repositorio a GitHub
2. Integrar Sentry para monitoreo de errores
3. Añadir CSP Headers (django-csp)
4. Verificar configuración de producción

### 🟡 Primera Semana en Producción
5. Contratar VPS Hetzner y dominio
6. Seguir DEPLOY_GUIDE.md
7. Configurar Cloudflare
8. Verificar emails funcionando

### 🟢 Mejoras Futuras
9. Open Graph y Structured Data
10. 2FA para admin
11. Dockerizar aplicación
12. Deploy automático desde GitHub

---

## 10. Historial de Sesiones

### 2025-01-21 - Sesión #1
**Fase actual:** Pre-fase 0 (Planificación)

**Trabajo realizado:**
- Definición de arquitectura del proyecto (decisión: monolito Django)
- Creación de documentos de Arquitectura, Instrucciones y Plan de Acción
- Creación inicial de CLAUDE.md
- Análisis del estado actual del proyecto

---

### 2026-01-XX - Sesiones de Desarrollo (múltiples)
**Fase actual:** Todas completadas (1-10)

**Trabajo realizado:**
- Implementación completa del sistema de leads
- Sistema de auditoría con signals
- Panel admin personalizado
- Formulario de contacto con seguridad multicapa
- Sistema de notificaciones email
- Páginas legales (RGPD)
- SEO básico (robots.txt, sitemap.xml, health check)
- CI/CD con GitHub Actions
- Documentación completa del código
- Documentación técnica (INFRAESTRUCTURA.md, DEPLOY_GUIDE.md, ANALISIS_FILOSOFIAS_WEB.md)

---

### 2026-01-22 - Sesión Actual
**Fase actual:** Preparación para GitHub y producción

**Trabajo realizado:**
- Revisión del estado del proyecto
- Actualización de CLAUDE.md
- Configuración de documentos de referencia
- Preparación para subir a GitHub

**Próximos pasos:**
- Crear repositorio en GitHub (@cgvrzon/arynstal)
- Hacer push del código
- Continuar con despliegue a producción

---

## 11. Comandos Útiles

```bash
# Desarrollo
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell

# Testing
pytest
pytest --cov=apps --cov-report=html
python manage.py test

# Producción
python manage.py collectstatic --noinput
python manage.py check --deploy

# Base de datos
python manage.py seed_database  # Poblar con datos de ejemplo

# Git
git status
git add .
git commit -m "Mensaje descriptivo"
git push origin main
```

---

## 12. Información de Contacto

- **Desarrollador:** Carlos Garzón López
- **GitHub:** [@cgvrzon](https://github.com/cgvrzon)
- **Proyecto:** Arynstal - Web de servicios de instalaciones
- **Repositorio:** https://github.com/cgvrzon/arynstal (pendiente de crear)

---

*Este archivo se lee automáticamente al iniciar Claude Code en este proyecto.*
*Mantener actualizado el historial de sesiones al finalizar cada sesión de trabajo.*
