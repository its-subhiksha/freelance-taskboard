import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freelance_taskboard.settings")

app = Celery("freelance_taskboard")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()