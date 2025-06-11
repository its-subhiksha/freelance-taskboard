from django.contrib import admin
from Interactions.models import UserNotes, Message, RevisionRequest, Notification


admin.register(UserNotes)
admin.register(Message)
admin.register(RevisionRequest)
admin.register(Notification)

