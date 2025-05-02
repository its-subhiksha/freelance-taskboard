from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'tasks'

urlpatterns = [
    path('create/',views.CreateTaskView.as_view(), name='create_task'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)