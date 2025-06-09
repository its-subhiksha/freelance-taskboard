from django.db import models
from Accounts.models import CustomUser
from django.utils import timezone
# Create your models here.

class AuthTokens(models.Model):
    class TokenType(models.IntegerChoices):
        VERIFYSIGNUP = 1, 'Verify Sign Up'
        LOGIN = 2, 'Login'
        PASSWORD_RESET = 3, 'Password Reset'
        INVITATION = 4, 'Invitation'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True, blank=True)
    token = models.CharField(max_length=255,unique=True)
    auth_type = models.IntegerField(choices=TokenType.choices)
    is_valid = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField()

    def is_valid_token(self):
        return self.is_valid and self.expires_on > timezone.now()