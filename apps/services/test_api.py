# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
from django.test import TestCase
from rest_framework.test import APIClient

from apps.services.models import Service


class ServiceAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.svc = Service.objects.create(
            name='Aerotermia', slug='aerotermia',
            description='Sistemas de aerotermia',
            short_description='Aerotermia eficiente',
            is_active=True,
        )

    def test_list_services(self):
        resp = self.client.get('/api/v1/services/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_list_excludes_inactive(self):
        Service.objects.create(
            name='Inactivo', slug='inactivo',
            description='No visible', is_active=False,
        )
        resp = self.client.get('/api/v1/services/')
        self.assertEqual(resp.data['count'], 1)

    def test_retrieve_service(self):
        resp = self.client.get(f'/api/v1/services/{self.svc.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], 'Aerotermia')
        self.assertIn('description', resp.data)
        self.assertIn('slug', resp.data)

    def test_no_write_methods(self):
        resp = self.client.post('/api/v1/services/', {'name': 'X'})
        self.assertEqual(resp.status_code, 405)
