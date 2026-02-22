"""
Management command para poblar la BD con servicios y proyectos de ejemplo.
Uso: python manage.py populate_projects

Idempotente: usa get_or_create, se puede ejecutar múltiples veces sin duplicar.
Requiere que las imágenes estén en MEDIA_ROOT/projects/2026/02/.
"""

from django.core.management.base import BaseCommand

from apps.projects.models import Project, ProjectImage
from apps.services.models import Service


SERVICES_DATA = [
    {
        'name': 'Reforma del hogar',
        'slug': 'reforma-del-hogar',
        'description': 'Reformas integrales de viviendas particulares.',
        'short_description': 'Reformas de viviendas',
        'order': 10,
    },
    {
        'name': 'Reforma industrial',
        'slug': 'reforma-industrial',
        'description': 'Acondicionamiento y reforma de naves y locales industriales.',
        'short_description': 'Reformas industriales',
        'order': 11,
    },
    {
        'name': 'Subcontrataciones',
        'slug': 'subcontrataciones',
        'description': 'Proyectos de gran envergadura junto a empresas líderes del sector.',
        'short_description': 'Obras con grandes empresas',
        'order': 12,
    },
]

PROJECTS_DATA = [
    {
        'title': 'Reforma integral piso en Eixample',
        'slug': 'reforma-integral-piso-eixample',
        'description': (
            'Reforma completa de vivienda de 95 m² en el Eixample barcelonés. '
            'Redistribución de espacios, nueva instalación eléctrica con domótica KNX '
            'y acabados de alta calidad. Cocina abierta al salón con isla central, '
            'dos baños completos y suelo de parquet natural en toda la vivienda.'
        ),
        'service_slug': 'reforma-del-hogar',
        'cover_image': 'projects/2026/02/reforma_hogar_cover.webp',
        'area': '95 m²',
        'duration': '3 meses',
        'year': 2024,
        'client': 'Particular',
        'order': 1,
        'images': [
            {
                'image': 'projects/2026/02/reforma_hogar_02.webp',
                'alt_text': 'Detalle de instalación domótica en la reforma',
                'order': 1,
            },
            {
                'image': 'projects/2026/02/reforma_hogar_03.webp',
                'alt_text': 'Resultado final del salón reformado',
                'order': 2,
            },
        ],
    },
    {
        'title': 'Acondicionamiento nave en Zona Franca',
        'slug': 'acondicionamiento-nave-zona-franca',
        'description': (
            'Acondicionamiento integral de nave industrial de 2.500 m² en el polígono '
            'de Zona Franca. Instalación de cuadro eléctrico general, distribución '
            'trifásica, iluminación LED industrial y sistema de emergencia. '
            'Adecuación completa a normativa vigente REBT.'
        ),
        'service_slug': 'reforma-industrial',
        'cover_image': 'projects/2026/02/reforma_industrial_cover.webp',
        'area': '2.500 m²',
        'duration': '5 meses',
        'year': 2023,
        'client': 'Confidencial',
        'order': 2,
        'images': [
            {
                'image': 'projects/2026/02/reforma_industrial_02.webp',
                'alt_text': 'Cuadro eléctrico general de la nave',
                'order': 1,
            },
            {
                'image': 'projects/2026/02/reforma_industrial_03.webp',
                'alt_text': 'Instalación de bandejas portacables en la nave',
                'order': 2,
            },
        ],
    },
    {
        'title': 'Subestación eléctrica con Elecnor',
        'slug': 'subestacion-electrica-elecnor',
        'description': (
            'Participación en la construcción de subestación eléctrica de media tensión '
            'como empresa subcontratada de Elecnor. Montaje de celdas, tendido de cables '
            'de potencia y puesta en marcha. Proyecto ejecutado bajo estrictos estándares '
            'de seguridad y calidad del sector energético.'
        ),
        'service_slug': 'subcontrataciones',
        'cover_image': 'projects/2026/02/subcontratacion_cover.webp',
        'area': '800 m²',
        'duration': '8 meses',
        'year': 2022,
        'client': 'Elecnor S.A.',
        'order': 3,
        'images': [
            {
                'image': 'projects/2026/02/subcontratacion_02.webp',
                'alt_text': 'Detalle del montaje de celdas de media tensión',
                'order': 1,
            },
            {
                'image': 'projects/2026/02/subcontratacion_03.webp',
                'alt_text': 'Vista general de la subestación terminada',
                'order': 2,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Crea servicios y proyectos de ejemplo para la galería'

    def handle(self, *args, **options):
        # Crear servicios
        for data in SERVICES_DATA:
            service, created = Service.objects.get_or_create(
                slug=data['slug'],
                defaults=data,
            )
            status = 'CREADO' if created else 'ya existe'
            self.stdout.write(f'  Servicio: {service.name} [{status}]')

        # Crear proyectos
        for data in PROJECTS_DATA:
            images_data = data.pop('images')
            service_slug = data.pop('service_slug')

            service = Service.objects.get(slug=service_slug)
            project, created = Project.objects.get_or_create(
                slug=data['slug'],
                defaults={**data, 'service': service},
            )
            status = 'CREADO' if created else 'ya existe'
            self.stdout.write(f'  Proyecto: {project.title} [{status}]')

            # Crear imágenes del proyecto
            if created:
                for img_data in images_data:
                    ProjectImage.objects.create(
                        project=project,
                        **img_data,
                    )
                    self.stdout.write(
                        f'    Imagen: {img_data["alt_text"]}'
                    )

            # Restaurar para idempotencia
            data['images'] = images_data
            data['service_slug'] = service_slug

        self.stdout.write(self.style.SUCCESS(
            '\nHecho. Recuerda que las imágenes deben estar en MEDIA_ROOT/projects/2026/02/'
        ))
