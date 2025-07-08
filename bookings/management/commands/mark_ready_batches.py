from django.core.management.base import BaseCommand
from bookings.models import ContainerBatch

class Command(BaseCommand):
    help = "Mark any open ContainerBatch as 'ready' once its target volume is reached."

    def handle(self, *args, **options):
        open_batches = ContainerBatch.objects.filter(status='open')
        for batch in open_batches:
            if batch.current_volume >= batch.target_volume:
                batch.status = 'ready'
                batch.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Batch #{batch.id} marked ready "
                        f"({batch.current_volume} / {batch.target_volume} m³)."
                    )
                )
            else:
                self.stdout.write(
                    f"Batch #{batch.id} not ready: "
                    f"{batch.current_volume:.2f} / {batch.target_volume} m³."
                )
