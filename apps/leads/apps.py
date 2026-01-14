from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.leads'

    def ready(self):
        """Importar signals cuando la app esté lista"""
        import apps.leads.signals
