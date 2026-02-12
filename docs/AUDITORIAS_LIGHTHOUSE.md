# ARYNSTAL - Auditorias Lighthouse

> Registro de auditorias de rendimiento y calidad web.
>
> Herramienta: Lighthouse CLI 13.0.1 (Chromium headless)

---

## Auditoria #1 — 12 febrero 2026 (Produccion)

**Entorno:** Servidor Hetzner CX22, Cloudflare CDN, Django 6.0
**Ejecutado desde:** WSL2 (Barcelona) contra https://arynstal.es

### Resultados por pagina

| Pagina | Performance | Accessibility | Best Practices | SEO |
|--------|:-----------:|:-------------:|:--------------:|:---:|
| Home | 95 | 85 | 96 | 100 |
| Services | 100 | 92 | 96 | 100 |
| About | 75 | 95 | 96 | 100 |
| Projects | 75 | 91 | 96 | 100 |
| Contact | 69 | 96 | 96 | 92 |
| **Media** | **83** | **92** | **96** | **98** |

### Core Web Vitals

| Pagina | FCP | LCP | TBT | CLS | SI |
|--------|-----|-----|-----|-----|-----|
| Home | 1.1s | 2.9s | 20ms | 0 | 1.1s |
| Services | 1.0s | 1.0s | 0ms | 0 | 1.1s |
| About | 0.9s | 13.2s | 0ms | 0 | 1.0s |
| Projects | 1.1s | 15.9s | 50ms | 0.027 | 1.3s |
| Contact | 1.1s | 11.2s | 300ms | 0 | 1.2s |

**Objetivo LCP:** < 2.5s. Solo Home y Services cumplen.

### Problemas detectados

#### Critico — LCP alto (About, Projects, Contact)

Las paginas About (13.2s), Projects (15.9s) y Contact (11.2s) tienen un LCP muy por encima del objetivo de 2.5s. Causa probable: imagenes grandes sin optimizar y sin lazy loading adecuado.

**Acciones:**
- [ ] Optimizar imagenes (WebP, compresion, tamanios adecuados)
- [ ] Revisar LCP element en cada pagina y priorizar su carga
- [ ] Anadir `width` y `height` explicitos a todas las imagenes

#### Importante — Accesibilidad (Home 85/100)

- Botones sin nombre accesible (`aria-label` faltante)
- Sin landmark `<main>` en el documento
- Touch targets demasiado pequenos en movil (Services, About, Contact)

**Acciones:**
- [ ] Anadir `<main>` como landmark principal en cada pagina
- [ ] Anadir `aria-label` a botones interactivos (slider, modal, menu)
- [ ] Revisar tamano de botones/links en movil (minimo 48x48px)

#### Menor — SEO (Contact 92/100)

Contact no llega a 100 en SEO. Revisar meta tags y estructura.

**Acciones:**
- [ ] Revisar meta description y title en contact.html
- [ ] Verificar orden de headings (h1 > h2 > h3 secuencial)

#### Menor — Best Practices

- Errores de consola en todas las paginas (probablemente JS)
- Cache headers pueden mejorarse para estaticos

**Acciones:**
- [ ] Investigar errores de consola del navegador
- [ ] Revisar cache lifetimes en Nginx/Cloudflare

### Comparativa con auditoria en desarrollo (enero 2026)

| Metrica | Desarrollo | Produccion | Cambio |
|---------|:----------:|:----------:|:------:|
| Performance (media) | 75 | 83 | +8 |
| Accessibility (media) | 95 | 92 | -3 |
| Best Practices (media) | 96 | 96 | = |
| SEO (media) | 98 | 98 | = |
| FCP (home) | 11.3s | 1.1s | -10.2s |

**Mejora notable** en FCP gracias a Cloudflare CDN y servidor de produccion real (vs runserver de desarrollo). Performance global sube 8 puntos. Accesibilidad baja ligeramente por cambios recientes en UI.

---

## Historial de Revisiones

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-02-12 | Primera auditoria en produccion |
