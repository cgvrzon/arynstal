# Arynstal — Corporate Website & Lead Management System

[![CI](https://github.com/cgvrzon/arynstal/actions/workflows/ci.yml/badge.svg)](https://github.com/cgvrzon/arynstal/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-092E20.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-06B6D4.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Full-stack web application built for **Arynstal SL**, a family-owned HVAC and home automation installation company based in Barcelona. Designed, developed, deployed, and maintained as the **sole developer** — covering the entire software lifecycle from requirements gathering to production monitoring.

> **Live:** [arynstal.es](https://arynstal.es) — Currently behind basic authentication as the project is in its final pre-launch phase.

---

## Key Metrics

| Metric | Result |
|--------|--------|
| Lighthouse Performance | **92** |
| Lighthouse Accessibility | **95** |
| Lighthouse SEO | **100** |
| Automated Tests | **101** (pytest) |
| CI/CD | Fully automated (GitHub Actions) |
| Uptime Monitoring | Sentry (EU region) |

---

## Features

**Public Website**
- Responsive corporate site with service catalog, project gallery, and contact form
- SEO-optimized with semantic HTML5 and structured metadata
- Multi-layer contact form security: CSRF, honeypot, rate limiting (5 req/min per IP), and server-side validation

**Lead Management (CRM)**
- Full lead lifecycle: capture, qualification, budgeting, and follow-up
- Role-based access control (Admin, Office, Field Technician)
- Complete audit trail — every status change and action is logged
- Automated email notifications for both admin and clients (via Brevo, DKIM/DMARC authenticated)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6.0, Python 3.12 |
| Frontend | HTML5, Tailwind CSS, JavaScript ES6+, Vite |
| Database | PostgreSQL (production), SQLite (development) |
| Server | Nginx (reverse proxy), Gunicorn (WSGI) |
| SSL | Let's Encrypt + Cloudflare Full (Strict) |
| CI/CD | GitHub Actions — automated testing and deployment |
| Monitoring | Sentry (error tracking), custom disk alerts |
| Email | Brevo (transactional), Zoho Mail (domain) |
| Security | Cloudflare WAF, rate limiting, HSTS, CSP headers |

---

## Architecture

```
Client (Browser)
    |
Cloudflare (DNS, WAF, SSL, Caching)
    |
Nginx (reverse proxy, rate limiting, static files)
    |
Gunicorn (3 workers, WSGI)
    |
Django 6.0 (application layer)
    |
PostgreSQL (data persistence)
```

### Project Structure

```
arynstal/
├── apps/
│   ├── leads/        # Lead model, Budget, LeadLog, signals, notifications
│   ├── services/     # Service catalog
│   ├── users/        # UserProfile with role-based permissions
│   └── web/          # Public views, contact form
├── arynstal/
│   └── settings/     # Split config: base / development / production
├── templates/        # Django templates (pages, components, emails, legal)
├── static/           # Compiled CSS/JS, images (WebP optimized)
├── docs/             # Technical documentation
└── requirements/     # Dependencies per environment
```

---

## Infrastructure & DevOps

- **Server:** Hardened Linux VPS — root SSH disabled, custom port, firewall configured
- **SSL:** Let's Encrypt certificates with automatic renewal, Cloudflare Full (Strict) mode
- **CI/CD:** GitHub Actions pipeline — runs tests on every push, auto-deploys to production on main
- **Backups:** Automated daily PostgreSQL dumps with 7-day rotation
- **Log Management:** Custom logrotate configuration for Nginx, Gunicorn, and backup logs
- **Disk Monitoring:** Tiered alert system (50/65/75/80% thresholds) via cron

---

## Security

- CSRF protection on all forms
- Rate limiting per IP on public endpoints
- Honeypot fields for bot detection
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- File upload validation (magic bytes verification)
- SQL injection prevention (Django ORM)
- XSS prevention (template auto-escaping)
- GDPR/RGPD compliant (privacy policy, cookie consent, data handling)
- Cloudflare WAF with custom rules

---

## Testing

101 automated tests covering models, views, forms, signals, and security:

```bash
pytest                              # Run all tests
pytest --cov=apps --cov-report=html # With coverage report
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [DEPLOY_GUIDE.md](docs/DEPLOY_GUIDE.md) | Step-by-step production deployment guide |
| [INFRAESTRUCTURA.md](docs/INFRAESTRUCTURA.md) | Infrastructure analysis and architectural decisions |
| [PRODUCT_BACKLOG.md](docs/PRODUCT_BACKLOG.md) | Original requirements (EPICs and user stories) |
| [AUDITORIAS_LIGHTHOUSE.md](docs/AUDITORIAS_LIGHTHOUSE.md) | Lighthouse audit history and improvements |

---

## Local Development

```bash
git clone https://github.com/cgvrzon/arynstal.git
cd arynstal
python -m venv venv && source venv/bin/activate
pip install -r requirements/development.txt
cp .env.example .env          # Configure your environment variables
python manage.py migrate
python manage.py seed_database # Populate with sample data
python manage.py runserver
```

---

## License

MIT — See [LICENSE](LICENSE) for details.

## Author

**Carlos Garzon Lopez** — [@cgvrzon](https://github.com/cgvrzon)
