from django.db.models.signals import post_save
from django.dispatch import receiver
from Tasks.models import Task,ScheduleTask,Invitation
from django.utils import timezone
from datetime import datetime
from Interactions.utils import create_notification



@receiver(post_save, sender=Task)
def create_or_update_schedule_task(sender, instance, created, **kwargs):
    if not instance.deadline:
        return

    # Handle str-to-date conversion
    deadline_value = instance.deadline
    print(f"Deadline value: {deadline_value}")
    if isinstance(deadline_value, str):
        try:
            deadline_value = datetime.strptime(deadline_value, "%Y-%m-%d").date()
        except ValueError:
            print(f"[!] Invalid deadline format: {instance.deadline}")
            return

    # Convert to timezone-aware datetime
    deadline_datetime = timezone.datetime.combine(deadline_value, timezone.datetime.min.time())
    if timezone.is_naive(deadline_datetime):
        deadline_datetime = timezone.make_aware(deadline_datetime)

    if deadline_datetime <= timezone.now():
        print(f"[!] Skipping ScheduleTask: deadline is in the past.")
        return

    if created:
        if not ScheduleTask.objects.filter(task=instance).exists():
            ScheduleTask.objects.create(
                task=instance,
                scheduled_time=deadline_datetime,
                notification_type='email',
            )
    else:
        try:
            schedule = ScheduleTask.objects.get(task=instance)
            if schedule.scheduled_time != deadline_datetime:
                schedule.scheduled_time = deadline_datetime
                schedule.status = 'scheduled'
                schedule.save()
        except ScheduleTask.DoesNotExist:
            ScheduleTask.objects.create(
                task=instance,
                scheduled_time=deadline_datetime,
                notification_type='email',
            )


# @receiver(post_save, sender=Invitation)
# def invitation_sent(sender, instance, created, **kwargs):
#     if created:
#         create_notification(
#             recipient=instance.member,
#             actor=instance.task.freelancer,
#             verb="invited you to",
#             target=instance.task.title,
#             url=f"/tasks/client/taskdetail/{instance.task.id}/")