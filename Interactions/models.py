from django.db import models
from Tasks.models import Task
from Accounts.models import CustomUser
from django.utils import timezone

# Create your models here.
class Message(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content}'
    

class UserNotes(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"
    


class RevisionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='revision_requests')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revision by {self.client.username} on {self.task.title} - {self.status}"


class Notification(models.Model):
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='actor_notifications', null=True, blank=True)
    verb = models.CharField(max_length=255)  # e.g., 'assigned you a task'
    target = models.CharField(max_length=255, null=True, blank=True)  # e.g., 'Task #42'
    url = models.URLField(null=True, blank=True)  # Link to the related object
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.actor} {self.verb} {self.target}'