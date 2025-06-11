from django.contrib import admin
from Tasks.models import Task, SubTask, Invitation,ScheduleTask,TaskAttachment, Activity
# Register your models here.


admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(Invitation)
admin.site.register(ScheduleTask)
admin.site.register(TaskAttachment)
admin.site.register(Activity)