"""
Tests para la app Leads.

Batería completa de pruebas que cubre:
- Modelo Lead y LeadImage
- Formulario LeadForm
- Validaciones
- Edge cases y situaciones de error
"""

from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from decimal import Decimal
import io
from PIL import Image

from .models import Lead, LeadImage, Budget, LeadLog
from .forms import LeadForm


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


def create_valid_lead_data():
    """Retorna datos válidos para crear un Lead."""
    return {
        'name': 'Juan Pérez García',
        'email': 'juan@example.com',
        'phone': '666777888',
        'location': 'Calle Mayor 1, Barcelona, 08001',
        'message': 'Este es un mensaje de prueba con más de 20 caracteres.',
    }


# =============================================================================
# TESTS DEL MODELO LEAD
# =============================================================================

class LeadModelTest(TestCase):
    """Tests para el modelo Lead."""

    def test_create_lead_with_required_fields(self):
        """Test: Crear Lead con campos requeridos."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        self.assertIsNotNone(lead.id)
        self.assertEqual(lead.status, 'nuevo')
        self.assertEqual(lead.source, 'web')

    def test_lead_str_representation(self):
        """Test: Representación string del Lead."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        self.assertIn('Test User', str(lead))
        self.assertIn('Nuevo', str(lead))

    def test_lead_default_values(self):
        """Test: Valores por defecto del Lead."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        self.assertEqual(lead.status, 'nuevo')
        self.assertEqual(lead.source, 'web')
        self.assertEqual(lead.preferred_contact, 'email')
        self.assertFalse(lead.privacy_accepted)

    def test_lead_timestamps(self):
        """Test: Timestamps se crean automáticamente."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        self.assertIsNotNone(lead.created_at)
        self.assertIsNotNone(lead.updated_at)

    def test_lead_ordering(self):
        """Test: Leads se ordenan por fecha descendente."""
        lead1 = Lead.objects.create(
            name='First',
            email='first@example.com',
            phone='666777881',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        lead2 = Lead.objects.create(
            name='Second',
            email='second@example.com',
            phone='666777882',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        leads = Lead.objects.all()
        self.assertEqual(leads[0], lead2)  # El más reciente primero

    def test_lead_status_choices(self):
        """Test: Status solo acepta valores válidos."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        valid_statuses = ['nuevo', 'contactado', 'presupuestado', 'cerrado', 'descartado']
        for status in valid_statuses:
            lead.status = status
            lead.save()
            self.assertEqual(lead.status, status)

    def test_lead_source_choices(self):
        """Test: Source solo acepta valores válidos."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        valid_sources = ['web', 'telefono', 'recomendacion', 'otro']
        for source in valid_sources:
            lead.source = source
            lead.save()
            self.assertEqual(lead.source, source)


class LeadValidationTest(TestCase):
    """Tests de validación del modelo Lead."""

    def test_name_minimum_length(self):
        """Test: Nombre debe tener al menos 2 caracteres."""
        lead = Lead(
            name='A',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        with self.assertRaises(ValidationError) as context:
            lead.full_clean()
        self.assertIn('name', context.exception.message_dict)

    def test_phone_valid_format(self):
        """Test: Teléfono debe tener entre 9 y 15 dígitos."""
        # Teléfono muy corto
        lead = Lead(
            name='Test User',
            email='test@example.com',
            phone='12345',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        with self.assertRaises(ValidationError) as context:
            lead.full_clean()
        self.assertIn('phone', context.exception.message_dict)

    def test_phone_with_spaces_and_dashes(self):
        """Test: Teléfono puede tener espacios y guiones."""
        lead = Lead(
            name='Test User',
            email='test@example.com',
            phone='666-777-888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        lead.full_clean()  # No debería lanzar excepción

    def test_message_minimum_length(self):
        """Test: Mensaje debe tener al menos 20 caracteres."""
        lead = Lead(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Corto'
        )
        with self.assertRaises(ValidationError) as context:
            lead.full_clean()
        self.assertIn('message', context.exception.message_dict)

    def test_email_valid_format(self):
        """Test: Email debe tener formato válido."""
        lead = Lead(
            name='Test User',
            email='invalid-email',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        with self.assertRaises(ValidationError) as context:
            lead.full_clean()
        self.assertIn('email', context.exception.message_dict)


class LeadImageModelTest(TestCase):
    """Tests para el modelo LeadImage."""

    def setUp(self):
        self.lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )

    def test_create_lead_image(self):
        """Test: Crear imagen asociada a Lead."""
        image = create_test_image()
        lead_image = LeadImage.objects.create(
            lead=self.lead,
            image=image
        )
        self.assertIsNotNone(lead_image.id)
        self.assertEqual(lead_image.lead, self.lead)

    def test_lead_images_count(self):
        """Test: Contar imágenes de un Lead."""
        for i in range(3):
            image = create_test_image(name=f'test{i}.jpg')
            LeadImage.objects.create(lead=self.lead, image=image)

        self.assertEqual(self.lead.get_images_count(), 3)

    def test_max_images_per_lead(self):
        """Test: Máximo 5 imágenes por Lead."""
        # Crear 5 imágenes
        for i in range(5):
            image = create_test_image(name=f'test{i}.jpg')
            LeadImage.objects.create(lead=self.lead, image=image)

        # Intentar crear la 6ta
        image = create_test_image(name='test6.jpg')
        lead_image = LeadImage(lead=self.lead, image=image)
        with self.assertRaises(ValidationError):
            lead_image.full_clean()

    def test_lead_image_cascade_delete(self):
        """Test: Imágenes se eliminan al eliminar Lead."""
        image = create_test_image()
        LeadImage.objects.create(lead=self.lead, image=image)

        lead_id = self.lead.id
        self.lead.delete()

        self.assertEqual(LeadImage.objects.filter(lead_id=lead_id).count(), 0)


# =============================================================================
# TESTS DEL FORMULARIO LEADFORM
# =============================================================================

class LeadFormTest(TestCase):
    """Tests para el formulario LeadForm."""

    def test_valid_form(self):
        """Test: Formulario válido con datos correctos."""
        data = create_valid_lead_data()
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_empty_form(self):
        """Test: Formulario vacío es inválido."""
        form = LeadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('phone', form.errors)
        self.assertIn('message', form.errors)

    def test_name_too_short(self):
        """Test: Nombre muy corto es inválido."""
        data = create_valid_lead_data()
        data['name'] = 'Ab'
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_message_too_short(self):
        """Test: Mensaje muy corto es inválido."""
        data = create_valid_lead_data()
        data['message'] = 'Muy corto'
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_message_too_long(self):
        """Test: Mensaje muy largo es inválido."""
        data = create_valid_lead_data()
        data['message'] = 'x' * 1001
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_invalid_email_format(self):
        """Test: Email con formato inválido."""
        data = create_valid_lead_data()
        data['email'] = 'not-an-email'
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_form_saves_lead(self):
        """Test: Formulario guarda Lead correctamente."""
        data = create_valid_lead_data()
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())
        lead = form.save()
        self.assertIsNotNone(lead.id)
        self.assertEqual(lead.name, data['name'])


# =============================================================================
# TESTS DE EDGE CASES
# =============================================================================

class LeadEdgeCasesTest(TestCase):
    """Tests de casos límite y situaciones especiales."""

    def test_name_with_special_characters(self):
        """Test: Nombre con caracteres especiales (acentos, ñ)."""
        data = create_valid_lead_data()
        data['name'] = 'José María Núñez Ñoño'
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_name_with_numbers(self):
        """Test: Nombre con números (debería fallar)."""
        data = create_valid_lead_data()
        data['name'] = 'Juan123'
        form = LeadForm(data=data)
        # Depende de la validación implementada
        # Si hay patrón que solo acepta letras, debería fallar

    def test_phone_with_international_prefix(self):
        """Test: Teléfono con prefijo internacional."""
        data = create_valid_lead_data()
        data['phone'] = '+34666777888'
        form = LeadForm(data=data)
        # El teléfono con + puede ser válido o no según validación

    def test_message_with_html_tags(self):
        """Test: Mensaje con tags HTML (posible XSS)."""
        data = create_valid_lead_data()
        data['message'] = '<script>alert("xss")</script> Mensaje normal aquí.'
        form = LeadForm(data=data)
        if form.is_valid():
            lead = form.save()
            # El contenido se guarda pero Django lo escapa al renderizar
            self.assertIn('<script>', lead.message)

    def test_message_with_sql_injection(self):
        """Test: Mensaje con intento de SQL injection."""
        data = create_valid_lead_data()
        data['message'] = "'; DROP TABLE leads; -- Mensaje normal aquí con más texto."
        form = LeadForm(data=data)
        if form.is_valid():
            lead = form.save()
            # Django ORM previene SQL injection
            self.assertEqual(Lead.objects.count(), 1)

    def test_email_with_plus_sign(self):
        """Test: Email con + (formato válido)."""
        data = create_valid_lead_data()
        data['email'] = 'user+tag@example.com'
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_very_long_email(self):
        """Test: Email muy largo."""
        data = create_valid_lead_data()
        data['email'] = 'a' * 200 + '@example.com'
        form = LeadForm(data=data)
        # Debería fallar por longitud máxima de EmailField

    def test_whitespace_only_fields(self):
        """Test: Campos con solo espacios en blanco."""
        data = {
            'name': '   ',
            'email': 'test@example.com',
            'phone': '666777888',
            'message': '                              ',  # 30 espacios
        }
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())

    def test_unicode_in_message(self):
        """Test: Mensaje con emojis y caracteres unicode."""
        data = create_valid_lead_data()
        data['message'] = '¡Hola! 👋 Necesito un presupuesto para mi casa 🏠'
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_boundary_message_length_20(self):
        """Test: Mensaje con exactamente 20 caracteres (límite)."""
        data = create_valid_lead_data()
        data['message'] = '12345678901234567890'  # Exactamente 20
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_boundary_message_length_19(self):
        """Test: Mensaje con 19 caracteres (bajo límite)."""
        data = create_valid_lead_data()
        data['message'] = '1234567890123456789'  # 19 caracteres
        form = LeadForm(data=data)
        self.assertFalse(form.is_valid())

    def test_boundary_message_length_1000(self):
        """Test: Mensaje con exactamente 1000 caracteres (límite)."""
        data = create_valid_lead_data()
        data['message'] = 'x' * 1000
        form = LeadForm(data=data)
        self.assertTrue(form.is_valid())


class LeadImageEdgeCasesTest(TestCase):
    """Tests de edge cases para imágenes."""

    def setUp(self):
        self.lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )

    def test_image_png_format(self):
        """Test: Imagen en formato PNG."""
        image = create_test_image(name='test.png', format='PNG')
        lead_image = LeadImage(lead=self.lead, image=image)
        lead_image.full_clean()  # No debería lanzar excepción

    def test_image_webp_format(self):
        """Test: Imagen en formato WEBP."""
        image = create_test_image(name='test.webp', format='WEBP')
        lead_image = LeadImage(lead=self.lead, image=image)
        lead_image.full_clean()  # No debería lanzar excepción

    def test_image_invalid_format(self):
        """Test: Archivo que no es imagen."""
        fake_file = SimpleUploadedFile(
            name='document.pdf',
            content=b'%PDF-1.4 fake pdf content',
            content_type='application/pdf'
        )
        lead_image = LeadImage(lead=self.lead, image=fake_file)
        with self.assertRaises(ValidationError):
            lead_image.full_clean()

    def test_image_very_large(self):
        """Test: Imagen muy grande (>5MB)."""
        # Crear imagen grande
        large_image = create_test_image(name='large.jpg', size=(5000, 5000))
        lead_image = LeadImage(lead=self.lead, image=large_image)
        # Debería fallar si hay validación de tamaño
        # (depende de la implementación del validator)


# =============================================================================
# TESTS DE CONCURRENCIA Y ESTRÉS
# =============================================================================

class LeadConcurrencyTest(TestCase):
    """Tests de concurrencia y múltiples operaciones."""

    def test_create_multiple_leads_same_email(self):
        """Test: Crear múltiples leads con el mismo email (permitido)."""
        for i in range(5):
            Lead.objects.create(
                name=f'User {i}',
                email='same@example.com',
                phone=f'66677788{i}',
                message='Mensaje de prueba con más de veinte caracteres.'
            )
        self.assertEqual(Lead.objects.filter(email='same@example.com').count(), 5)

    def test_create_100_leads(self):
        """Test: Crear 100 leads (prueba de volumen)."""
        for i in range(100):
            Lead.objects.create(
                name=f'User {i}',
                email=f'user{i}@example.com',
                phone=f'666{i:06d}',
                message='Mensaje de prueba con más de veinte caracteres.'
            )
        self.assertEqual(Lead.objects.count(), 100)

    def test_lead_with_max_images(self):
        """Test: Lead con máximo de imágenes permitidas."""
        lead = Lead.objects.create(
            name='Test User',
            email='test@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.'
        )
        for i in range(5):
            image = create_test_image(name=f'img{i}.jpg')
            LeadImage.objects.create(lead=lead, image=image)

        self.assertEqual(lead.get_images_count(), 5)


# =============================================================================
# TESTS DE NOTIFICACIONES POR EMAIL
# =============================================================================

from unittest.mock import patch, MagicMock
from apps.leads.notifications import (
    notify_new_lead,
    send_admin_notification,
    send_customer_confirmation,
    get_notification_config,
)


class NotificationConfigTest(TestCase):
    """Tests para la configuración de notificaciones."""

    def test_get_notification_config(self):
        """Test: Obtener configuración de notificaciones."""
        config = get_notification_config()
        self.assertIsInstance(config, dict)

    @override_settings(NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAILS': ['test@test.com']}})
    def test_config_returns_correct_values(self):
        """Test: Configuración retorna valores correctos."""
        config = get_notification_config()
        self.assertTrue(config.get('ENABLED'))
        self.assertEqual(config.get('ADMIN_EMAILS'), ['test@test.com'])


class AdminNotificationTest(TestCase):
    """Tests para notificaciones al administrador."""

    def setUp(self):
        self.lead = Lead.objects.create(
            name='Test User',
            email='customer@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.',
            source='web',
        )

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAILS': ['admin@test.com']}},
        DEFAULT_FROM_EMAIL='noreply@test.com',
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_send_admin_notification_success(self, mock_email_class):
        """Test: Envío exitoso de notificación al admin."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        result = send_admin_notification(self.lead)

        self.assertTrue(result)
        mock_email_class.assert_called_once()
        mock_email.attach_alternative.assert_called_once()
        mock_email.send.assert_called_once_with(fail_silently=False)

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAILS': ['admin@test.com']}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_admin_notification_contains_lead_data(self, mock_email_class):
        """Test: Notificación contiene datos del lead."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        send_admin_notification(self.lead)

        call_kwargs = mock_email_class.call_args.kwargs
        self.assertIn('Test User', call_kwargs['subject'])
        self.assertEqual(call_kwargs['to'], ['admin@test.com'])

    @override_settings(NOTIFICATIONS={'LEAD': {'ENABLED': False}})
    def test_admin_notification_disabled(self):
        """Test: Notificación deshabilitada no envía email."""
        result = send_admin_notification(self.lead)
        self.assertFalse(result)

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAILS': ['admin@test.com']}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_admin_notification_handles_error(self, mock_email_class):
        """Test: Error en envío no lanza excepción."""
        mock_email = MagicMock()
        mock_email.send.side_effect = Exception('SMTP Error')
        mock_email_class.return_value = mock_email

        result = send_admin_notification(self.lead)

        self.assertFalse(result)

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAILS': ['admin@test.com', 'info@test.com']}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_admin_notification_multiple_recipients(self, mock_email_class):
        """Test: Notificación se envía a múltiples destinatarios."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        result = send_admin_notification(self.lead)

        self.assertTrue(result)
        call_kwargs = mock_email_class.call_args.kwargs
        self.assertEqual(call_kwargs['to'], ['admin@test.com', 'info@test.com'])

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAILS': 'admin@test.com, info@test.com'}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_admin_notification_csv_string(self, mock_email_class):
        """Test: Parsing de string CSV (formato env var)."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        result = send_admin_notification(self.lead)

        self.assertTrue(result)
        call_kwargs = mock_email_class.call_args.kwargs
        self.assertEqual(call_kwargs['to'], ['admin@test.com', 'info@test.com'])

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'ADMIN_EMAIL': 'legacy@test.com'}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_admin_notification_backward_compat(self, mock_email_class):
        """Test: ADMIN_EMAIL legacy sigue funcionando."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        result = send_admin_notification(self.lead)

        self.assertTrue(result)
        call_kwargs = mock_email_class.call_args.kwargs
        self.assertEqual(call_kwargs['to'], ['legacy@test.com'])


class CustomerConfirmationTest(TestCase):
    """Tests para confirmación al cliente."""

    def setUp(self):
        self.lead = Lead.objects.create(
            name='Test User',
            email='customer@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.',
            source='web',
        )

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'SEND_CUSTOMER_CONFIRMATION': True}},
        DEFAULT_FROM_EMAIL='noreply@test.com',
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_send_customer_confirmation_success(self, mock_email_class):
        """Test: Envío exitoso de confirmación al cliente."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        result = send_customer_confirmation(self.lead)

        self.assertTrue(result)
        mock_email.send.assert_called_once()

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'SEND_CUSTOMER_CONFIRMATION': True}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_customer_confirmation_sent_to_correct_email(self, mock_email_class):
        """Test: Confirmación se envía al email del cliente."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        send_customer_confirmation(self.lead)

        call_kwargs = mock_email_class.call_args.kwargs
        self.assertEqual(call_kwargs['to'], ['customer@example.com'])

    @override_settings(NOTIFICATIONS={'LEAD': {'ENABLED': True, 'SEND_CUSTOMER_CONFIRMATION': False}})
    def test_customer_confirmation_disabled(self):
        """Test: Confirmación deshabilitada no envía email."""
        result = send_customer_confirmation(self.lead)
        self.assertFalse(result)

    @override_settings(NOTIFICATIONS={'LEAD': {'ENABLED': False}})
    def test_customer_confirmation_when_notifications_disabled(self):
        """Test: Confirmación no se envía si notificaciones están deshabilitadas."""
        result = send_customer_confirmation(self.lead)
        self.assertFalse(result)

    @override_settings(
        NOTIFICATIONS={'LEAD': {'ENABLED': True, 'SEND_CUSTOMER_CONFIRMATION': True}},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_customer_confirmation_handles_error(self, mock_email_class):
        """Test: Error en envío no lanza excepción."""
        mock_email = MagicMock()
        mock_email.send.side_effect = Exception('SMTP Error')
        mock_email_class.return_value = mock_email

        result = send_customer_confirmation(self.lead)

        self.assertFalse(result)


class NotifyNewLeadTest(TestCase):
    """Tests para la función principal de notificación."""

    def setUp(self):
        self.lead = Lead.objects.create(
            name='Test User',
            email='customer@example.com',
            phone='666777888',
            message='Mensaje de prueba con más de veinte caracteres.',
            source='web',
        )

    @override_settings(
        NOTIFICATIONS={'LEAD': {
            'ENABLED': True,
            'ADMIN_EMAILS': ['admin@test.com'],
            'SEND_CUSTOMER_CONFIRMATION': True,
        }},
        DEFAULT_FROM_EMAIL='noreply@test.com',
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_notify_new_lead_sends_both(self, mock_email_class):
        """Test: notify_new_lead envía ambas notificaciones."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        results = notify_new_lead(self.lead)

        self.assertTrue(results['admin_notified'])
        self.assertTrue(results['customer_confirmed'])
        # Se llama dos veces: una para admin, otra para cliente
        self.assertEqual(mock_email.send.call_count, 2)

    @override_settings(
        NOTIFICATIONS={'LEAD': {
            'ENABLED': True,
            'ADMIN_EMAILS': ['admin@test.com'],
            'SEND_CUSTOMER_CONFIRMATION': False,
        }},
    )
    @patch('apps.leads.notifications.EmailMultiAlternatives')
    def test_notify_new_lead_admin_only(self, mock_email_class):
        """Test: notify_new_lead solo envía a admin si confirmación deshabilitada."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        results = notify_new_lead(self.lead)

        self.assertTrue(results['admin_notified'])
        self.assertFalse(results['customer_confirmed'])
        self.assertEqual(mock_email.send.call_count, 1)

    @override_settings(NOTIFICATIONS={'LEAD': {'ENABLED': False}})
    def test_notify_new_lead_all_disabled(self):
        """Test: notify_new_lead no envía nada si está deshabilitado."""
        results = notify_new_lead(self.lead)

        self.assertFalse(results['admin_notified'])
        self.assertFalse(results['customer_confirmed'])
