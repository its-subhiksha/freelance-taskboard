from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    has_freelanced = models.BooleanField(default=False)
    has_cliented = models.BooleanField(default=False)

    def role_summary(self):
        roles = []
        if self.has_freelanced:
            roles.append("Freelancer")
        if self.has_cliented:
            roles.append("Client")
        return " & ".join(roles) if roles else "No activity yet"