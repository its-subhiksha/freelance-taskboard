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
    attachement_files = models.FileField(upload_to='tasks/attachments/', blank=True, null=True)
    deadline = models.DateField()
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='freelancer_tasks')
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_tasks',null=True, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='awaiting')
    created_at = models.DateTimeField(auto_now_add=True)


class Invitation(models.Model):
    class InvitationStatus(models.IntegerChoices):
        PENDING = 1, 'Pending'
        ACCEPTED = 2, 'Accepted'
        REJECTED = 3, 'Rejected'
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='invitations')
    invited_email = models.EmailField()
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=20,choices=InvitationStatus.choices,default=InvitationStatus.PENDING)
    auth_token = models.ForeignKey(AuthTokens, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return f"{self.invited_email} - {self.task.title}"