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

- **LCP critico** en About (13.2s), Projects (15.9s), Contact (11.2s) — imagenes sin optimizar
- **Accesibilidad** — sin `<main>`, sin `aria-label` en botones, touch targets < 48px
- **SEO** — Contact con `<meta name="message">` en vez de `description`
- **JS** — console.log de debug en produccion

---

## Auditoria #2 — 13 febrero 2026 (Post-optimizacion)

**Cambios aplicados entre auditorias #1 y #2:**
- Imagenes convertidas a WebP (6.8MB → 262KB, reduccion 97%)
- Anadido `width`/`height` a todas las imagenes (elimina CLS)
- Anadido `loading="lazy"` a imagenes below-the-fold
- Anadido `<main>` landmark en index, services, projects
- Anadido `aria-label` en botones de carousel, modal y filtros
- Corregido `<meta name="description">` en contact.html
- Anadido `<h1>` en index.html, corregido jerarquia headings en projects
- Eliminados console.log/warn del JS compilado (rebuild Vite)
- Touch targets de iconos sociales: w-8 → w-11

### Resultados por pagina

| Pagina | Performance | Accessibility | Best Practices | SEO |
|--------|:-----------:|:-------------:|:--------------:|:---:|
| Home | 84 | 95 | 96 | 100 |
| Services | 100 | 95 | 96 | 100 |
| About | 93 | 95 | 96 | 100 |
| Projects | 84 | 95 | 96 | 100 |
| Contact | 100 | 96 | 96 | 100 |
| **Media** | **92** | **95** | **96** | **100** |

### Core Web Vitals

| Pagina | FCP | LCP | TBT | CLS | SI |
|--------|-----|-----|-----|-----|-----|
| Home | 1.3s | 4.5s | 0ms | 0 | 1.3s |
| Services | 1.0s | 1.2s | 0ms | 0 | 1.2s |
| About | 1.1s | 3.2s | 0ms | 0 | 1.2s |
| Projects | 1.1s | 4.6s | 0ms | 0 | 1.2s |
| Contact | 0.9s | 1.5s | 0ms | 0 | 0.9s |

### Comparativa #1 vs #2

| Metrica | Audit #1 | Audit #2 | Cambio |
|---------|:--------:|:--------:|:------:|
| Performance (media) | 83 | 92 | **+9** |
| Accessibility (media) | 92 | 95 | **+3** |
| Best Practices (media) | 96 | 96 | = |
| SEO (media) | 98 | 100 | **+2** |

**Mejoras destacadas:**
- Contact Performance: 69 → 100 (+31) — WebP + meta fix
- About Performance: 75 → 93 (+18) — LCP de 13.2s a 3.2s
- Projects CLS: 0.027 → 0 — width/height en imagenes
- TBT: todos a 0ms (antes hasta 300ms en Contact)
- SEO: 100 en todas las paginas

### Problemas pendientes

#### LCP en Home (4.5s) y Projects (4.6s)

Las imagenes del carousel (Home) y cards de proyectos siguen por encima de 2.5s. Posibles acciones futuras:
- Preload de la primera imagen del carousel via `<link rel="preload">`
- Reducir tamano de imagenes de proyectos o usar thumbnails
- Implementar responsive images con `srcset`

#### Touch targets (Accessibility)

Los dots del carousel (`w-3 h-3` = 12px) y los links del footer no alcanzan 48px.
- Dots: ampliar area clickable con padding o min-w/min-h
- Footer links: anadir padding vertical

---

## Historial de Revisiones

| Version | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-02-12 | Primera auditoria en produccion |
| 1.1 | 2026-02-13 | Auditoria #2 post-optimizacion imagenes, a11y y SEO |
