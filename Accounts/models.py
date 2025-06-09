from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    has_freelanced = models.BooleanField(default=False)
    has_cliented = models.BooleanField(default=False)

     # Shared
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    def role_summary(self):
        roles = []
        if self.has_freelanced:
            roles.append("Freelancer")
        if self.has_cliented:
            roles.append("Client")
        return " & ".join(roles) if roles else "No activity yet"