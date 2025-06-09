import django.utils.timezone as timezone
from Tasks.models import Invitation,Task


# changing the status from pending to expired
def expire_invitations():
    now = timezone.now()
    expired_invitations = Invitation.objects.filter(
        expires_on__lte=now,  
        status=Invitation.InvitationStatus.PENDING  
    )
    expired_count = expired_invitations.update(status=Invitation.InvitationStatus.EXPIRED)
    return f"Expired {expired_count} invitations."
