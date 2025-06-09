from Interactions.models import Notification
from django.utils import timezone


def create_notification(recipient, actor=None, verb="", target="", url=None):
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        target=target,
        url=url
    )