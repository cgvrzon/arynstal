from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import ContactRequest, ContactRequestImage
from leads.models import Lead, LeadImage


class Command(BaseCommand):
    help = 'Migra los datos de ContactRequest (web) a Lead (leads)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la migración sin guardar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        # Obtener todos los ContactRequest
        contact_requests = ContactRequest.objects.all()
        total = contact_requests.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay ContactRequest para migrar'))
            return

        self.stdout.write(f'Encontrados {total} registros de ContactRequest para migrar')

        migrated = 0
        errors = 0

        with transaction.atomic():
            for cr in contact_requests:
                try:
                    # Verificar si ya existe un Lead con el mismo email y teléfono
                    existing_lead = Lead.objects.filter(
                        email=cr.email,
                        phone=cr.telefono
                    ).first()

                    if existing_lead:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠ Ya existe un Lead para {cr.nombre} ({cr.email}). Saltando...'
                            )
                        )
                        continue

                    # Crear nuevo Lead
                    lead = Lead(
                        name=cr.nombre,
                        email=cr.email,
                        phone=cr.telefono,
                        message=cr.descripcion,
                        source='web',
                        status=cr.status if cr.status in dict(Lead.STATUS_CHOICES) else 'nuevo',
                        assigned_to=cr.assigned_to,
                        notes=cr.internal_notes,
                        privacy_accepted=True,  # Asumimos que aceptó privacidad al enviar
                        created_at=cr.created_at,
                        updated_at=cr.updated_at
                    )

                    if not dry_run:
                        lead.save()

                    # Migrar imágenes asociadas
                    images = ContactRequestImage.objects.filter(contact_request=cr)
                    for img in images:
                        lead_image = LeadImage(
                            lead=lead,
                            image=img.image,
                            uploaded_at=img.uploaded_at
                        )
                        if not dry_run:
                            lead_image.save()

                    migrated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Migrado: {cr.nombre} ({images.count()} imágenes)'
                        )
                    )

                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error al migrar {cr.nombre}: {str(e)}'
                        )
                    )

            # Si es dry-run, hacer rollback
            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING('\nDRY-RUN: Todos los cambios fueron revertidos')
                )

        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Migración completada:'))
        self.stdout.write(f'  Total registros: {total}')
        self.stdout.write(self.style.SUCCESS(f'  Migrados exitosamente: {migrated}'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'  Con errores: {errors}'))
        self.stdout.write('='*60)

        if not dry_run and migrated > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✓ Los datos fueron migrados correctamente.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'NOTA: Los modelos ContactRequest y ContactRequestImage antiguos '
                    'aún existen en la base de datos. Puedes eliminarlos manualmente '
                    'después de verificar que todo funciona correctamente.'
                )
            )
