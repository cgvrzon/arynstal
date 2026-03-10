import io
from datetime import date

from PIL import Image

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from apps.projects.models import Project, ProjectImage
from apps.services.models import Service


def _create_test_image(name='test.jpg', size=(800, 600), fmt='JPEG'):
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
            'description': 'Instalación completa de sistema de aerotermia con suelo radiante en chalet adosado de 200m².',
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

    def test_clean_short_description(self):
        project = self._create_project()
        project.description = 'Muy corta'
        with self.assertRaises(ValidationError) as ctx:
            project.clean()
        self.assertIn('description', ctx.exception.message_dict)

    def test_clean_small_cover_image(self):
        project = self._create_project(cover_image=_create_test_image(size=(200, 200)))
        with self.assertRaises(ValidationError) as ctx:
            project.clean()
        self.assertIn('cover_image', ctx.exception.message_dict)

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
            description='Instalación de climatización industrial con equipos de alta eficiencia energética.',
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

    def test_small_image_validation(self):
        img = ProjectImage(
            project=self.project,
            image=_create_test_image('small.jpg', size=(200, 200)),
            order=0,
        )
        with self.assertRaises(ValidationError) as ctx:
            img.clean()
        self.assertIn('image', ctx.exception.message_dict)


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

    def test_office_admin_project_accessible_to_admin(self):
        """Superusuario puede acceder al listado de proyectos en offynstal."""
        response = self.client.get('/offynstal/projects/project/')
        self.assertEqual(response.status_code, 200)


# =============================================================================
# TESTS DE PERMISOS: OfficeProjectAdmin
# =============================================================================

class OfficeProjectAdminPermissionsTest(TestCase):
    """
    Tests de permisos para OfficeProjectAdmin en el panel /offynstal/.

    Matriz de permisos (definida en OfficeProjectAdmin._is_office_or_admin):
        - office: listado, creación y edición. Sin eliminación.
        - admin: listado, creación y edición. Sin eliminación.
        - field: sin acceso a proyectos (redirige al login del site).
    """

    def setUp(self):
        from django.contrib.auth.models import User
        from apps.users.models import UserProfile
        from apps.services.models import Service

        self.client = Client()

        # Usuario con rol admin (is_staff para acceder al site)
        self.admin_user = User.objects.create_user(
            username='admin_office',
            email='admin@test.com',
            password='pass123',
            is_staff=True,
        )
        self.admin_user.profile.role = 'admin'
        self.admin_user.profile.save()

        # Usuario con rol office (is_staff para acceder al site)
        self.office_user = User.objects.create_user(
            username='office_user',
            email='office@test.com',
            password='pass123',
            is_staff=True,
        )
        self.office_user.profile.role = 'office'
        self.office_user.profile.save()

        # Usuario con rol field (is_staff para intentar acceder al site)
        self.field_user = User.objects.create_user(
            username='field_user',
            email='field@test.com',
            password='pass123',
            is_staff=True,
        )
        self.field_user.profile.role = 'field'
        self.field_user.profile.save()

        # Servicio para el proyecto de prueba
        self.service = Service.objects.create(
            name='Aerotermia',
            description='Instalación de aerotermia',
            is_active=True,
        )

        # Proyecto de prueba con datos que superan todas las validaciones
        self.project = Project.objects.create(
            title='Proyecto Permisos Test',
            description=(
                'Instalación completa de aerotermia con suelo radiante '
                'en vivienda unifamiliar de 180m² en Barcelona.'
            ),
            service=self.service,
            cover_image=_create_test_image(size=(800, 400)),
            year=date.today().year,
        )

    # -------------------------------------------------------------------------
    # ACCESO AL LISTADO — /offynstal/projects/project/
    # -------------------------------------------------------------------------

    def test_office_can_access_changelist(self):
        """Rol office puede ver el listado de proyectos en offynstal."""
        self.client.force_login(self.office_user)
        response = self.client.get('/offynstal/projects/project/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_changelist(self):
        """Rol admin puede ver el listado de proyectos en offynstal."""
        self.client.force_login(self.admin_user)
        response = self.client.get('/offynstal/projects/project/')
        self.assertEqual(response.status_code, 200)

    def test_field_cannot_access_changelist(self):
        """Rol field no tiene acceso al módulo de proyectos en offynstal."""
        self.client.force_login(self.field_user)
        response = self.client.get('/offynstal/projects/project/')
        # Django redirige al login del site cuando has_module_permission=False
        self.assertIn(response.status_code, [302, 403])

    # -------------------------------------------------------------------------
    # ACCESO AL FORMULARIO DE CREACIÓN — /offynstal/projects/project/add/
    # -------------------------------------------------------------------------

    def test_office_can_access_add_form(self):
        """Rol office puede acceder al formulario de creación de proyectos."""
        self.client.force_login(self.office_user)
        response = self.client.get('/offynstal/projects/project/add/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_add_form(self):
        """Rol admin puede acceder al formulario de creación de proyectos."""
        self.client.force_login(self.admin_user)
        response = self.client.get('/offynstal/projects/project/add/')
        self.assertEqual(response.status_code, 200)

    def test_field_cannot_access_add_form(self):
        """Rol field no puede acceder al formulario de creación de proyectos."""
        self.client.force_login(self.field_user)
        response = self.client.get('/offynstal/projects/project/add/')
        self.assertIn(response.status_code, [302, 403])

    # -------------------------------------------------------------------------
    # ACCESO AL FORMULARIO DE EDICIÓN — /offynstal/projects/project/{id}/change/
    # -------------------------------------------------------------------------

    def test_office_can_access_change_form(self):
        """Rol office puede acceder al formulario de edición de un proyecto."""
        self.client.force_login(self.office_user)
        response = self.client.get(
            f'/offynstal/projects/project/{self.project.pk}/change/'
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_change_form(self):
        """Rol admin puede acceder al formulario de edición de un proyecto."""
        self.client.force_login(self.admin_user)
        response = self.client.get(
            f'/offynstal/projects/project/{self.project.pk}/change/'
        )
        self.assertEqual(response.status_code, 200)

    def test_field_cannot_access_change_form(self):
        """Rol field no puede acceder al formulario de edición de proyectos."""
        self.client.force_login(self.field_user)
        response = self.client.get(
            f'/offynstal/projects/project/{self.project.pk}/change/'
        )
        self.assertIn(response.status_code, [302, 403])

    # -------------------------------------------------------------------------
    # PERMISOS DE ELIMINACIÓN — has_delete_permission = False siempre
    # -------------------------------------------------------------------------

    def test_office_has_no_delete_permission(self):
        """Rol office no puede eliminar proyectos (has_delete_permission=False)."""
        from apps.leads.office_admin import OfficeProjectAdmin, office_site
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.office_user

        admin_instance = OfficeProjectAdmin(Project, office_site)
        self.assertFalse(admin_instance.has_delete_permission(request))
        self.assertFalse(admin_instance.has_delete_permission(request, self.project))

    def test_admin_has_no_delete_permission_in_offynstal(self):
        """Rol admin tampoco puede eliminar proyectos desde offynstal."""
        from apps.leads.office_admin import OfficeProjectAdmin, office_site
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.admin_user

        admin_instance = OfficeProjectAdmin(Project, office_site)
        self.assertFalse(admin_instance.has_delete_permission(request))
        self.assertFalse(admin_instance.has_delete_permission(request, self.project))

    def test_delete_url_returns_no_access_for_office(self):
        """La URL de confirmación de borrado no es accesible para rol office."""
        self.client.force_login(self.office_user)
        response = self.client.get(
            f'/offynstal/projects/project/{self.project.pk}/delete/'
        )
        # Django devuelve 403 cuando has_delete_permission=False
        self.assertIn(response.status_code, [302, 403])
