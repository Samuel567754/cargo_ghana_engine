# bookings/apps.py
from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class BookingsConfig(AppConfig):
    name = 'bookings'

    def ready(self):
        # Delay import until Django is fully loaded
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        from . import tasks

        try:
            # Milestones every hour
            sched_hourly, _ = CrontabSchedule.objects.get_or_create(
                minute='0', hour='*'
            )
            PeriodicTask.objects.update_or_create(
                name='Milestone Check',
                defaults={
                    'crontab': sched_hourly,
                    'task': 'bookings.tasks.check_milestones_and_notify',
                }
            )

            # Dispatch check every 15 minutes
            sched_15, _ = CrontabSchedule.objects.get_or_create(
                minute='*/15', hour='*'
            )
            PeriodicTask.objects.update_or_create(
                name='Dispatch Ready Check',
                defaults={
                    'crontab': sched_15,
                    'task': 'bookings.tasks.notify_dispatch_ready',
                }
            )

        # On first migrate, beat tables may not yet exist
        except (OperationalError, ProgrammingError):
            pass
