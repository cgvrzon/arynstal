# HISTORIAL DE AUDITORÍAS LIGHTHOUSE - ARYNSTAL

Este documento registra las auditorías de rendimiento realizadas con Google Lighthouse
para monitorizar la evolución del sitio web.

---

## Índice

1. [Auditoría #1 - 22 Enero 2026](#auditoría-1---22-enero-2026)

---

## Auditoría #1 - 22 Enero 2026

**Fecha**: 22 de Enero de 2026
**Hora**: 15:10 - 15:17
**Entorno**: Desarrollo local (Django runserver)
**Herramienta**: Lighthouse CLI v12.6.0
**Navegador**: Chromium (snap)

### Configuración de la auditoría
```bash
export CHROME_PATH=/snap/bin/chromium
lighthouse http://127.0.0.1:8000/[page]/ \
  --output=html,json \
  --output-path=./audits/lighthouse-[page]-$(date +%Y%m%d-%H%M%S).report \
  --chrome-flags="--headless --no-sandbox --disable-gpu"
```

---

## Resultados por Página

### 1. Homepage (/)

**URL**: `http://127.0.0.1:8000/`

| Categoría | Puntuación | Estado |
|-----------|------------|--------|
| Performance | 75/100 | 🟡 |
| Accessibility | 81/100 | 🟡 |
| Best Practices | 96/100 | 🟢 |
| SEO | 100/100 | 🟢 |

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| FCP | 1.4s | < 1.8s | 🟢 |
| LCP | 27.6s | < 2.5s | 🔴 |

**Archivos**: `audits/lighthouse-home-20260122-151007.report.*`

---

### 2. Contacto (/contact/)

**URL**: `http://127.0.0.1:8000/contact/`

| Categoría | Puntuación | Estado |
|-----------|------------|--------|
| Performance | 75/100 | 🟡 |
| Accessibility | 100/100 | 🟢 |
| Best Practices | 96/100 | 🟢 |
| SEO | 92/100 | 🟢 |

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| FCP | 1.4s | < 1.8s | 🟢 |
| LCP | 11.7s | < 2.5s | 🔴 |

**Archivos**: `audits/lighthouse-contact-20260122-151234.report.*`

---

### 3. Servicios (/services/)

**URL**: `http://127.0.0.1:8000/services/`

| Categoría | Puntuación | Estado |
|-----------|------------|--------|
| Performance | 75/100 | 🟡 |
| Accessibility | 98/100 | 🟢 |
| Best Practices | 96/100 | 🟢 |
| SEO | 100/100 | 🟢 |

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| FCP | 1.2s | < 1.8s | 🟢 |
| LCP | 11.3s | < 2.5s | 🔴 |

**Archivos**: `audits/lighthouse-services-20260122-151343.report.*`

---

### 4. Sobre Nosotros (/about-us/)

**URL**: `http://127.0.0.1:8000/about-us/`

| Categoría | Puntuación | Estado |
|-----------|------------|--------|
| Performance | 75/100 | 🟡 |
| Accessibility | 100/100 | 🟢 |
| Best Practices | 96/100 | 🟢 |
| SEO | 100/100 | 🟢 |

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| FCP | 1.4s | < 1.8s | 🟢 |
| LCP | 13.5s | < 2.5s | 🔴 |

**Archivos**: `audits/lighthouse-about-20260122-151514.report.*`

---

### 5. Proyectos (/projects/)

**URL**: `http://127.0.0.1:8000/projects/`

| Categoría | Puntuación | Estado |
|-----------|------------|--------|
| Performance | 75/100 | 🟡 |
| Accessibility | 95/100 | 🟢 |
| Best Practices | 96/100 | 🟢 |
| SEO | 100/100 | 🟢 |

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| FCP | 1.4s | < 1.8s | 🟢 |
| LCP | 16.5s | < 2.5s | 🔴 |

**Archivos**: `audits/lighthouse-projects-20260122-151618.report.*`

---

## Resumen General

### Tabla Comparativa

| Página | Perf | A11y | BP | SEO | LCP | FCP |
|--------|------|------|-----|-----|-----|-----|
| Homepage | 75 🟡 | 81 🟡 | 96 🟢 | 100 🟢 | 27.6s 🔴 | 1.4s 🟢 |
| Contact | 75 🟡 | 100 🟢 | 96 🟢 | 92 🟢 | 11.7s 🔴 | 1.4s 🟢 |
| Services | 75 🟡 | 98 🟢 | 96 🟢 | 100 🟢 | 11.3s 🔴 | 1.2s 🟢 |
| About-us | 75 🟡 | 100 🟢 | 96 🟢 | 100 🟢 | 13.5s 🔴 | 1.4s 🟢 |
| Projects | 75 🟡 | 95 🟢 | 96 🟢 | 100 🟢 | 16.5s 🔴 | 1.4s 🟢 |

### Promedios

| Categoría | Promedio |
|-----------|----------|
| Performance | 75/100 🟡 |
| Accessibility | 95/100 🟢 |
| Best Practices | 96/100 🟢 |
| SEO | 98/100 🟢 |

---

## Análisis de Problemas

### 🔴 CRÍTICO: LCP elevado en todas las páginas

**Valores actuales**: 11.3s - 27.6s
**Objetivo**: < 2.5s

**Causa probable**:
El servidor de desarrollo de Django (`python manage.py runserver`) no está optimizado
para rendimiento. Es un servidor single-threaded diseñado solo para desarrollo.

**Factores que afectan en desarrollo**:
- Sin compresión gzip/brotli
- Sin caché de assets estáticos
- Sin optimización de imágenes
- Sin CDN
- Servidor single-threaded

**Expectativa en producción**:
Con Gunicorn + Nginx + Cloudflare, el LCP debería mejorar significativamente:
- Compresión automática (Cloudflare)
- Caché de assets estáticos (Nginx + Cloudflare)
- Múltiples workers (Gunicorn)
- CDN global (Cloudflare)

### 🟡 Homepage: Accessibility 81/100

La homepage tiene menor puntuación de accesibilidad que el resto de páginas.

**Posibles causas**:
- Contraste de colores insuficiente
- Imágenes sin alt text adecuado
- Falta de ARIA labels en elementos interactivos

**Acción**: Revisar el informe HTML detallado para identificar problemas específicos.

### 🟡 Contact: SEO 92/100

La página de contacto tiene menor SEO que el resto.

**Posibles causas**:
- Meta description podría mejorarse
- Heading structure podría optimizarse

---

## Recomendaciones

### Pre-Despliegue (Prioridad Alta)

1. **Revisar Homepage Accessibility**
   - Abrir `audits/lighthouse-home-*.report.html`
   - Corregir issues de contraste y alt text
   - Objetivo: ≥ 90/100

2. **Verificar imágenes**
   - Confirmar que todas tienen alt text
   - Verificar tamaños y formatos

### Post-Despliegue (Re-auditar)

1. **Re-ejecutar auditoría completa en producción**
   - Esperar mejora significativa en LCP (objetivo < 2.5s)
   - Performance debería subir a ≥ 90/100

2. **Configurar monitoreo continuo**
   - Lighthouse CI en GitHub Actions
   - Alertas si métricas bajan

---

## Archivos Generados

```
audits/
├── lighthouse-home-20260122-151007.report.html
├── lighthouse-home-20260122-151007.report.json
├── lighthouse-contact-20260122-151234.report.report.html
├── lighthouse-contact-20260122-151234.report.report.json
├── lighthouse-services-20260122-151343.report.report.html
├── lighthouse-services-20260122-151343.report.report.json
├── lighthouse-about-20260122-151514.report.report.html
├── lighthouse-about-20260122-151514.report.report.json
├── lighthouse-projects-20260122-151618.report.report.html
└── lighthouse-projects-20260122-151618.report.report.json
```

---

## Historial de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 22/01/2026 | 1.0 | Auditoría inicial completa (5 páginas) |

---

## Próxima Auditoría Programada

**Cuándo**: Después del despliegue en producción
**Objetivo**: Verificar mejora en LCP y Performance general
**Páginas a auditar**: Todas las anteriores + páginas legales
