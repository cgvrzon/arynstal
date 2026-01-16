"""
===============================================================================
ARCHIVO: conftest.py
PROYECTO: Arynstal - Sistema CRM para gestión de instalaciones y reformas
AUTOR: @cgvrzon
===============================================================================

DESCRIPCIÓN:
    Configuración global de pytest para el proyecto.
    Define fixtures reutilizables en todos los tests.

FIXTURES DISPONIBLES:
    - client: Cliente HTTP para tests de vistas
    - user: Usuario de prueba con perfil
    - admin_user: Usuario superadmin
    - service: Servicio de prueba
    - lead: Lead de prueba

USO:
    def test_example(client, user):
        client.force_login(user)
        response = client.get('/contact/')
        assert response.status_code == 200

===============================================================================
"""

import pytest
from django.contrib.auth.models import User


@pytest.fixture
def user(db):
    """
    Crea un usuario normal con perfil para tests.

    El signal post_save crea automáticamente el UserProfile.
    """
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    # El perfil se crea automáticamente via signal
    user.profile.role = 'office'
    user.profile.save()
    return user


@pytest.fixture
def admin_user(db):
    """
    Crea un superusuario para tests de admin.
    """
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def service(db):
    """
    Crea un servicio de prueba.
    """
    from apps.services.models import Service
    return Service.objects.create(
        name='Test Service',
        short_description='Descripción corta de prueba',
        description='Descripción larga del servicio de prueba para tests.',
        is_active=True,
        order=1
    )


@pytest.fixture
def lead(db, service):
    """
    Crea un lead de prueba con servicio asociado.
    """
    from apps.leads.models import Lead
    return Lead.objects.create(
        name='Lead de Prueba',
        email='lead@example.com',
        phone='612345678',
        location='Barcelona',
        service=service,
        message='Este es un mensaje de prueba para el lead. Tiene más de 20 caracteres.',
        status='nuevo',
        source='web',
        urgency='normal',
        privacy_accepted=True
    )


@pytest.fixture
def lead_form_data(service):
    """
    Datos válidos para el formulario de contacto.
    """
    return {
        'name': 'Juan Pérez',
        'email': 'juan@example.com',
        'phone': '612345678',
        'location': 'Barcelona',
        'service': service.id if service else '',
        'message': 'Este es un mensaje de prueba con más de 20 caracteres para validación.',
        'privacidad': 'on',
    }
