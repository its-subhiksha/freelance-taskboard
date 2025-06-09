import os
from celery import Celery
from django.utils import timezone
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freelance_taskboard.settings")

app = Celery("freelance_taskboard", broker_connection_retry_on_startup =True)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.update(
    timezone="UTC",
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
)


app.conf.beat_schedule = {
    "minute_5": {
        "task": "Coresystem.tasks.CronFiveMinute",
        "schedule":timezone.timedelta(minutes=1),
    }
}

app.autodiscover_tasks() 