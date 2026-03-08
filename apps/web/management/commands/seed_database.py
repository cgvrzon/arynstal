"""
===============================================================================
ARCHIVO: apps/web/management/commands/seed_database.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Management command para poblar la base de datos con datos de prueba.
    Facilita el desarrollo y testing creando datos realistas automáticamente.

USO:
    # Crear todos los datos de prueba
    python manage.py seed_database

    # Limpiar datos existentes antes de crear nuevos
    python manage.py seed_database --clear

    # Solo crear servicios
    python manage.py seed_database --only-services

    # Solo crear leads
    python manage.py seed_database --only-leads

    # Solo crear usuarios
    python manage.py seed_database --only-users

DATOS QUE CREA:
    SERVICIOS (5):
    - Aerotermia
    - Aire Acondicionado
    - Domótica KNX
    - Instalaciones Eléctricas
    - Reformas Integrales

    USUARIOS (3):
    - maria_oficina (rol: office) - Personal de oficina
    - carlos_tecnico (rol: field) - Técnico de campo
    - jorge_tecnico (rol: field) - Técnico de campo

    LEADS (5):
    - Varios estados: nuevo, contactado, presupuestado, cerrado
    - Varios orígenes: web, teléfono, recomendación
    - Con asignaciones y presupuesto de ejemplo

FLUJO DE EJECUCIÓN:
    1. Parsear argumentos (--clear, --only-*)
    2. Si --clear: eliminar datos existentes
    3. Crear servicios (si aplica)
    4. Crear usuarios (si aplica)
    5. Crear leads con relaciones (si aplica)
    6. Mostrar resumen de operaciones

NOTAS:
    - Usa transaction.atomic() para rollback si algo falla
    - get_or_create evita duplicados al ejecutar múltiples veces
    - El superusuario NUNCA se elimina (protección con --clear)
    - Los UserProfile se crean automáticamente via signal

===============================================================================
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from apps.services.models import Service
from apps.leads.models import Lead, Budget
from apps.users.models import UserProfile


class Command(BaseCommand):
    """
    Management command para poblar la base de datos con datos de prueba.

    HERENCIA:
        Extiende BaseCommand de Django para integrarse con manage.py.

    ATRIBUTOS:
        help: Descripción que aparece en 'python manage.py help seed_database'

    MÉTODOS PRINCIPALES:
        add_arguments: Define los argumentos CLI disponibles
        handle: Lógica principal del comando
        _create_services: Crea servicios de ejemplo
        _create_users: Crea usuarios con perfiles
        _create_leads: Crea leads con relaciones
    """

    help = 'Pobla la base de datos con datos de prueba para desarrollo'

    def add_arguments(self, parser):
        """
        Define los argumentos de línea de comandos.

        ARGUMENTOS:
            --clear: Elimina datos existentes antes de crear nuevos.
                    Útil para resetear la base de datos a un estado conocido.

            --only-services: Solo crea servicios, ignora usuarios y leads.
                           Útil cuando solo se necesita el catálogo.

            --only-leads: Solo crea leads (requiere usuarios existentes).
                         Útil para probar el CRM con más datos.

            --only-users: Solo crea usuarios, ignora servicios y leads.
                         Útil para probar permisos y roles.

        PARÁMETROS:
            parser: ArgumentParser de Django para registrar argumentos.
        """
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpia los datos existentes antes de crear nuevos',
        )
        parser.add_argument(
            '--only-services',
            action='store_true',
            help='Solo crea servicios',
        )
        parser.add_argument(
            '--only-leads',
            action='store_true',
            help='Solo crea leads',
        )
        parser.add_argument(
            '--only-users',
            action='store_true',
            help='Solo crea usuarios',
        )

    def handle(self, *args, **options):
        """
        Punto de entrada principal del comando.

        FLUJO:
            1. Extraer opciones de la línea de comandos
            2. Determinar qué crear (todo o específico)
            3. Dentro de transacción atómica:
               a. Limpiar datos si --clear
               b. Crear servicios si aplica
               c. Crear usuarios si aplica
               d. Crear leads si aplica
            4. Mostrar mensaje de éxito

        PARÁMETROS:
            *args: Argumentos posicionales (no usados)
            **options: Diccionario con valores de los argumentos definidos

        NOTA:
            transaction.atomic() asegura que si algo falla,
            todos los cambios se revierten (rollback).
        """
        clear = options['clear']
        only_services = options['only_services']
        only_leads = options['only_leads']
        only_users = options['only_users']

        # Si no se especifica ningún --only, crear todos
        create_all = not any([only_services, only_leads, only_users])

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('  SEED DATABASE - ARYNSTAL SL'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        with transaction.atomic():
            # -----------------------------------------------------------------
            # Paso 1: Limpiar datos si se solicita
            # -----------------------------------------------------------------
            if clear:
                self.stdout.write(self.style.WARNING('\n🗑️  Limpiando datos existentes...'))
                if create_all or only_leads:
                    Budget.objects.all().delete()
                    Lead.objects.all().delete()
                    self.stdout.write('  ✓ Presupuestos y Leads eliminados')
                if create_all or only_services:
                    Service.objects.all().delete()
                    self.stdout.write('  ✓ Servicios eliminados')
                if create_all or only_users:
                    # IMPORTANTE: No eliminar el superusuario
                    User.objects.filter(is_superuser=False).delete()
                    self.stdout.write('  ✓ Usuarios no-admin eliminados')

            # -----------------------------------------------------------------
            # Paso 2: Crear servicios
            # -----------------------------------------------------------------
            if create_all or only_services:
                self.stdout.write(self.style.SUCCESS('\n📦 Creando servicios...'))
                self._create_services()

            # -----------------------------------------------------------------
            # Paso 3: Crear usuarios
            # -----------------------------------------------------------------
            if create_all or only_users:
                self.stdout.write(self.style.SUCCESS('\n👥 Creando usuarios...'))
                self._create_users()

            # -----------------------------------------------------------------
            # Paso 4: Crear leads
            # -----------------------------------------------------------------
            if create_all or only_leads:
                self.stdout.write(self.style.SUCCESS('\n📋 Creando leads...'))
                self._create_leads()

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('✅ Base de datos poblada correctamente'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

    def _create_services(self):
        """
        Crea servicios de ejemplo para el catálogo.

        SERVICIOS CREADOS:
            1. Aerotermia - Climatización eficiente
            2. Aire Acondicionado - Instalación y mantenimiento
            3. Domótica KNX - Control inteligente del hogar
            4. Instalaciones Eléctricas - Certificaciones
            5. Reformas Integrales - Llave en mano

        COMPORTAMIENTO:
            - Usa get_or_create para evitar duplicados
            - Muestra ✓ si creó, ⚠ si ya existía
            - Informa del total creado al final
        """
        services_data = [
            {
                "name": "Aerotermia",
                "short_description": "Climatización eficiente con aerotermia",
                "description": "Instalación completa de sistemas de aerotermia para climatización eficiente y sostenible de tu hogar o negocio.",
                "icon": "heat-pump",
                "is_active": True,
                "order": 1
            },
            {
                "name": "Aire Acondicionado",
                "short_description": "Instalación y mantenimiento de AC",
                "description": "Instalación, mantenimiento y reparación de sistemas de aire acondicionado de todas las marcas.",
                "icon": "air-conditioner",
                "is_active": True,
                "order": 2
            },
            {
                "name": "Domótica KNX",
                "short_description": "Control inteligente de tu hogar",
                "description": "Diseño e implementación de sistemas de domótica KNX para control total de tu vivienda.",
                "icon": "smart-home",
                "is_active": True,
                "order": 3
            },
            {
                "name": "Instalaciones Eléctricas",
                "short_description": "Instalaciones eléctricas certificadas",
                "description": "Instalaciones eléctricas completas para viviendas, oficinas y naves industriales.",
                "icon": "electrical",
                "is_active": True,
                "order": 4
            },
            {
                "name": "Reformas Integrales",
                "short_description": "Reformas completas llave en mano",
                "description": "Reformas integrales de viviendas y locales comerciales con todas las instalaciones incluidas.",
                "icon": "renovation",
                "is_active": True,
                "order": 5
            },
        ]

        count = 0
        for data in services_data:
            service, created = Service.objects.get_or_create(
                name=data["name"],
                defaults=data
            )
            if created:
                count += 1
                self.stdout.write(f'  ✓ {service.name}')
            else:
                self.stdout.write(f'  ⚠ {service.name} (ya existía)')

        self.stdout.write(self.style.SUCCESS(f'  Total: {count} servicios creados'))

    def _create_users(self):
        """
        Crea usuarios de ejemplo con diferentes roles.

        USUARIOS CREADOS:
            1. maria_oficina (office) - Personal de oficina
               - Puede gestionar leads y crear presupuestos

            2. carlos_tecnico (field) - Técnico de campo
               - Acceso limitado, ve sus leads asignados

            3. jorge_tecnico (field) - Técnico de campo
               - Acceso limitado, ve sus leads asignados

        FLUJO:
            1. Crear User con get_or_create
            2. Si es nuevo, establecer contraseña con set_password()
            3. El signal crea UserProfile automáticamente
            4. Actualizar rol y teléfono del perfil

        NOTA SOBRE CONTRASEÑAS:
            Las contraseñas son simples (ej: "maria123") solo para pruebas.
            NUNCA usar contraseñas así en producción.
        """
        users_data = [
            {
                "username": "maria_oficina",
                "email": "maria@arynstal.com",
                "first_name": "María",
                "last_name": "García",
                "password": "maria123",
                "role": "office",
                "phone": "612345001"
            },
            {
                "username": "carlos_tecnico",
                "email": "carlos@arynstal.com",
                "first_name": "Carlos",
                "last_name": "Rodríguez",
                "password": "carlos123",
                "role": "field",
                "phone": "612345002"
            },
            {
                "username": "jorge_tecnico",
                "email": "jorge@arynstal.com",
                "first_name": "Jorge",
                "last_name": "Martínez",
                "password": "jorge123",
                "role": "field",
                "phone": "612345003"
            },
        ]

        count = 0
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                }
            )
            if created:
                # Establecer contraseña (se hashea automáticamente)
                user.set_password(data["password"])
                user.save()
                # El signal post_save ya creó el UserProfile
                # Solo necesitamos actualizar rol y teléfono
                user.profile.role = data["role"]
                user.profile.phone = data["phone"]
                user.profile.save()
                count += 1
                self.stdout.write(f'  ✓ {user.get_full_name()} ({user.profile.get_role_display()})')
            else:
                self.stdout.write(f'  ⚠ {user.username} (ya existía)')

        self.stdout.write(self.style.SUCCESS(f'  Total: {count} usuarios creados'))

    def _create_leads(self):
        """
        Crea leads de ejemplo con diferentes estados y relaciones.

        LEADS CREADOS:
            1. Juan Pérez - Nuevo (web) - Aerotermia
            2. María González - Contactado (web) - Aire Acondicionado
            3. Pedro Martínez - Presupuestado (teléfono) - Domótica KNX
            4. Ana Rodríguez - Nuevo (recomendación) - Sin servicio específico
            5. Luis Fernández - Cerrado (teléfono) - Aire Acondicionado

        RELACIONES:
            - Algunos leads tienen servicio asignado
            - Algunos leads tienen usuario asignado (maria_oficina)
            - El lead "presupuestado" tiene un Budget asociado

        PROPÓSITO:
            Proporciona datos variados para probar:
            - Filtros del admin (por estado, urgencia, origen)
            - Asignación de leads a usuarios
            - Flujo completo: nuevo → contactado → presupuestado → cerrado
        """
        # Obtener servicios y usuarios existentes
        aerotermia = Service.objects.filter(name="Aerotermia").first()
        aire = Service.objects.filter(name="Aire Acondicionado").first()
        domotica = Service.objects.filter(name="Domótica KNX").first()
        maria = User.objects.filter(username="maria_oficina").first()

        leads_data = [
            {
                "name": "Juan Pérez García",
                "email": "juan.perez@email.com",
                "phone": "612345678",
                "location": "Barcelona",
                "service": aerotermia,
                "message": "Buenos días, me gustaría recibir un presupuesto para la instalación de aerotermia en una vivienda unifamiliar de 150m². La casa es de nueva construcción.",
                "status": "nuevo",
                "source": "web",
                "privacy_accepted": True
            },
            {
                "name": "María González López",
                "email": "maria.gonzalez@empresa.com",
                "phone": "687654321",
                "location": "Hospitalet de Llobregat",
                "service": aire,
                "message": "Necesito presupuesto para instalación de aire acondicionado en una oficina de 100m². Preferiblemente sistema split de 3 unidades.",
                "status": "contactado",
                "assigned_to": maria,
                "source": "web",
                "privacy_accepted": True
            },
            {
                "name": "Pedro Martínez",
                "email": "pedro.m@gmail.com",
                "phone": "654321987",
                "location": "Barcelona",
                "service": domotica,
                "message": "Hola, estoy interesado en instalar domótica KNX en mi vivienda. Es una reforma integral y me gustaría automatizar iluminación, persianas y climatización.",
                "status": "presupuestado",
                "assigned_to": maria,
                "source": "telefono",
                "privacy_accepted": True
            },
            {
                "name": "Ana Rodríguez",
                "email": "ana.rodriguez@hotmail.com",
                "phone": "699887766",
                "location": "Sant Boi",
                "message": "Querría información sobre vuestros servicios de instalación eléctrica. Es para una nave industrial de 300m².",
                "status": "nuevo",
                "source": "recomendacion",
                "privacy_accepted": True
            },
            {
                "name": "Luis Fernández",
                "email": "luis.fernandez@yahoo.es",
                "phone": "677554433",
                "location": "Cornellà",
                "service": aire,
                "message": "Buenas tardes, necesito reparación urgente de aire acondicionado. Ha dejado de funcionar y tenemos ola de calor.",
                "status": "cerrado",
                "assigned_to": maria,
                "source": "telefono",
                "privacy_accepted": True
            },
        ]

        count = 0
        for data in leads_data:
            lead, created = Lead.objects.get_or_create(
                email=data["email"],
                defaults=data
            )
            if created:
                count += 1
                status_emoji = {
                    'nuevo': '🆕',
                    'contactado': '📞',
                    'presupuestado': '💰',
                    'cerrado': '✅',
                    'descartado': '❌'
                }
                self.stdout.write(
                    f'  {status_emoji.get(lead.status, "·")} '
                    f'{lead.name} - {lead.get_status_display()}'
                )
            else:
                self.stdout.write(f'  ⚠ {data["name"]} (ya existía)')

        # -----------------------------------------------------------------
        # Crear presupuesto de ejemplo
        # -----------------------------------------------------------------
        # Para demostrar el flujo completo, creamos un presupuesto
        # asociado al lead que está en estado "presupuestado"

        if count > 0:
            lead_presupuestado = Lead.objects.filter(status='presupuestado').first()
            if lead_presupuestado:
                budget, created = Budget.objects.get_or_create(
                    lead=lead_presupuestado,
                    defaults={
                        'description': 'Instalación completa de domótica KNX en vivienda unifamiliar',
                        'amount': 8500.00,
                        'status': 'enviado',
                        'created_by': maria
                    }
                )
                if created:
                    self.stdout.write(
                        f'  💰 Presupuesto creado: {budget.reference} - {budget.amount}€'
                    )

        self.stdout.write(self.style.SUCCESS(f'  Total: {count} leads creados'))
