from django.urls import re_path
from Interactions.consumers import ChatConsumer,NotesConsumer

websocket_urlpatterns = [
    re_path(r'ws/task/(?P<task_id>\d+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/notes/(?P<task_id>\d+)/$',NotesConsumer.as_asgi()),
]