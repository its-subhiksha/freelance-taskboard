from django.db import models
from django.conf import settings
from Accounts.models import CustomUser
from Coresystem.models import AuthTokens

# Create your models here.

class Task(models.Model):
    STATUS_CHOICES = [
        ('awaiting', 'Awaiting Client Approval'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),  
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateField()
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='freelancer_tasks')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_tasks',null=True, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='awaiting')
    created_at = models.DateTimeField(auto_now_add=True)


class SubTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'), 
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,default='pending')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"



class Invitation(models.Model):
    class InvitationStatus(models.IntegerChoices):
        PENDING = 1, 'Pending'
        ACCEPTED = 2, 'Accepted'
        REJECTED = 3, 'Rejected'
        EXPIRED = 4, 'Expired'
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='invitations')
    invited_email = models.EmailField(null=True, blank=True)
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.IntegerField(choices=InvitationStatus.choices,default=InvitationStatus.PENDING)
    auth_token = models.ForeignKey(AuthTokens, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return f"{self.invited_email} - {self.task.title}"
    



class ScheduleTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='deadline_schedule')
    scheduled_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[('scheduled', 'Scheduled'), ('completed', 'Completed')],
        default='scheduled'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('in_app', 'In-App'), ('sms', 'SMS')],
        default='email'
    )

    def __str__(self):
        return f"Deadline for {self.task.title} at {self.scheduled_time}"


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachements')
    file = models.FileField(upload_to='tasks/attachments/', null=True, blank=True)
    original_name = models.CharField(max_length=255,null=True,blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = self.file.name
        super().save(*args, **kwargs)


class Activity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"