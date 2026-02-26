# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.leads.models import Lead, Budget, LeadLog
from apps.services.models import Service
from apps.users.models import UserProfile


THROTTLE_OFF = {
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}


def _make_rest_settings(**overrides):
    """Merge REST_FRAMEWORK defaults with throttle-off + overrides."""
    from django.conf import settings
    base = dict(settings.REST_FRAMEWORK)
    base.update(THROTTLE_OFF)
    base.update(overrides)
    return base


def _create_user(username, role='field', password='testpass123'):
    user = User.objects.create_user(username=username, password=password)
    # Signal creates profile with default 'field' role; update if needed
    profile = user.profile
    if profile.role != role:
        profile.role = role
        profile.save()
    return user


def _valid_lead_data(**overrides):
    data = {
        'name': 'Juan Pérez García',
        'email': 'juan@example.com',
        'phone': '666777888',
        'message': 'Necesito información sobre instalación de aerotermia en mi vivienda unifamiliar.',
    }
    data.update(overrides)
    return data


# =============================================================================
# FASE 2: Creación pública de leads
# =============================================================================

@override_settings(REST_FRAMEWORK=_make_rest_settings())
class LeadCreateAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_lead_success(self):
        resp = self.client.post('/api/v1/leads/', _valid_lead_data(), format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.source, 'api')
        self.assertEqual(lead.status, 'nuevo')
        self.assertTrue(lead.privacy_accepted)

    def test_create_lead_with_service(self):
        svc = Service.objects.create(name='Aero', slug='aero', description='X')
        resp = self.client.post(
            '/api/v1/leads/',
            _valid_lead_data(service=svc.pk),
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Lead.objects.first().service, svc)

    def test_create_lead_short_name_rejected(self):
        resp = self.client.post(
            '/api/v1/leads/', _valid_lead_data(name='AB'), format='json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('name', resp.data)

    def test_create_lead_short_message_rejected(self):
        resp = self.client.post(
            '/api/v1/leads/', _valid_lead_data(message='Corto'), format='json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('message', resp.data)

    def test_create_lead_invalid_phone(self):
        resp = self.client.post(
            '/api/v1/leads/', _valid_lead_data(phone='123'), format='json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('phone', resp.data)

    def test_honeypot_blocks_creation(self):
        data = _valid_lead_data(website_url='http://spam.com')
        resp = self.client.post('/api/v1/leads/', data, format='json')
        self.assertEqual(resp.status_code, 201)  # fake success
        self.assertEqual(Lead.objects.count(), 0)

    def test_create_lead_creates_log(self):
        self.client.post('/api/v1/leads/', _valid_lead_data(), format='json')
        self.assertEqual(LeadLog.objects.count(), 1)
        log = LeadLog.objects.first()
        self.assertEqual(log.action, 'created')

    def test_create_lead_missing_email(self):
        data = _valid_lead_data()
        del data['email']
        resp = self.client.post('/api/v1/leads/', data, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_create_lead_cannot_set_status(self):
        """Status no se acepta en input, se fuerza a 'nuevo'."""
        resp = self.client.post(
            '/api/v1/leads/',
            _valid_lead_data(status='cerrado'),
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Lead.objects.first().status, 'nuevo')


# =============================================================================
# FASE 3: Endpoints autenticados — List/Retrieve
# =============================================================================

@override_settings(REST_FRAMEWORK=_make_rest_settings())
class LeadListAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_user = _create_user('admin1', role='admin')
        self.office_user = _create_user('office1', role='office')
        self.field_user = _create_user('tech1', role='field')

        self.lead = Lead.objects.create(
            name='Test Lead', email='t@t.com', phone='666777888',
            message='Test message long enough for validation purposes here.',
            status='nuevo', source='web', assigned_to=self.field_user,
        )

    def test_unauthenticated_cannot_list(self):
        resp = self.client.get('/api/v1/leads/')
        self.assertEqual(resp.status_code, 403)

    def test_admin_sees_all_leads(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/v1/leads/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_office_sees_all_leads(self):
        self.client.force_authenticate(user=self.office_user)
        resp = self.client.get('/api/v1/leads/')
        self.assertEqual(resp.data['count'], 1)

    def test_field_sees_only_assigned(self):
        self.client.force_authenticate(user=self.field_user)
        resp = self.client.get('/api/v1/leads/')
        self.assertEqual(resp.data['count'], 1)

        # Another field user sees nothing
        other = _create_user('tech2', role='field')
        self.client.force_authenticate(user=other)
        resp = self.client.get('/api/v1/leads/')
        self.assertEqual(resp.data['count'], 0)

    def test_list_has_annotated_counts(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/v1/leads/')
        item = resp.data['results'][0]
        self.assertIn('images_count', item)
        self.assertIn('budgets_count', item)

    def test_retrieve_lead(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get(f'/api/v1/leads/{self.lead.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'Test Lead')

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/v1/leads/', {'status': 'nuevo'})
        self.assertEqual(resp.data['count'], 1)
        resp2 = self.client.get('/api/v1/leads/', {'status': 'cerrado'})
        self.assertEqual(resp2.data['count'], 0)


# =============================================================================
# FASE 3: Endpoints autenticados — Update
# =============================================================================

@override_settings(REST_FRAMEWORK=_make_rest_settings())
class LeadUpdateAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_user = _create_user('admin1', role='admin')
        self.field_user = _create_user('tech1', role='field')
        self.lead = Lead.objects.create(
            name='Update Lead', email='u@u.com', phone='666777888',
            message='Mensaje suficientemente largo para pasar validación ok.',
            status='nuevo', source='web', assigned_to=self.field_user,
        )

    def test_admin_can_patch(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.patch(
            f'/api/v1/leads/{self.lead.pk}/',
            {'status': 'contactado'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, 'contactado')

    def test_field_can_patch_assigned_lead(self):
        self.client.force_authenticate(user=self.field_user)
        resp = self.client.patch(
            f'/api/v1/leads/{self.lead.pk}/',
            {'notes': 'Visita realizada'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)

    def test_field_cannot_patch_unassigned_lead(self):
        """Field user gets 404 (not 403) because queryset filters by assigned_to."""
        other = _create_user('tech2', role='field')
        self.client.force_authenticate(user=other)
        resp = self.client.patch(
            f'/api/v1/leads/{self.lead.pk}/',
            {'status': 'contactado'},
            format='json',
        )
        self.assertEqual(resp.status_code, 404)

    def test_put_not_allowed(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.put(
            f'/api/v1/leads/{self.lead.pk}/',
            _valid_lead_data(),
            format='json',
        )
        self.assertEqual(resp.status_code, 405)

    def test_delete_not_allowed(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.delete(f'/api/v1/leads/{self.lead.pk}/')
        self.assertEqual(resp.status_code, 405)


# =============================================================================
# FASE 3: Logs + Budgets
# =============================================================================

@override_settings(REST_FRAMEWORK=_make_rest_settings())
class LeadLogsAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_user = _create_user('admin1', role='admin')
        self.field_user = _create_user('tech1', role='field')
        self.lead = Lead.objects.create(
            name='Log Lead', email='l@l.com', phone='666777888',
            message='Mensaje largo para test de logs de auditoría del lead.',
            status='nuevo', source='web',
        )
        LeadLog.objects.create(lead=self.lead, action='created', new_value='Test')

    def test_admin_can_view_logs(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get(f'/api/v1/leads/{self.lead.pk}/logs/')
        self.assertEqual(resp.status_code, 200)

    def test_field_cannot_view_logs(self):
        self.client.force_authenticate(user=self.field_user)
        resp = self.client.get(f'/api/v1/leads/{self.lead.pk}/logs/')
        self.assertEqual(resp.status_code, 403)


@override_settings(REST_FRAMEWORK=_make_rest_settings())
class BudgetAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin_user = _create_user('admin1', role='admin')
        self.field_user = _create_user('tech1', role='field')
        self.lead = Lead.objects.create(
            name='Budget Lead', email='b@b.com', phone='666777888',
            message='Mensaje largo para test de presupuestos del lead.',
            status='nuevo', source='web',
        )
        Budget.objects.create(
            lead=self.lead, description='Instalación aerotermia',
            amount=8500, created_by=self.admin_user,
        )

    def test_admin_can_list_budgets(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/v1/budgets/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_field_cannot_list_budgets(self):
        self.client.force_authenticate(user=self.field_user)
        resp = self.client.get('/api/v1/budgets/')
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_cannot_list_budgets(self):
        resp = self.client.get('/api/v1/budgets/')
        self.assertEqual(resp.status_code, 403)
