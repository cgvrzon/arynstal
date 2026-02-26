# [STACK-ORPHEUS:DRF] Archivo didáctico completo — eliminar para cleanup
import io

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.projects.models import Project, ProjectImage
from apps.services.models import Service


def _create_test_image(name='test.jpg'):
    img = Image.new('RGB', (100, 100), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/jpeg')


class ProjectAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.service = Service.objects.create(
            name='Aerotermia', slug='aerotermia', description='Desc',
        )
        self.project = Project.objects.create(
            title='Proyecto Test',
            slug='proyecto-test',
            description='Descripción del proyecto de prueba',
            service=self.service,
            cover_image=_create_test_image(),
            year=2024,
            area='100 m²',
            duration='3 meses',
            client='Cliente Test',
            is_active=True,
            is_featured=True,
        )
        self.img = ProjectImage.objects.create(
            project=self.project,
            image=_create_test_image('extra.jpg'),
            alt_text='Extra',
            order=1,
        )

    # ----- LIST -----

    def test_list_projects(self):
        resp = self.client.get('/api/v1/projects/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_list_excludes_inactive(self):
        Project.objects.create(
            title='Inactivo', slug='inactivo', description='X',
            cover_image=_create_test_image('inactive.jpg'),
            year=2023, is_active=False,
        )
        resp = self.client.get('/api/v1/projects/')
        self.assertEqual(resp.data['count'], 1)

    def test_list_serializer_fields(self):
        resp = self.client.get('/api/v1/projects/')
        item = resp.data['results'][0]
        self.assertIn('title', item)
        self.assertIn('service_name', item)
        self.assertIn('cover_image_url', item)
        self.assertNotIn('description', item)

    # ----- FILTER -----

    def test_filter_by_service_slug(self):
        resp = self.client.get('/api/v1/projects/', {'service': 'aerotermia'})
        self.assertEqual(resp.data['count'], 1)

    def test_filter_by_service_slug_no_match(self):
        resp = self.client.get('/api/v1/projects/', {'service': 'domotica'})
        self.assertEqual(resp.data['count'], 0)

    def test_filter_by_year(self):
        resp = self.client.get('/api/v1/projects/', {'year': 2024})
        self.assertEqual(resp.data['count'], 1)
        resp2 = self.client.get('/api/v1/projects/', {'year': 2020})
        self.assertEqual(resp2.data['count'], 0)

    def test_filter_by_is_featured(self):
        resp = self.client.get('/api/v1/projects/', {'is_featured': True})
        self.assertEqual(resp.data['count'], 1)

    # ----- DETAIL -----

    def test_retrieve_project(self):
        resp = self.client.get(f'/api/v1/projects/{self.project.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('description', resp.data)
        self.assertIn('details', resp.data)
        self.assertIn('images', resp.data)
        self.assertIn('additional_images', resp.data)

    def test_retrieve_details_list(self):
        resp = self.client.get(f'/api/v1/projects/{self.project.pk}/')
        self.assertIn('Superficie: 100 m²', resp.data['details'])

    def test_retrieve_images_includes_cover(self):
        resp = self.client.get(f'/api/v1/projects/{self.project.pk}/')
        self.assertGreaterEqual(len(resp.data['images']), 2)

    # ----- 404 -----

    def test_retrieve_inactive_returns_404(self):
        self.project.is_active = False
        self.project.save()
        resp = self.client.get(f'/api/v1/projects/{self.project.pk}/')
        self.assertEqual(resp.status_code, 404)

    def test_no_write_methods(self):
        resp = self.client.post('/api/v1/projects/', {'title': 'X'})
        self.assertEqual(resp.status_code, 405)
