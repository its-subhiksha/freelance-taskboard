from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'interactions'


urlpatterns =  [
    path('task/<int:task_id>/', views.task_chat_view, name='task_chat'),
    path('tasks/<int:task_id>/notes/', views.NotesBoardView.as_view(), name='task_notes'),
    path('notes/create/', views.CreateNoteView.as_view(), name='create_note'),
    path('notes/<int:pk>/autosave/', views.UpdateNoteView.as_view(), name='note_autosave'),
    path('notifications/', views.FetchNotifications.as_view(), name='fetch_notifications'),

    path('calendar/', views.CalendarPageView.as_view(), name='calendar'),
    path('calendar/events/', views.CalendarEventsAPI.as_view(), name='calendar_events'),
    

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)