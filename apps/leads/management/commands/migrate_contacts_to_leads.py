from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Migra los datos de ContactRequest (web) a Lead (leads). OBSOLETO: web no tiene modelos.'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.ERROR(
                'Este comando está obsoleto. La app "web" no tiene modelos '
                '(ContactRequest, ContactRequestImage). Los leads se gestionan '
                'en apps.leads. Si necesitas migrar datos de otro sistema, '
                'crea un nuevo comando que use apps.leads.models.'
            )
        )
