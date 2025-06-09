from .CronJob import (
    expire_invitations,
)

from celery import shared_task


@shared_task
def CronFiveMinute():
    expire_invitations()

    return "Completed"