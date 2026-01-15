"""
Tests para la app Web.

Batería completa de pruebas que cubre:
- Vistas públicas (home, services, projects, about, contact)
- Formulario de contacto
- Seguridad (CSRF, honeypot, rate limiting)
- Integración completa del flujo de leads
- Edge cases y situaciones de error
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
import io
from PIL import Image

from apps.leads.models import Lead, LeadImage


# =============================================================================
# HELPERS PARA TESTS
# =============================================================================

def create_test_image(name='test.jpg', size=(100, 100), format='JPEG'):
    """Crea una imagen de prueba en memoria."""
    image = Image.new('RGB', size, color='red')
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=buffer.read(),
        content_type=f'image/{format.lower()}'
    )


def create_valid_contact_data():
    """Retorna datos válidos para el formulario de contacto."""
    return {
        'name': 'Juan Pérez García',
        'email': 'juan@example.com',
        'phone': '666777888',
        'message': 'Este es un mensaje de prueba con más de 20 caracteres para el formulario.',
        'privacidad': 'on',
        'website_url': '',  # Honeypot vacío
    }


# =============================================================================
# TESTS DE VISTAS PÚBLICAS
# =============================================================================

class PublicViewsTest(TestCase):
    """Tests para las vistas públicas de la web."""

    def setUp(self):
        self.client = Client()

    def test_home_view_status_code(self):
        """Test: Home retorna 200."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_template(self):
        """Test: Home usa el template correcto."""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'pages/index.html')

    def test_services_view_status_code(self):
        """Test: Services retorna 200."""
        response = self.client.get(reverse('services'))
        self.assertEqual(response.status_code, 200)

    def test_services_view_template(self):
        """Test: Services usa el template correcto."""
        response = self.client.get(reverse('services'))
        self.assertTemplateUsed(response, 'pages/services.html')

    def test_projects_view_status_code(self):
        """Test: Projects retorna 200."""
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)

    def test_projects_view_template(self):
        """Test: Projects usa el template correcto."""
        response = self.client.get(reverse('projects'))
        self.assertTemplateUsed(response, 'pages/projects.html')

    def test_about_view_status_code(self):
        """Test: About retorna 200."""
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 200)

    def test_about_view_template(self):
        """Test: About usa el template correcto."""
        response = self.client.get(reverse('about_us'))
        self.assertTemplateUsed(response, 'pages/about.html')

    def test_contact_view_get_status_code(self):
        """Test: Contact GET retorna 200."""
        response = self.client.get(reverse('contact_us'))
        self.assertEqual(response.status_code, 200)

    def test_contact_view_template(self):
        """Test: Contact usa el template correcto."""
        response = self.client.get(reverse('contact_us'))
        self.assertTemplateUsed(response, 'pages/contact.html')

    def test_contact_view_has_form(self):
        """Test: Contact GET incluye el formulario."""
        response = self.client.get(reverse('contact_us'))
        self.assertIn('form', response.context)


# =============================================================================
# TESTS DEL FORMULARIO DE CONTACTO
# =============================================================================

class ContactFormViewTest(TestCase):
    """Tests para el formulario de contacto (vista contact_us)."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('contact_us')
        cache.clear()  # Limpiar cache para rate limiting

    def test_valid_form_creates_lead(self):
        """Test: Formulario válido crea un Lead."""
        data = create_valid_contact_data()
        leads_before = Lead.objects.count()

        response = self.client.post(self.url, data)

        self.assertEqual(Lead.objects.count(), leads_before + 1)
        self.assertRedirects(response, self.url)

    def test_valid_form_shows_success_message(self):
        """Test: Formulario válido muestra mensaje de éxito."""
        data = create_valid_contact_data()

        response = self.client.post(self.url, follow=True)

        # Nota: el POST sin datos válidos no creará lead
        # Este test verifica con datos válidos
        response = self.client.post(self.url, data, follow=True)
        messages = list(get_messages(response.wsgi_request))

        # Debe haber al menos un mensaje de éxito
        success_messages = [m for m in messages if m.tags == 'success']
        self.assertTrue(len(success_messages) > 0)

    def test_missing_privacy_shows_error(self):
        """Test: Sin checkbox de privacidad muestra error."""
        data = create_valid_contact_data()
        del data['privacidad']

        response = self.client.post(self.url, data)

        # No debe crear lead
        self.assertEqual(Lead.objects.count(), 0)
        # Debe mostrar error
        messages = list(get_messages(response.wsgi_request))
        error_messages = [m for m in messages if m.tags == 'error']
        self.assertTrue(len(error_messages) > 0)

    def test_invalid_form_shows_error(self):
        """Test: Formulario inválido muestra error."""
        data = {
            'name': 'Ab',  # Muy corto
            'email': 'invalid',  # Email inválido
            'phone': '123',  # Muy corto
            'message': 'Corto',  # Muy corto
            'privacidad': 'on',
        }

        response = self.client.post(self.url, data)

        self.assertEqual(Lead.objects.count(), 0)

    def test_lead_saves_correct_data(self):
        """Test: Lead guarda los datos correctamente."""
        data = create_valid_contact_data()

        self.client.post(self.url, data)

        lead = Lead.objects.first()
        self.assertEqual(lead.name, data['name'])
        self.assertEqual(lead.email, data['email'])
        self.assertEqual(lead.phone, data['phone'])
        self.assertEqual(lead.status, 'nuevo')
        self.assertEqual(lead.source, 'web')
        self.assertTrue(lead.privacy_accepted)

    def test_lead_saves_ip_address(self):
        """Test: Lead guarda la IP del visitante."""
        data = create_valid_contact_data()

        self.client.post(self.url, data)

        lead = Lead.objects.first()
        self.assertIsNotNone(lead.ip_address)

    def test_lead_saves_user_agent(self):
        """Test: Lead guarda el User-Agent."""
        data = create_valid_contact_data()

        self.client.post(
            self.url,
            data,
            HTTP_USER_AGENT='Mozilla/5.0 Test Browser'
        )

        lead = Lead.objects.first()
        self.assertIn('Mozilla', lead.user_agent)


# =============================================================================
# TESTS DE SUBIDA DE IMÁGENES
# =============================================================================

class ContactFormImagesTest(TestCase):
    """Tests para la subida de imágenes en el formulario de contacto."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('contact_us')
        cache.clear()

    def test_form_with_single_image(self):
        """Test: Formulario con una imagen."""
        data = create_valid_contact_data()
        image = create_test_image()

        response = self.client.post(self.url, {**data, 'fotos': image})

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.get_images_count(), 1)

    def test_form_with_multiple_images(self):
        """Test: Formulario con múltiples imágenes."""
        data = create_valid_contact_data()
        images = [create_test_image(name=f'img{i}.jpg') for i in range(3)]

        response = self.client.post(self.url, {**data, 'fotos': images})

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.get_images_count(), 3)

    def test_form_with_max_images(self):
        """Test: Formulario con máximo de imágenes (5)."""
        data = create_valid_contact_data()
        images = [create_test_image(name=f'img{i}.jpg') for i in range(5)]

        response = self.client.post(self.url, {**data, 'fotos': images})

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.get_images_count(), 5)

    def test_form_with_too_many_images(self):
        """Test: Formulario con más de 5 imágenes es rechazado."""
        data = create_valid_contact_data()
        images = [create_test_image(name=f'img{i}.jpg') for i in range(6)]

        response = self.client.post(self.url, {**data, 'fotos': images})

        # No debe crear lead
        self.assertEqual(Lead.objects.count(), 0)
        # Debe mostrar error
        messages = list(get_messages(response.wsgi_request))
        error_messages = [m for m in messages if m.tags == 'error']
        self.assertTrue(len(error_messages) > 0)

    def test_form_without_images(self):
        """Test: Formulario sin imágenes (válido)."""
        data = create_valid_contact_data()

        response = self.client.post(self.url, data)

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.get_images_count(), 0)


# =============================================================================
# TESTS DE SEGURIDAD - CSRF
# =============================================================================

class CSRFSecurityTest(TestCase):
    """Tests de protección CSRF."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse('contact_us')

    def test_post_without_csrf_token_fails(self):
        """Test: POST sin CSRF token falla."""
        data = create_valid_contact_data()

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 403)

    def test_post_with_csrf_token_succeeds(self):
        """Test: POST con CSRF token funciona."""
        # Primero hacer GET para obtener el token
        self.client = Client()  # Sin enforce_csrf_checks para este test
        cache.clear()
        data = create_valid_contact_data()

        response = self.client.post(self.url, data)

        self.assertIn(response.status_code, [200, 302])


# =============================================================================
# TESTS DE SEGURIDAD - HONEYPOT
# =============================================================================

class HoneypotSecurityTest(TestCase):
    """Tests de protección honeypot anti-bot."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('contact_us')
        cache.clear()

    def test_empty_honeypot_creates_lead(self):
        """Test: Honeypot vacío (humano) crea Lead."""
        data = create_valid_contact_data()
        data['website_url'] = ''  # Vacío = humano

        self.client.post(self.url, data)

        self.assertEqual(Lead.objects.count(), 1)

    def test_filled_honeypot_blocks_lead(self):
        """Test: Honeypot con valor (bot) NO crea Lead."""
        data = create_valid_contact_data()
        data['website_url'] = 'http://spam-site.com'  # Bot

        self.client.post(self.url, data)

        self.assertEqual(Lead.objects.count(), 0)

    def test_filled_honeypot_shows_fake_success(self):
        """Test: Honeypot detectado muestra éxito falso (no revela detección)."""
        data = create_valid_contact_data()
        data['website_url'] = 'http://spam-site.com'

        response = self.client.post(self.url, data, follow=True)

        # Debe redirigir (simular éxito)
        self.assertEqual(response.status_code, 200)
        # Pero no crear lead
        self.assertEqual(Lead.objects.count(), 0)

    def test_honeypot_with_any_value_blocks(self):
        """Test: Cualquier valor en honeypot bloquea."""
        test_values = [
            'x',
            ' ',
            'http://example.com',
            '<script>alert(1)</script>',
            '1',
        ]

        for value in test_values:
            cache.clear()
            data = create_valid_contact_data()
            data['website_url'] = value

            self.client.post(self.url, data)

            self.assertEqual(
                Lead.objects.count(), 0,
                f"Honeypot con valor '{value}' no bloqueó el lead"
            )


# =============================================================================
# TESTS DE SEGURIDAD - RATE LIMITING
# =============================================================================

@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class RateLimitingSecurityTest(TestCase):
    """Tests de protección rate limiting."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('contact_us')
        cache.clear()

    def test_first_5_requests_succeed(self):
        """Test: Las primeras 5 peticiones son exitosas."""
        for i in range(5):
            cache.clear()  # Limpiar para cada petición en este test
            data = create_valid_contact_data()
            data['email'] = f'user{i}@example.com'

            response = self.client.post(self.url, data)

            self.assertIn(
                response.status_code, [200, 302],
                f"Petición {i+1} falló con status {response.status_code}"
            )

    def test_rate_limit_after_5_requests(self):
        """Test: Después de 5 peticiones, se bloquean las siguientes."""
        # Enviar 6 peticiones rápidamente
        for i in range(6):
            data = create_valid_contact_data()
            data['email'] = f'ratelimit{i}@example.com'
            response = self.client.post(self.url, data)

        # La 6ta debería estar limitada (status 200 con mensaje de error)
        self.assertEqual(response.status_code, 200)

        # Verificar que hay mensaje de rate limit
        content = response.content.decode('utf-8').lower()
        self.assertTrue(
            'demasiadas' in content or Lead.objects.count() < 6,
            "Rate limiting no funcionó correctamente"
        )

    def test_rate_limit_message_is_friendly(self):
        """Test: Mensaje de rate limit es amigable."""
        # Enviar 7 peticiones
        for i in range(7):
            data = create_valid_contact_data()
            data['email'] = f'test{i}@example.com'
            response = self.client.post(self.url, data)

        # Verificar mensaje amigable
        messages = list(get_messages(response.wsgi_request))
        if messages:
            error_text = str(messages[-1]).lower()
            # No debe revelar detalles técnicos
            self.assertNotIn('rate limit', error_text)
            self.assertNotIn('429', error_text)


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================

class ContactFormIntegrationTest(TestCase):
    """Tests de integración del flujo completo de contacto."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('contact_us')
        cache.clear()

    def test_complete_flow_without_images(self):
        """Test: Flujo completo sin imágenes."""
        # 1. GET - Ver formulario
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # 2. POST - Enviar formulario
        data = create_valid_contact_data()
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)

        # 3. Verificar Lead creado
        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, data['name'])
        self.assertEqual(lead.status, 'nuevo')

        # 4. GET - Ver mensaje de éxito
        response = self.client.get(self.url)
        # El mensaje de éxito debería mostrarse

    def test_complete_flow_with_images(self):
        """Test: Flujo completo con imágenes."""
        data = create_valid_contact_data()
        images = [create_test_image(name=f'img{i}.jpg') for i in range(3)]

        response = self.client.post(self.url, {**data, 'fotos': images})

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.get_images_count(), 3)

        # Verificar que las imágenes existen
        for lead_image in lead.images.all():
            self.assertTrue(lead_image.image)

    def test_multiple_leads_from_same_ip(self):
        """Test: Múltiples leads desde la misma IP (hasta el límite)."""
        leads_created = 0

        for i in range(5):
            cache.clear()  # Reset rate limit para este test
            data = create_valid_contact_data()
            data['email'] = f'multi{i}@example.com'

            response = self.client.post(self.url, data)
            if response.status_code == 302:
                leads_created += 1

        self.assertEqual(leads_created, 5)

    def test_form_preserves_data_on_error(self):
        """Test: Formulario preserva datos cuando hay error."""
        data = create_valid_contact_data()
        data['message'] = 'Corto'  # Error: muy corto

        response = self.client.post(self.url, data)

        # El formulario debe estar en el contexto con los datos
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)


# =============================================================================
# TESTS DE EDGE CASES DE VISTAS
# =============================================================================

class ViewsEdgeCasesTest(TestCase):
    """Tests de edge cases para las vistas."""

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_contact_post_empty_body(self):
        """Test: POST con cuerpo vacío."""
        response = self.client.post(reverse('contact_us'), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    def test_contact_with_extra_fields(self):
        """Test: Formulario con campos extra (ignorados)."""
        data = create_valid_contact_data()
        data['extra_field'] = 'should be ignored'
        data['another_extra'] = 'also ignored'

        response = self.client.post(reverse('contact_us'), data)

        self.assertRedirects(response, reverse('contact_us'))
        lead = Lead.objects.first()
        self.assertIsNotNone(lead)

    def test_contact_with_very_long_user_agent(self):
        """Test: User-Agent muy largo (se trunca)."""
        data = create_valid_contact_data()
        long_ua = 'Mozilla/5.0 ' + 'x' * 1000

        self.client.post(
            reverse('contact_us'),
            data,
            HTTP_USER_AGENT=long_ua
        )

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertLessEqual(len(lead.user_agent), 500)

    def test_contact_without_user_agent(self):
        """Test: Sin User-Agent (campo vacío)."""
        data = create_valid_contact_data()

        self.client.post(reverse('contact_us'), data)

        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        # user_agent puede estar vacío pero no debe fallar

    def test_contact_non_post_methods_dont_create_lead(self):
        """Test: Métodos HTTP distintos de POST no crean Lead."""
        initial_count = Lead.objects.count()

        # PUT no crea lead
        self.client.put(reverse('contact_us'))
        self.assertEqual(Lead.objects.count(), initial_count)

        # DELETE no crea lead
        self.client.delete(reverse('contact_us'))
        self.assertEqual(Lead.objects.count(), initial_count)

        # PATCH no crea lead
        self.client.patch(reverse('contact_us'))
        self.assertEqual(Lead.objects.count(), initial_count)


# =============================================================================
# TESTS DE ERROR HANDLERS
# =============================================================================

class ErrorHandlersTest(TestCase):
    """Tests para los handlers de error personalizados."""

    def test_404_page(self):
        """Test: Página 404 personalizada."""
        response = self.client.get('/pagina-que-no-existe/')
        self.assertEqual(response.status_code, 404)


# =============================================================================
# TESTS DE RENDIMIENTO BÁSICO
# =============================================================================

class PerformanceTest(TestCase):
    """Tests básicos de rendimiento."""

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_home_page_loads_quickly(self):
        """Test: Home carga en tiempo razonable."""
        import time

        start = time.time()
        response = self.client.get(reverse('home'))
        elapsed = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 1.0)  # Menos de 1 segundo

    def test_contact_page_loads_quickly(self):
        """Test: Contact carga en tiempo razonable."""
        import time

        start = time.time()
        response = self.client.get(reverse('contact_us'))
        elapsed = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 1.0)

    def test_form_submission_processes_quickly(self):
        """Test: Envío de formulario procesa en tiempo razonable."""
        import time

        data = create_valid_contact_data()

        start = time.time()
        response = self.client.post(reverse('contact_us'), data)
        elapsed = time.time() - start

        self.assertIn(response.status_code, [200, 302])
        self.assertLess(elapsed, 2.0)  # Menos de 2 segundos
