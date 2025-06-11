from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'tasks'

urlpatterns = [
    path('create/',views.CreateTaskView.as_view(), name='create_task'),
    path('invite/accept/', views.AcceptInvitation.as_view(), name='accept_invitation'),
    path('invite/member/', views.InviteMember.as_view(), name='invite_member'),
    path('members/', views.Members.as_view(), name='members'),
    path('freelancer/',views.MyTask.as_view(), name='my_task'),
    path('freelancer/<uuid:uuid>/',views.TaskDetail.as_view(), name='task_detail'),
    path('freelancer/edit/<uuid:uuid>/', views.UpdateTaskView.as_view(), name='edit_task'),
    path('freelancer/pending_task/', views.PendingTask.as_view(),name='pending_task'),


    path('subtasks/create/<uuid:task_uuid>/', views.CreateSubTaskView.as_view(), name='create_subtask'),
    path('<uuid:task_uuid>/subtasks/<uuid:subtask_uuid>/toggle_status/', views.UpdateSubTaskStatusView.as_view(), name='update_subtask_status'),
    path('<uuid:task_uuid>/subtasks/<uuid:subtask_uuid>/edit/', views.UpdateSubTaskView.as_view(), name='edit_subtask'),

    path('client/', views.ClientTasksView.as_view(), name='client_tasks'),
    path('client/<uuid:uuid>/',views.ClientTaskDetail.as_view(), name='client_taskdetail'),
    path('client/incoming_invitations/', views.IncomingInvitation.as_view(), name='incoming_invitations'),

    


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)