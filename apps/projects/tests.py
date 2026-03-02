import io
from datetime import date

from PIL import Image

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from apps.projects.models import Project, ProjectImage
from apps.services.models import Service


def _create_test_image(name='test.jpg', size=(100, 100), fmt='JPEG'):
    """Crea imagen de prueba en memoria."""
    img = Image.new('RGB', size, color='blue')
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=buf.read(),
        content_type=f'image/{fmt.lower()}',
    )


class ProjectModelTest(TestCase):

    def setUp(self):
        self.service = Service.objects.create(
            name='Reformas', description='Reformas integrales', is_active=True
        )

    def _create_project(self, **kwargs):
        defaults = {
            'title': 'Proyecto Test',
            'description': 'Descripción del proyecto',
            'service': self.service,
            'cover_image': _create_test_image(),
            'year': 2024,
        }
        defaults.update(kwargs)
        return Project.objects.create(**defaults)

    def test_create_project(self):
        project = self._create_project()
        self.assertEqual(project.title, 'Proyecto Test')
        self.assertTrue(project.is_active)

    def test_str(self):
        project = self._create_project()
        self.assertEqual(str(project), 'Proyecto Test')

    def test_slug_auto_generated(self):
        project = self._create_project(title='Mi Gran Proyecto')
        self.assertEqual(project.slug, 'mi-gran-proyecto')

    def test_slug_not_overwritten(self):
        project = self._create_project(title='Original', slug='custom-slug')
        self.assertEqual(project.slug, 'custom-slug')

    def test_clean_future_year(self):
        project = self._create_project()
        project.year = date.today().year + 1
        with self.assertRaises(ValidationError) as ctx:
            project.clean()
        self.assertIn('year', ctx.exception.message_dict)

    def test_clean_current_year_valid(self):
        project = self._create_project(year=date.today().year)
        project.clean()  # No debe lanzar excepción

    def test_get_details_list_full(self):
        project = self._create_project(
            area='500 m²', duration='3 meses', year=2024, client='ACME'
        )
        details = project.get_details_list()
        self.assertEqual(len(details), 4)
        self.assertIn('Superficie: 500 m²', details)
        self.assertIn('Cliente: ACME', details)

    def test_get_details_list_partial(self):
        project = self._create_project(area='', duration='', client='')
        details = project.get_details_list()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0], 'Año: 2024')

    def test_get_all_image_urls_cover_only(self):
        project = self._create_project()
        urls = project.get_all_image_urls()
        self.assertEqual(len(urls), 1)
        self.assertIn('projects/', urls[0])

    def test_get_all_image_urls_with_gallery(self):
        project = self._create_project()
        ProjectImage.objects.create(
            project=project, image=_create_test_image('extra1.jpg'), order=0
        )
        ProjectImage.objects.create(
            project=project, image=_create_test_image('extra2.jpg'), order=1
        )
        urls = project.get_all_image_urls()
        self.assertEqual(len(urls), 3)

    def test_ordering(self):
        p1 = self._create_project(
            title='Normal', slug='normal',
            is_featured=False, order=0, year=2024,
        )
        p2 = self._create_project(
            title='Destacado', slug='destacado',
            is_featured=True, order=0, year=2023,
        )
        projects = list(Project.objects.all())
        self.assertEqual(projects[0], p2)  # featured first


class ProjectImageModelTest(TestCase):

    def setUp(self):
        self.service = Service.objects.create(
            name='Electricidad', description='Instalaciones', is_active=True
        )
        self.project = Project.objects.create(
            title='Proyecto Imgs',
            description='Desc',
            service=self.service,
            cover_image=_create_test_image(),
            year=2024,
        )

    def test_create_image(self):
        img = ProjectImage.objects.create(
            project=self.project,
            image=_create_test_image('gallery.jpg'),
            order=0,
        )
        self.assertIn('Proyecto Imgs', str(img))

    def test_max_images_validation(self):
        for i in range(ProjectImage.MAX_IMAGES_PER_PROJECT):
            ProjectImage.objects.create(
                project=self.project,
                image=_create_test_image(f'img{i}.jpg'),
                order=i,
            )
        extra = ProjectImage(
            project=self.project,
            image=_create_test_image('overflow.jpg'),
            order=99,
        )
        with self.assertRaises(ValidationError):
            extra.clean()


class ProjectViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.service = Service.objects.create(
            name='Reformas Industriales',
            description='Reformas de naves',
            is_active=True,
            order=1,
        )

    def _create_project(self, **kwargs):
        defaults = {
            'title': 'Proyecto Vista',
            'description': 'Descripción vista',
            'service': self.service,
            'cover_image': _create_test_image(),
            'year': 2024,
            'is_active': True,
        }
        defaults.update(kwargs)
        return Project.objects.create(**defaults)

    def test_projects_page_200(self):
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)

    def test_projects_template(self):
        response = self.client.get(reverse('projects'))
        self.assertTemplateUsed(response, 'pages/projects.html')

    def test_context_keys(self):
        self._create_project()
        response = self.client.get(reverse('projects'))
        self.assertIn('projects_list', response.context)
        self.assertIn('filter_categories', response.context)
        self.assertIn('projects_data', response.context)

    def test_inactive_excluded(self):
        self._create_project(title='Activo', slug='activo', is_active=True)
        self._create_project(title='Inactivo', slug='inactivo', is_active=False)
        response = self.client.get(reverse('projects'))
        projects = response.context['projects_list']
        titles = [p.title for p in projects]
        self.assertIn('Activo', titles)
        self.assertNotIn('Inactivo', titles)

    def test_filter_categories(self):
        self._create_project()
        response = self.client.get(reverse('projects'))
        categories = response.context['filter_categories']
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]['slug'], 'reformas-industriales')

    def test_projects_data_json(self):
        project = self._create_project(
            area='100 m²', duration='2 meses', client='Test Client'
        )
        response = self.client.get(reverse('projects'))
        data = response.context['projects_data']
        self.assertIn(str(project.id), data)
        entry = data[str(project.id)]
        self.assertEqual(entry['title'], 'Proyecto Vista')
        self.assertIsInstance(entry['images'], list)
        self.assertGreaterEqual(len(entry['images']), 1)

    def test_empty_state(self):
        response = self.client.get(reverse('projects'))
        self.assertContains(response, 'No hay proyectos disponibles')

    def test_no_service_excluded_from_filters(self):
        """Proyectos sin servicio no generan categoría de filtro."""
        self._create_project(title='Sin Servicio', slug='sin-servicio', service=None)
        response = self.client.get(reverse('projects'))
        categories = response.context['filter_categories']
        self.assertEqual(len(categories), 0)


class ProjectAdminTest(TestCase):

    def setUp(self):
        from django.contrib.auth.models import User
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'pass123'
        )
        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_admin_changelist(self):
        response = self.client.get('/admynstal/projects/project/')
        self.assertEqual(response.status_code, 200)

    def test_admin_add_page(self):
        response = self.client.get('/admynstal/projects/project/add/')
        self.assertEqual(response.status_code, 200)

    def test_office_admin_no_projects(self):
        # Projects ya no está registrado en el panel de oficina
        self.admin_user.profile.role = 'admin'
        self.admin_user.profile.save()
        response = self.client.get('/offynstal/projects/project/')
        self.assertEqual(response.status_code, 404)
