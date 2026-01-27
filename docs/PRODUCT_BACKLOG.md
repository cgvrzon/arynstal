# Product Backlog - Arynstal CRM

> Documento de referencia del producto final deseado.
> Este documento define las funcionalidades requeridas y sus prioridades.

---

## Metodología MoSCoW

| Prioridad | Significado | Descripción |
|-----------|-------------|-------------|
| **M** | Must Have | Imprescindible para el MVP |
| **S** | Should Have | Importante, pero no crítico |
| **C** | Could Have | Deseable si hay tiempo |
| **W** | Won't Have | Fuera del alcance actual |

---

## EPIC 1: Web Pública

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-1.1 | Página de Inicio | M | Hero section, servicios destacados, CTA claro |
| US-1.2 | Página de Servicios | M | Listado de servicios con descripción e iconos |
| US-1.3 | Página Sobre Nosotros | M | Historia, equipo, valores de la empresa |
| US-1.4 | Página de Proyectos | S | Galería de proyectos realizados |
| US-1.5 | Formulario de Contacto | M | Validación frontend/backend, CSRF, honeypot, rate limit |
| US-1.6 | Páginas Legales | M | Política de privacidad, aviso legal, cookies |
| US-1.7 | Banner de Cookies | S | Banner de consentimiento RGPD con aceptar/rechazar |
| US-1.8 | Páginas de Error | S | 404 y 500 personalizadas con navegación |
| US-1.9 | SEO Básico | S | robots.txt, sitemap.xml, Open Graph tags |

---

## EPIC 2: Gestión de Leads

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-2.1 | Modelo Lead | M | Campos: nombre, email, teléfono, mensaje, servicio, urgencia, estado |
| US-2.2 | Modelo LeadImage | M | Hasta 5 imágenes por lead, validación magic bytes, máx 5MB |
| US-2.3 | Modelo LeadLog | M | Auditoría automática de cambios vía signals |
| US-2.4 | Admin de Leads | M | Badges de estado, filtros, búsqueda, inlines para imágenes/presupuestos |
| US-2.5 | Exportar a CSV | S | Acción en admin para exportar leads seleccionados |

---

## EPIC 3: Presupuestos

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-3.1 | Modelo Budget | M | Referencia automática ARYN-YYYY-NNN, monto, estado, fecha validez |
| US-3.2 | Admin de Presupuestos | M | CRUD completo, badges de estado, adjuntar PDF |

---

## EPIC 4: Usuarios y Permisos

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-4.1 | Modelo UserProfile | M | Extensión de User con rol y teléfono |
| US-4.2 | Grupos y Permisos | M | Roles: admin (todo), office (gestión), field (lectura asignados) |
| US-4.3 | Restricción Leads por Técnico | S | Técnicos de campo solo ven leads asignados a ellos |

---

## EPIC 5: Notificaciones

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-5.1 | Notificación Nuevo Lead | M | Email a admin cuando llega lead + confirmación a cliente |
| US-5.2 | Notificación Lead Asignado | S | Email al técnico cuando se le asigna un lead |
| US-5.3 | Notificación Nota Añadida | C | Email a admins cuando técnico añade nota a lead |

---

## EPIC 6: Catálogo de Servicios

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-6.1 | Modelo Service | C | Nombre, descripción, icono, orden, activo |
| US-6.2 | Servicios Dinámicos | C | Página de servicios lee de la BD en vez de hardcoded |

---

## EPIC 7: Seguridad

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-7.1 | Protección Formulario | M | CSRF, honeypot, rate limiting, validación magic bytes |
| US-7.2 | Headers de Seguridad | M | SSL, HSTS, CSP, X-Frame-Options, X-Content-Type |
| US-7.3 | URL Admin Personalizada | S | Admin en /admynstal/ en vez de /admin/ |

---

## EPIC 8: Infraestructura

| ID | User Story | Prioridad | Criterios de Aceptación |
|----|------------|-----------|-------------------------|
| US-8.1 | Variables de Entorno | M | .env para secrets, .env.example documentado |
| US-8.2 | Separación de Settings | M | base.py, development.py, production.py |
| US-8.3 | Sistema de Backups | S | Script documentado para backup de BD y media |
| US-8.4 | Health Check | S | Endpoint /health/ que verifica BD |

---

## Resumen por Prioridad

| Prioridad | Total | Descripción |
|-----------|-------|-------------|
| Must Have | 14 | Funcionalidades imprescindibles para MVP |
| Should Have | 9 | Importantes para completar el producto |
| Could Have | 3 | Deseables si hay tiempo |

---

*Documento creado: Enero 2026*
*Proyecto: Arynstal CRM*
