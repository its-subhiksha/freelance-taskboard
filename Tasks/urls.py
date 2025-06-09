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
    path('freelancer/my_task/',views.MyTask.as_view(), name='my_task'),
    path('freelancer/taskdetail/<int:task_id>/',views.TaskDetail.as_view(), name='task_detail'),
    path('<int:task_id>/edit/', views.UpdateTaskView.as_view(), name='edit_task'),


    path('<int:task_id>/subtasks/create/', views.CreateSubTaskView.as_view(), name='create_subtask'),
    path('<int:task_id>/subtasks/<int:subtask_id>/toggle_status/', views.UpdateSubTaskStatusView.as_view(), name='update_subtask_status'),
    path('<int:task_id>/subtasks/edit/', views.UpdateSubTaskView.as_view(), name='edit_subtask'),

    path('client/my-tasks/', views.ClientTasksView.as_view(), name='client_tasks'),
    path('client/taskdetail/<int:task_id>/',views.ClientTaskDetail.as_view(), name='client_taskdetail'),
    path('client/incoming_invitations/', views.IncomingInvitation.as_view(), name='incoming_invitations'),

    


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)