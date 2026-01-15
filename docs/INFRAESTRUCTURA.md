# ARYNSTAL - Documento de Infraestructura y Despliegue

> Análisis técnico, decisiones de arquitectura y estrategia de escalabilidad.
>
> Última actualización: Enero 2026

---

## 1. Resumen Ejecutivo

### 1.1 Contexto del Proyecto

| Aspecto | Descripción |
|---------|-------------|
| **Negocio** | Empresa familiar de instalaciones (aerotermia, AC, domótica) |
| **Ubicación** | Barcelona y alrededores (radio 1-1.5h) |
| **Equipo** | 4 personas: 1 administrativa, 2 técnicos, 1 responsable técnico |
| **Volumen esperado** | 5-10 leads/mes en fase inicial |
| **Presupuesto** | 70-150€/año para infraestructura |

### 1.2 Requisitos Técnicos

| Requisito | Especificación |
|-----------|----------------|
| **Framework** | Django 6.0 (Python 3.12) |
| **Base de datos** | PostgreSQL 16 |
| **Servidor web** | Nginx + Gunicorn |
| **SSL** | Obligatorio (HTTPS) |
| **Email** | SMTP para notificaciones |
| **Almacenamiento** | Archivos estáticos + media (imágenes de leads) |
| **Backups** | Diarios, retención 7 días mínimo |

### 1.3 Decisión Final

```
┌─────────────────────────────────────────────────────────────────┐
│  STACK DE PRODUCCIÓN SELECCIONADO                               │
├─────────────────────────────────────────────────────────────────┤
│  Hosting:      Hetzner Cloud CX22 (Falkenstein, Alemania)       │
│  Sistema:      Ubuntu 24.04 LTS                                 │
│  DNS/CDN:      Cloudflare (plan gratuito)                       │
│  SSL:          Let's Encrypt (Certbot)                          │
│  Email:        Brevo SMTP (tier gratuito)                       │
│  Dominio:      Registrador a elegir (.es)                       │
│  Backups:      Script local + almacenamiento externo            │
│                                                                 │
│  Coste estimado: ~70€/año                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Análisis de Opciones de Hosting

### 2.1 Categorías Evaluadas

Se evaluaron tres categorías de hosting:

1. **VPS (Virtual Private Server)** - Servidor virtual con control total
2. **PaaS (Platform as a Service)** - Plataforma gestionada
3. **Shared Hosting** - Hosting compartido (descartado por limitaciones)

### 2.2 Comparativa VPS

| Proveedor | Plan | vCPU | RAM | SSD | Precio/mes | Precio/año | Datacenter EU | Nota |
|-----------|------|------|-----|-----|------------|------------|---------------|------|
| **Hetzner** | CX22 | 2 | 4 GB | 40 GB | 3.99€ | 47.88€ | ✅ Alemania | ⭐ Recomendado |
| **Hetzner** | CX32 | 4 | 8 GB | 80 GB | 7.49€ | 89.88€ | ✅ Alemania | Escalado |
| DigitalOcean | Basic | 1 | 1 GB | 25 GB | 6$ | 72$ | ✅ Frankfurt | Más caro |
| DigitalOcean | Basic | 1 | 2 GB | 50 GB | 12$ | 144$ | ✅ Frankfurt | |
| Contabo | VPS S | 4 | 8 GB | 50 GB | 4.99€ | 59.88€ | ✅ Alemania | Soporte lento |
| OVH | Starter | 1 | 2 GB | 20 GB | 4€ | 48€ | ✅ España | Panel confuso |
| Vultr | Regular | 1 | 1 GB | 25 GB | 6$ | 72$ | ✅ Amsterdam | |
| Linode | Nanode | 1 | 1 GB | 25 GB | 5$ | 60$ | ✅ Frankfurt | |

### 2.3 Comparativa PaaS

| Proveedor | Modelo | Precio base | PostgreSQL | Pros | Contras |
|-----------|--------|-------------|------------|------|---------|
| Railway | Por uso | ~5$/mes | Incluido | Deploy fácil | Costes variables |
| Render | Fijo | 7$/mes | +7$/mes | Similar a Heroku | BD cara |
| Fly.io | Por uso | ~3-5$/mes | +5$/mes | Edge computing | Complejo |
| PythonAnywhere | Fijo | 5$/mes | Incluido | Específico Python | Limitado |
| Heroku | Fijo | 7$/mes | +5$/mes | Muy fácil | Caro para lo que ofrece |

### 2.4 Justificación de la Decisión

**¿Por qué Hetzner CX22?**

1. **Precio imbatible**: 3.99€/mes por 2 vCPU y 4GB RAM
2. **Datacenter en Europa**: Cumplimiento RGPD, baja latencia para España
3. **Recursos suficientes**: Para el volumen esperado, sobra capacidad
4. **Escalabilidad clara**: Upgrade a CX32/CX42 sin migración
5. **Control total**: Podemos optimizar según necesidades
6. **Reputación**: Empresa alemana establecida, buen soporte

**¿Por qué no PaaS?**

- Para un proyecto de bajo tráfico, el VPS es más económico a largo plazo
- Mayor control sobre la configuración
- Sin límites artificiales de plataforma
- Aprendizaje valioso para el equipo técnico

**¿Por qué no otros VPS?**

- DigitalOcean: 50% más caro por menos recursos
- Contabo: Soporte deficiente, problemas de red reportados
- OVH: Panel de control confuso, experiencia de usuario pobre

---

## 3. Arquitectura de Producción

### 3.1 Diagrama de Arquitectura

```
                              INTERNET
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │      CLOUDFLARE         │
                    │  ─────────────────────  │
                    │  • DNS                  │
                    │  • CDN (caché estáticos)│
                    │  • SSL/TLS termination  │
                    │  • DDoS protection      │
                    │  • WAF básico           │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │    HETZNER VPS (CX22)   │
                    │    Ubuntu 24.04 LTS     │
                    │  ─────────────────────  │
                    │                         │
                    │  ┌───────────────────┐  │
                    │  │      NGINX        │  │
                    │  │  (reverse proxy)  │  │
                    │  │  Puerto 80/443    │  │
                    │  └─────────┬─────────┘  │
                    │            │            │
                    │            ▼            │
                    │  ┌───────────────────┐  │
                    │  │     GUNICORN      │  │
                    │  │   (WSGI server)   │  │
                    │  │  Unix socket      │  │
                    │  └─────────┬─────────┘  │
                    │            │            │
                    │            ▼            │
                    │  ┌───────────────────┐  │
                    │  │      DJANGO       │  │
                    │  │   (aplicación)    │  │
                    │  └─────────┬─────────┘  │
                    │            │            │
                    │            ▼            │
                    │  ┌───────────────────┐  │
                    │  │   POSTGRESQL 16   │  │
                    │  │  (base de datos)  │  │
                    │  └───────────────────┘  │
                    │                         │
                    │  /var/www/arynstal/     │
                    │  ├── static/            │
                    │  └── media/             │
                    │                         │
                    └─────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │   BREVO SMTP    │ │   BACKUPS   │ │   MONITORING    │
    │  (email salida) │ │  (externo)  │ │   (opcional)    │
    └─────────────────┘ └─────────────┘ └─────────────────┘
```

### 3.2 Estructura de Directorios en Servidor

```
/var/www/arynstal/
├── venv/                    # Entorno virtual Python
├── arynstal/                # Código de la aplicación
│   ├── apps/
│   ├── arynstal/
│   ├── templates/
│   ├── static/              # Archivos fuente
│   └── manage.py
├── staticfiles/             # Archivos estáticos recolectados
├── media/                   # Archivos subidos por usuarios
├── logs/                    # Logs de la aplicación
│   ├── gunicorn.log
│   ├── django.log
│   └── nginx-access.log
├── backups/                 # Backups locales temporales
├── .env                     # Variables de entorno
└── gunicorn.conf.py         # Configuración Gunicorn
```

### 3.3 Servicios del Sistema

| Servicio | Puerto | Función | Gestión |
|----------|--------|---------|---------|
| Nginx | 80, 443 | Proxy reverso, SSL, estáticos | systemd |
| Gunicorn | socket | Servidor WSGI | systemd |
| PostgreSQL | 5432 (local) | Base de datos | systemd |
| UFW | - | Firewall | ufw |
| Certbot | - | Renovación SSL | cron/timer |
| Backup | - | Backup diario | cron |

### 3.4 Seguridad

#### Firewall (UFW)
```
22/tcp     ALLOW   # SSH (considerar cambiar puerto)
80/tcp     ALLOW   # HTTP (redirige a HTTPS)
443/tcp    ALLOW   # HTTPS
```

#### Headers de Seguridad (Nginx + Django)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy` (básico)

#### Acceso SSH
- Autenticación por clave pública (sin contraseña)
- Fail2ban para protección contra fuerza bruta
- Usuario no-root para la aplicación

---

## 4. Servicios Externos

### 4.1 Cloudflare (DNS + CDN)

**Plan**: Gratuito

**Configuración**:
- Proxy habilitado para el dominio principal
- SSL/TLS: Full (strict)
- Caché de archivos estáticos
- Reglas de página para excluir `/gestion-interna/` del caché

**Beneficios**:
- SSL gestionado automáticamente
- Protección DDoS básica
- CDN global (mejora velocidad)
- Analytics de tráfico

### 4.2 Brevo (Email Transaccional)

**Plan**: Gratuito (300 emails/día)

**Uso previsto**:
- Notificaciones de nuevos leads (~10/mes)
- Confirmaciones a clientes (~10/mes)
- Total: <50 emails/mes (muy por debajo del límite)

**Configuración**:
```
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = '<tu-email>'
EMAIL_HOST_PASSWORD = '<api-key>'
```

### 4.3 Dominio

**Opciones recomendadas para .es**:

| Registrador | Precio/año | Notas |
|-------------|------------|-------|
| Dondominio | 8.95€ | Español, buen soporte |
| Porkbun | ~9€ | Barato, interfaz limpia |
| Namecheap | ~10€ | Popular, fiable |
| Cloudflare | ~9€ | Integrado con DNS |

---

## 5. Estrategia de Escalabilidad

### 5.1 Escenarios de Crecimiento

| Fase | Tráfico | Leads/mes | Infraestructura |
|------|---------|-----------|-----------------|
| **Actual** | Bajo | 5-10 | CX22 (4GB RAM) |
| **Crecimiento** | Medio | 50-100 | CX32 (8GB RAM) |
| **Expansión** | Alto | 500+ | Arquitectura distribuida |

### 5.2 Escalado Vertical (Fase 1-2)

El primer paso de escalado es simplemente aumentar los recursos del VPS:

```
CX22 (actual)  →  CX32  →  CX42  →  CX52
4GB RAM           8GB      16GB     32GB
2 vCPU            4        8        16
3.99€/mes         7.49€    14.99€   29.99€
```

**Proceso**: Apagar VPS → Cambiar plan → Reiniciar (~5 min downtime)

### 5.3 Escalado Horizontal (Fase 3+)

Si el negocio crece significativamente:

```
                         ┌─────────────────┐
                         │   CLOUDFLARE    │
                         │   Load Balancer │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌─────────┐   ┌─────────┐   ┌─────────┐
              │  App 1  │   │  App 2  │   │  App 3  │
              │ Django  │   │ Django  │   │ Django  │
              └────┬────┘   └────┬────┘   └────┬────┘
                   │             │             │
                   └─────────────┼─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   PostgreSQL Managed    │
                    │   (Hetzner o externo)   │
                    └─────────────────────────┘
```

**Componentes para escalar horizontalmente**:
1. **Load Balancer**: Cloudflare o HAProxy
2. **Base de datos gestionada**: Hetzner Managed PostgreSQL o Amazon RDS
3. **Almacenamiento de media**: Cloudflare R2 o Amazon S3
4. **Caché**: Redis para sesiones y caché de queries
5. **Cola de tareas**: Celery + Redis para emails asíncronos

### 5.4 Optimizaciones Antes de Escalar

Antes de añadir servidores, optimizar:

| Área | Optimización | Impacto |
|------|--------------|---------|
| **BD** | Índices en campos frecuentes | Alto |
| **BD** | Connection pooling (pgBouncer) | Medio |
| **Caché** | Django cache framework + Redis | Alto |
| **Queries** | select_related/prefetch_related | Alto |
| **Estáticos** | CDN agresivo (Cloudflare) | Medio |
| **Imágenes** | Compresión automática | Bajo |

### 5.5 Indicadores para Escalar

| Métrica | Umbral de alerta | Acción |
|---------|------------------|--------|
| CPU sostenido | >70% | Upgrade VPS |
| RAM usada | >80% | Upgrade VPS |
| Tiempo respuesta | >2s | Optimizar/Upgrade |
| Disco usado | >80% | Limpiar/Expandir |
| Errores 5xx | >1% | Investigar |

---

## 6. Backups y Recuperación

### 6.1 Estrategia de Backup

| Tipo | Frecuencia | Retención | Contenido |
|------|------------|-----------|-----------|
| **BD completa** | Diaria (3:00 AM) | 7 días | pg_dump completo |
| **BD incremental** | Cada 6 horas | 24 horas | WAL logs |
| **Media** | Semanal | 4 semanas | /media/ |
| **Código** | En cada deploy | Ilimitado | Git (GitHub/GitLab) |

### 6.2 Ubicaciones de Backup

1. **Local**: `/var/backups/arynstal/` (7 días)
2. **Externo**: Backblaze B2 o similar (30 días)

### 6.3 Proceso de Restauración

```bash
# 1. Restaurar BD
pg_restore -d arynstal backup_2026-01-15.dump

# 2. Restaurar media (si es necesario)
rsync -av backup/media/ /var/www/arynstal/media/

# 3. Verificar
python manage.py check
python manage.py migrate --check
```

**RTO (Recovery Time Objective)**: < 1 hora
**RPO (Recovery Point Objective)**: < 6 horas

---

## 7. Monitorización (Opcional)

### 7.1 Opciones Gratuitas

| Herramienta | Función | Coste |
|-------------|---------|-------|
| **Uptime Kuma** | Monitorización uptime | Gratis (self-hosted) |
| **Netdata** | Métricas del servidor | Gratis |
| **Sentry** | Errores de aplicación | Gratis (5k eventos/mes) |
| **GoAccess** | Analytics de logs | Gratis |

### 7.2 Alertas Básicas

Para empezar, configurar alertas de:
- Servidor caído (Uptime Kuma o Cloudflare)
- Certificado SSL próximo a expirar
- Disco >80%
- Errores 500 en Django

---

## 8. Costes Detallados

### 8.1 Coste Anual Estimado

| Concepto | Proveedor | Coste mensual | Coste anual |
|----------|-----------|---------------|-------------|
| VPS CX22 | Hetzner | 3.99€ | 47.88€ |
| Dominio .es | Dondominio | 0.75€ | 8.95€ |
| DNS + CDN | Cloudflare | 0€ | 0€ |
| SSL | Let's Encrypt | 0€ | 0€ |
| Email SMTP | Brevo | 0€ | 0€ |
| Backups | Local + Script | 0€ | 0€ |
| **TOTAL** | | **~4.75€** | **~57€** |

### 8.2 Costes Opcionales

| Concepto | Proveedor | Coste |
|----------|-----------|-------|
| Backup externo | Backblaze B2 | ~1€/mes |
| Monitorización | Uptime Kuma | 0€ (self-hosted) |
| Email profesional | Google Workspace | 6€/usuario/mes |

### 8.3 Proyección de Costes por Crecimiento

| Escenario | VPS | Otros | Total anual |
|-----------|-----|-------|-------------|
| Inicial | CX22 (48€) | 9€ | ~57€ |
| Crecimiento | CX32 (90€) | 20€ | ~110€ |
| Expansión | CX42 x2 (360€) | 100€ | ~460€ |

---

## 9. Checklist Pre-Despliegue

### 9.1 Código y Configuración
- [ ] requirements.txt actualizado
- [ ] .env.example completo
- [ ] DEBUG=False en producción
- [ ] SECRET_KEY único generado
- [ ] ALLOWED_HOSTS configurado
- [ ] Emails de notificación correctos

### 9.2 Seguridad
- [ ] CSRF_COOKIE_SECURE=True
- [ ] SESSION_COOKIE_SECURE=True
- [ ] SECURE_SSL_REDIRECT=True
- [ ] SECURE_HSTS_SECONDS configurado
- [ ] Admin URL ofuscada (/gestion-interna/)

### 9.3 Base de Datos
- [ ] PostgreSQL instalado y configurado
- [ ] Usuario de BD creado (no root)
- [ ] Migraciones aplicadas
- [ ] Backup inicial realizado

### 9.4 Servidor Web
- [ ] Nginx configurado
- [ ] Gunicorn como servicio
- [ ] SSL certificado instalado
- [ ] Firewall configurado

### 9.5 Funcionalidad
- [ ] Páginas públicas cargan correctamente
- [ ] Formulario de contacto funciona
- [ ] Emails de notificación se envían
- [ ] Panel de admin accesible
- [ ] Archivos estáticos se sirven

---

## 10. Conclusiones

### 10.1 Decisión Final Justificada

La arquitectura seleccionada (Hetzner + Cloudflare + Brevo) ofrece:

1. **Coste mínimo**: ~57€/año cumple el objetivo de 70-150€
2. **Rendimiento adecuado**: Sobra capacidad para el volumen esperado
3. **Escalabilidad clara**: Ruta definida para crecer
4. **Control total**: Sin dependencias de plataformas propietarias
5. **Cumplimiento RGPD**: Datos en Europa
6. **Mantenimiento bajo**: Servicios estables y maduros

### 10.2 Próximos Pasos

1. **Inmediato**: Contratar dominio y VPS
2. **Semana 1**: Configurar servidor y desplegar
3. **Semana 2**: Testing y go-live
4. **Mes 1**: Monitorizar y ajustar
5. **Trimestre 1**: Evaluar y optimizar

---

## Historial de Revisiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-01-15 | Documento inicial |

---

*Documento generado como parte del proyecto Arynstal.*
*Para la guía de despliegue paso a paso, ver `DEPLOY_GUIDE.md`*
