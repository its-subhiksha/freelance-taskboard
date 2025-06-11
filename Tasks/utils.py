# tasks/utils.py
from Tasks.models import Invitation,Task
from Coresystem.models import AuthTokens
from Accounts.models import CustomUser
from Interactions.models import Notification
from Coresystem.security import AuthtokenGenerator, is_valid_email
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
import os

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'gif','txt','doc','docx','csv','ppt','webp','tiff']


def new_invitation(task, email, user):
    print("comes under the new invitation")
    token_generator = AuthtokenGenerator(
        token_type=AuthTokens.TokenType.INVITATION,
        user_id=user.id if user else None
    )
    auth_token = token_generator.issue_new_token()
    auth_token_obj = AuthTokens.objects.get(token=auth_token)
    expires_on = auth_token_obj.expires_on

    invitation = Invitation.objects.create(
        task=task,
        invited_email=email,
        member=user if user else None,
        status=Invitation.InvitationStatus.PENDING,
        auth_token=auth_token_obj,
        expires_on=expires_on
    )

    invite_link = f"http://freelancetaskboard.com:8000/tasks/invite/accept?token={auth_token}&task_uuid={task.uuid}"
    print(f"Invitation link: {invite_link}")
    return invite_link

def resend_invitation(invitation):
    print("comes under the resend invitation")

    auth_token_obj = invitation.auth_token
    if not auth_token_obj:
        return None

    # Extend expiry (e.g., another 10 minutes from now)
    new_expiry = timezone.now() + timezone.timedelta(minutes=10)
    auth_token_obj.expires_on = new_expiry
    auth_token_obj.save()

    invitation.expires_on = new_expiry
    invitation.save()

    invite_link = f"http://freelancetaskboard.com:8000/tasks/invite/accept?token={auth_token_obj.token}&task_uuid={invitation.task.uuid}"
    print(f"Invitation link: {invite_link}")
    return invite_link

def reinvite_invitation(invitation):
    print("comes under the reinvite invitation")

    user = invitation.member if invitation.member else None
    generator = AuthtokenGenerator(
        token_type=AuthTokens.TokenType.INVITATION,
        user_id=user.id if user else None
    )

    # Update the existing AuthToken object with a new token and expiry
    updated_token = generator.update_existing_token(invitation.auth_token)
    updated_expiry = invitation.auth_token.expires_on

    invitation.expires_on = updated_expiry
    invitation.status = Invitation.InvitationStatus.PENDING
    invitation.save()

    invite_link = f"http://freelancetaskboard.com:8000/tasks/invite/accept?token={updated_token}&task_uuid={invitation.task.uuid}"
    print(f"Re-invited link: {invite_link}")
    return invite_link

class RoleManager:
    def __init__(self, task, user=None, email=None):
        self.task = task
        self.user = user
        self.email = email

    def remove_role(self):
        print("comes under the remove role")

        self.remove_task()
        self.remove_invitation()
        # self.remove_authtoken(task, user, email)
        return True
    
    def remove_task(self):
        print("comes under the remove task")

        print(f"Task: {self.task}")
        print(f"User: {self.user}")
        print(f"Email: {self.email}")

        task_obj = Task.objects.filter(id=self.task.id).first()
        if task_obj:
            task_obj.delete()
            return True
        return False
    
    def remove_invitation(self):
        print("comes under the remove invitation")

        print(f"Task: {self.task}")
        print(f"User: {self.user}")
        print(f"Email: {self.email}")

        if self.user:
            invitation = Invitation.objects.filter(task=self.task, member=self.user).first()
        elif self.email:
            invitation = Invitation.objects.filter(task=self.task, invited_email=self.email).first()

        if not self.user and not self.email:
            print("No user or email provided for invitation removal.")
            return False

        auth_token_id = invitation.auth_token if invitation else None

        auth_token_obj = AuthTokens.objects.filter(id=auth_token_id, auth_type=AuthTokens.TokenType.INVITATION).first()
        if auth_token_obj:
            auth_token_obj.delete()


        if invitation:
            invitation.delete()
            return True
        return False
    
    
def is_allowed_file(file):
    ext = os.path.splitext(file.name)[1][1:].lower()
    return ext in ALLOWED_EXTENSIONS


