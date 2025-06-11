from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from Tasks.models import Task, Invitation,ScheduleTask,TaskAttachment,SubTask,Activity
from Coresystem.models import AuthTokens
from Accounts.models import CustomUser
from Interactions.models import Message,RevisionRequest,UserNotes,Notification
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from Coresystem.security import AuthtokenGenerator,is_valid_email,is_ping_valid,isnt_temp_domain,AuthTokenValidator
from django.http import JsonResponse
from django.utils import timezone
from Tasks.utils import new_invitation, resend_invitation, reinvite_invitation, is_valid_email,RoleManager,is_allowed_file
from Interactions.utils import create_notification
from datetime import datetime
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
# Create your views here.

@method_decorator(login_required(login_url="/login/"),name='dispatch')
class CreateTaskView(View):
    def get(self,request):
        return render(request, "Tasks/create_task.html")
    def post(self,request):
        title = request.POST.get("title")
        description = request.POST.get("description")
        deadline = request.POST.get("deadline")
        attachement = request.FILES.getlist("attachment")
        print("attachement",attachement)
        client_email = request.POST.get("client_email")

        if not title or not description or not client_email:
            return JsonResponse({"error": "Please fill all the required fields."}, status=400)
            

        try:
            result = is_valid_email.delay(client_email.lower())
            is_valid = result.get(timeout=10)
        except Exception as e:
            print("Email validation failed:", e)
            return JsonResponse({"error": "Could not validate email."}, status=500)
        
        if not is_valid:
            print("comes under is not valid email")
            return JsonResponse({"message": "Invalid Email, please enter correct email"}, status=400)
        
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
            if deadline_date < timezone.now().date():
                return JsonResponse({"error": "Deadline cannot be in the past."}, status=400)
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)
        
        
        # checking if the client already have an account to get his user id
        try:
            client = CustomUser.objects.get(email=client_email)
            client_registered = True
        except CustomUser.DoesNotExist:
            client_registered = False
            client = None

        # Creatinf the tasks

        task = Task.objects.create(
            title = title,
            description = description,
            deadline = deadline,
            freelancer = request.user,
            client = client if client_registered else None,
            status = 'awaiting')
        
        valid_files = [f for f in attachement if is_allowed_file(f)]
        if not valid_files and attachement:
            task.delete()
            return JsonResponse({"error": "All attachments are invalid."}, status=400)

        for file in valid_files:
            try:
                TaskAttachment.objects.create(task=task, file=file)
            except Exception as e:
                print(f"Failed to save file {file.name}: {e}")

        try:
            new_invitation(task, client_email, request.user)
        except Exception as e:
            print("Invitation generation failed:", e)
            task.delete()
            return JsonResponse({"error": "Failed to create invitation."}, status=500)

        # Send notification to client if they have an account
        if client_registered:
            print("comes under the client registered")
            print("client",client)
            print("task",task)
            print("request.user",request.user)
            print("creating notification for the client")
            create_notification(
                recipient=client,
                actor=request.user,
                verb="invited you to join his Project:",
                target=task.title,
                url=reverse('tasks:client_taskdetail', kwargs={'uuid': task.uuid})
            )
        Activity.objects.create(
            user=request.user,
            message=f"You created a task '{title}' and invited {client_email}"
        )

        # return redirect('/accounts/freelancer/dashboard/')
        return render(request, "Tasks/create_task.html", {
                "success_message": "Task created and invitation sent!"
            })

    
class InviteMember(View):
    def post(self, request):
        email = request.POST.get("email")
        print("email",email)
        # task_id = request.POST.get("task_id")
        # print("task_id",task_id)

        task_uuid = request.POST.get("task_uuid")
        print("task_uuid",task_uuid)


        status = request.POST.get("status")
        print("status",status)

        if not email or not task_uuid or not status:
            print("comes under the missing required fields")
            return JsonResponse({"message": "Missing required fields"}, status=400)

        # Get the task
        task = get_object_or_404(Task, uuid=task_uuid)

        try:
            if status == "New":
                print("comes under the new invite")
                return self.handle_new_invite(email, task)
            elif status == "Pending":
                print("comes under the resend invite")
                return self.handle_resend(email, task)
            elif status == "Expired":
                print("comes under the reinvite")
                return self.handle_reinvite(email, task)
            else:
                return JsonResponse({"message": "Invalid status provided"}, status=400)
        except Exception as e:
            print(f"Invite Error: {e}")
            return JsonResponse({"message": "Something went wrong"}, status=500)
        
        return redirect("Tasks:members.html")

    def handle_new_invite(self, email, task):
        # Validate email
        try:
            result = is_valid_email.delay(email.lower())
            is_valid = result.get(timeout=10)
        except Exception as e:
            print("Email validation failed:", e)
            return JsonResponse({"message": "Email validation service failed"}, status=500)

        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = None
        except Exception as e:
            print("Error fetching user:", e)
            return JsonResponse({"message": "Something went wrong while checking user."}, status=500)

        # Check if already invited
        if Invitation.objects.filter(task=task, invited_email=email, status__in=[1, 4]).exists():
            return JsonResponse({"message": "User already invited (pending or expired)"}, status=400)

        # Issue new invitation
        try:
            invitation, link = new_invitation(task=task, email=email, user=user)
        except Exception as e:
            print("Failed to create invitation:", e)
            return JsonResponse({"message": "Could not create invitation."}, status=500)        
        
        return redirect('tasks:members') 

    def handle_resend(self, email, task):
        invitation = Invitation.objects.filter(task=task, invited_email=email, status=Invitation.InvitationStatus.PENDING).first()
        if not invitation:
            return JsonResponse({"message": "No pending invitation found"}, status=404)
        link = resend_invitation(invitation)
        print("link",link)

        if link:
            create_notification(
                recipient=email,
                actor=request.user,
                verb="invited you to join his Project:",
                target=task.title,
                url=reverse('tasks:client_taskdetail', kwargs={'uuid': task.uuid}),
            )

            Activity.objects.create(
                user=request.user,
                message=f"You created a task '{task.title}' and invited {task.client_email}"
            )


        return redirect('tasks:members') 

    def handle_reinvite(self, email, task):
        invitation = Invitation.objects.filter(task=task, invited_email=email, status=Invitation.InvitationStatus.EXPIRED).first()
        if not invitation:
            return JsonResponse({"message": "No expired invitation found"}, status=404)
        link = reinvite_invitation(invitation)
        print("link",link)

        if link:
            create_notification(
                recipient=email,
                actor=request.user,
                verb="invited you to join his Project:",
                target=task.title,
                url=reverse('tasks:client_taskdetail', kwargs={'uuid': task.uuid}),
            )

            Activity.objects.create(
                user=request.user,
                message=f"You created a task '{task.title}' and invited {task.client_email}"
            )

        return redirect('tasks:members') 

class AcceptInvitation(View):
    def get(self, request):
        token_str = request.GET.get('token')
        print("token_str",token_str)
        task_uuid = request.GET.get('task_uuid')
        # task_id = request.GET.get('task_id')
        print("task_id",task_uuid)

        if not token_str or not task_uuid:
            return JsonResponse({"message": "Invalid invitation link."}, status=400)

        # Validate the token
        token_obj = AuthTokenValidator(token_str, expected_type=AuthTokens.TokenType.INVITATION)
        print("Token validity:", token_obj.is_valid_token())
        print("Token status:", token_obj.auth_type, token_obj.token)
        if not token_obj or not token_obj.is_valid_token():
            return JsonResponse({"message": "This invitation link is invalid or has expired."}, status=400)

        # Check if the user is authenticated
        if not request.user.is_authenticated:
            # Store the next URL and redirect to login
            request.session['next_url'] = request.get_full_path()
            return redirect('accounts:login')

        # Retrieve the invitation
        invitation = get_object_or_404(Invitation, auth_token=token_obj, task_id=task_id)
        print("invitation",invitation)
        print("invitation status",invitation.status)

        # Check if the invitation has already been accepted
        try:
            invitation = Invitation.objects.get(auth_token=token_obj, task_id=task_id)
        except Invitation.DoesNotExist:
            return JsonResponse({"message": "Invalid invitation or task."}, status=404)
        
        # Update the invitation status and associate it with the user
        invitation.status = Invitation.InvitationStatus.ACCEPTED
        invitation.save()

        task = get_object_or_404(Task, uuid=task_uuid)
        task.status = 'in_progress'


        if task.client is None:
            try:
                # Match invited email with logged-in user's email
                if invitation.invited_email.lower() == request.user.email.lower():
                    task.client = request.user
                    print("Updated task.client to logged-in user.")
            except Exception as e:
                print(f"Error updating task.client: {e}")
        
        task.save()

        # Invalidate the token
        token_obj.is_valid = False
        try:
            token_obj.save()
        except Exception as e:
            print("Failed to invalidate token:", e)

        # Create a notification for the user
        create_notification(
            recipient=task.freelancer,  # notify the freelancer, not the client
            actor=task.client,         # the client accepting the invite
            verb="accepted your invitation",
            target=task.title,
            url=reverse('tasks:client_taskdetail', kwargs={'uuid': task.uuid})
        )

        Activity.objects.create(
            user=request.user,
            message=f"You accepted the invitation to task '{task.title}'"
        )

        # Activity.objects.create(
        #     user=task.freelancer,
        #     message=f"Client accepted your task invitation for '{task.title}'"
        # )

        return redirect('accounts:dashboard')

class Members(View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('accounts:login')
        
                # Get all invitations for the logged-in user
        invitations = Invitation.objects.filter(member=user).select_related('task')

        invitation_data = []
        for invite in invitations:
            invitation_data.append({
                'email': invite.invited_email,
                'task_title': invite.task.title,
                'task_id': invite.task.id,
                'status': invite.get_status_display()
            })

        context = {
            'invitations': invitation_data
        }

        return render(request, 'Tasks/members.html', context)
    
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('accounts:login')
        
        user_id = request.POST.get("user_id")
        print("user_id",user_id)
        task_id = request.POST.get("task_id")
        print("task_id",task_id)
        action = request.POST.get("action")
        print("action",action)
        email = request.POST.get("email")
        print("email",email)

        if not (user_id or email) or not task_id:
            # messages.error(request, "Invalid request: Missing user ID or email, or task ID.")
            # return redirect('tasks:members')
            return JsonResponse({'success': False, 'error': "Missing user ID or email, or task ID."})

        
        try:
            task = Task.objects.get(id=task_id)
            print("task",task)
        except Task.DoesNotExist:
            # messages.error(request, "Task not found.")
            # return redirect('tasks:members')
            return JsonResponse({'success': False, 'error': "Task not found."})
        
        if action == "remove":
            print("comes under the remove action")

            # if user_id:
            #     RoleManager.remove_role(task, user_id)
            # elif email:
            #     RoleManager.remove_role(task, email)

            result = RoleManager(task=task, email=email).remove_role()
            if result:
                create_notification(
                    recipient=email,
                    actor=request.user,
                    verb="Removed you from his Project:",
                    target=task.title,
                    url=f"/tasks/client/taskdetail/{task.id}/"
                )

                Activity.objects.create(
                    user=request.user,
                    message=f"You have Removed the '{email}' from the task {title}"
                )

            if not result:
                # messages.error(request, "Failed to remove role.")
                # return redirect('tasks:members')
                return JsonResponse({'success': False, 'error': "Failed to remove role."})

            # return redirect('tasks:members')
            return JsonResponse({'success': True})


@method_decorator(login_required,name='dispatch')  
class MyTask(View):
     def get(self, request):
        user = request.user
        tasks = Task.objects.filter(freelancer=user).exclude(status='awaiting').order_by('-created_at')

        VALID_STATUSES = ['in_progress', 'under_review', 'completed']

        # Filtering
        status_filter = request.GET.get('status')
        print("status_filter",status_filter)
        if status_filter:
            tasks = tasks.filter(status=status_filter)

        if status_filter and status_filter not in VALID_STATUSES:
            return JsonResponse({"message": "Invalid status filter."}, status=400)

        # Sorting
        sort_by = request.GET.get('sort')
        print("sort_by",sort_by)
        if sort_by == 'sooner':
            print("comes under the sooner")
            tasks = tasks.order_by('deadline')
        elif sort_by == 'later':
            print("comes under the later")
            tasks = tasks.order_by('deadline')
        elif sort_by and sort_by not in ['sooner', 'later']:
            print("Invalid sort option. Ignoring.")

        if not tasks.exists():
            print("No tasks found for user.")

        context = {
            'tasks': tasks,
            'status_filter': status_filter,
            'sort_by': sort_by,
        }
        return render(request, 'Tasks/my_task.html', context)

class PendingTask(View):
    def get(self, request):
        user = request.user
        tasks = Task.objects.filter(freelancer=user,status='awaiting').order_by('-created_at')

        # VALID_STATUSES = ['awaiting']

        # # Filtering
        # status_filter = request.GET.get('status')
        # print("status_filter",status_filter)
        # if status_filter:
        #     tasks = tasks.filter(status=status_filter)

        # if status_filter and status_filter not in VALID_STATUSES:
        #     return JsonResponse({"message": "Invalid status filter."}, status=400)

        # Sorting
        # sort_by = request.GET.get('sort')
        # print("sort_by",sort_by)
        # if sort_by == 'sooner':
        #     print("comes under the sooner")
        #     tasks = tasks.order_by('deadline')
        # elif sort_by == 'later':
        #     print("comes under the later")
        #     tasks = tasks.order_by('deadline')
        # elif sort_by and sort_by not in ['sooner', 'later']:
        #     print("Invalid sort option. Ignoring.")

        if not tasks.exists():
            print("No tasks found for user.")

        context = {
            'tasks': tasks,
            # 'status_filter': status_filter,
            # 'sort_by': sort_by,
        }
        return render(request, 'Tasks/pending_task.html', context)


        
@method_decorator(login_required,name='dispatch')
class TaskDetail(View):
    def get(self, request, uuid):

        task = get_object_or_404(Task, uuid=uuid,freelancer=request.user)
        task_messages = Message.objects.filter(task=task).order_by('timestamp')
        attachments = task.attachements.all() if hasattr(task, 'attachements') else []
        revision_requests = task.revision_requests.all().order_by('-created_at') if hasattr(task, 'revision_requests') else []

        context = {
            'task': task,
            'attachments': attachments,
            'task_messages': task_messages,
            'revision_requests': revision_requests,
        }

        return render(request, "Tasks/task_detail.html", context)
    
    def post(self, request, uuid):
        task = get_object_or_404(Task, uuid=uuid, freelancer=request.user)
        print("task",task)

        if 'attachment' in request.FILES:
            files = request.FILES.getlist('attachment')
            for file in files:
                if is_allowed_file(file):
                    TaskAttachment.objects.create(task=task, file=file)
                else:
                    print(f"Unsupported file type skipped: {file.name}")
                    messages.error(request,"Invalid file type")
                    return redirect('tasks:task_detail', uuid=uuid)
        else:
            print("No attachments provided.")
    
        try:
            attachment_id = int(request.POST.get('delete_attachment_id'))
        except (ValueError, TypeError):
            attachment_id = None

        print("attachment_id",attachment_id)
        if attachment_id:
            try:
                attachment = get_object_or_404(TaskAttachment, id=int(attachment_id), task=task)
                attachment.file.delete(save=False)
                attachment.delete()
            except (ValueError, TaskAttachment.DoesNotExist):
                print("Invalid or missing attachment ID")
                messages.error(request, "Invalid or missing attachment ID")
                return redirect('tasks:task_detail')


        # Submit task for review
        if 'submit_task' in request.POST:
            task.status = 'under_review'
            task.save()
            Activity.objects.create(
                user=request.user,
                message=f"You submitted '{task.title}' for review"
            )

            return redirect('tasks:my_task')

        try:
            revision_id = int(request.POST.get('revision_id'))
        except (ValueError, TypeError):
            revision_id = None

        if revision_id:
            try:
                revision = get_object_or_404(RevisionRequest, id=revision_id, task=task)
                revision.status = 'completed'
                revision.save()
            except RevisionRequest.DoesNotExist:
                messages.error(request, "Revision not found for completion.")
                print("Revision not found for completion.")
                return redirect('tasks:task_detail')
                # return JsonResponse({"message": "Invalid revision ID."}, status=404)

        return redirect('tasks:task_detail',uuid = uuid)

@method_decorator(login_required, name='dispatch')
class UpdateTaskView(View):
    def post(self, request, uuid):
        title = request.POST.get("title")
        description = request.POST.get("description")
        deadline = request.POST.get("deadline")

        if not title or not description or not deadline:
            # messages.error(request, "All fields are required")
            return JsonResponse({'success': False, 'error': "All fields are required."})
            # return JsonResponse({"message": "All fields are required."}, status=400)
            # return redirect("tasks:task_detail")

        try:
            parsed_deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        except ValueError:
            # messages.error(request,"Invalid deadline format. Use YYYY-MM-DD.")
            return JsonResponse({'success': False, 'error': "Invalid deadline format"})
            # return JsonResponse({"message": "Invalid deadline format. Use YYYY-MM-DD."}, status=400)

        if parsed_deadline < timezone.now().date():
            return JsonResponse({'success': False, 'error': "Due date cannot be in the past."})
            # messages.error(request,"Deadline cannot be in the past")
            # return JsonResponse({"message": "Deadline cannot be in the past."}, status=400)

        try:
            task = get_object_or_404(Task, uuid=uuid, freelancer=request.user)

            task.title = request.POST.get("title")
            task.description = request.POST.get("description")
            task.deadline = request.POST.get("deadline")
            task.save()

            Activity.objects.create(
                user=request.user,
                message=f"You Updated the Task '{task.title}'."
            )

        except Exception as e:
            print(f"Error updating task: {e}")
            return JsonResponse({'success': False, 'error': "Failed to update task"})
            # messages.error(request,"Failed to update task")
            # return JsonResponse({"message": "Failed to update task."}, status=500)

        # return redirect("tasks:task_detail", task_id=task_id)
        return JsonResponse({'success': True})
    
@method_decorator(login_required, name='dispatch')
class CreateSubTaskView(View):
    # def get(self, request, task_id):
    #     task = get_object_or_404(Task, id=task_id, freelancer=request.user)
    #     return render(request, "Tasks/subtask.html", {'task': task})

    def post(self, request, task_uuid):
        task = get_object_or_404(Task, uuid=task_uuid, freelancer=request.user)
        title = request.POST.get('title')
        print("title",title)
        description = request.POST.get('description')
        print("description",description)
        due_date = request.POST.get('due_date')

        if not title or not description or not due_date:
            # messages.error(request,"Please fill all required fields.")
            # return redirect('tasks:task_detail', task_id=task.id)
            return JsonResponse({'success': False, 'error': "Please fill all required fields."})

        try:
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            # messages.error(request,"Invalid due date format.")
            # return redirect('tasks:task_detail', task_id=task.id)
            return JsonResponse({'success': False, 'error': "Invalid due date format."})

        if due < timezone.now().date():
            # messages.error(request,"Due date cannot be in the past.")
            # return redirect('tasks:task_detail', task_id=task.id)
            return JsonResponse({'success': False, 'error': "Due date cannot be in the past."})


        try:
            subTask = SubTask.objects.create(
                task=task,
                title=title,
                description=description,
                due_date=due,
                status='pending'
            )

            if subTask:

                create_notification(
                    recipient=task.client,
                    actor=request.user,
                    verb=f"Has created a New Subtask Under the {task.title} Project ",
                    target=task.title,
                    url=f"/tasks/client/taskdetail/{task.id}/"
                )
                Activity.objects.create(
                    user=request.user,
                    message=f"You have created a New Subtask Under the  '{task.title}' Project"
                )

        except Exception as e:
            print(f"Failed to create subtask: {e}")
            # messages.error(request,"Subtask creation failed")
            return JsonResponse({'success': False, 'error': "Subtask creation failed."})

        
        print("Created SubTask:", subTask)
        # return redirect('tasks:task_detail', task_id=task.id)
        return JsonResponse({'success': True})
    
class UpdateSubTaskStatusView(View):
    def post(self, request, task_uuid, subtask_uuid):
        task = get_object_or_404(Task, uuid=task_uuid, freelancer=request.user)
        subtask = get_object_or_404(SubTask, uuid=subtask_uuid, task=task)
        # Check if the request is to delete the subtask
        if 'delete_subtask' in request.POST:
            subtask.delete()  # Delete the subtask
            return redirect('tasks:task_detail', uuid=task_uuid)

        # Otherwise, update the status
        new_status = request.POST.get('status')
        if not new_status or new_status not in ['pending', 'in_progress', 'completed']:
            # messages.error(request,"Invalid status value")
            return JsonResponse({'success': False, 'error': "Invalid status value"})
            # return JsonResponse({"message": "Invalid status value."}, status=400)
        try:
            subtask.status = new_status
            subtask.save()

            create_notification(
                    recipient=task.client,
                    actor=request.user,
                    verb=f"Has Updated the Subtask Status Under the {task.title} Project ",
                    target=task.title,
                    url=f"/tasks/client/taskdetail/{task.id}/"
                )
            Activity.objects.create(
                user=request.user,
                message=f"You have Updated the Subtask Status Under the {task.title} Project"
            )
        except Exception as e:
            print(f"Failed to update subtask status: {e}")
            return JsonResponse({'success': False, 'error': "Could not update subtask"})
            # messages.error(request,"Could not update subtask.")
            # return JsonResponse({"message": "Could not update subtask."}, status=500)
        
        # return redirect('tasks:task_detail', task_id=task_id)
        # return JsonResponse({'success': True})
        return redirect('tasks:task_detail', uuid=task_uuid)

class UpdateSubTaskView(View):
    def post(self, request, task_uuid, subtask_uuid):
        title = request.POST.get("title")
        description = request.POST.get("description")
        due_date = request.POST.get("due_date")

        if not title or not description or not due_date:
            return JsonResponse({'success': False, 'error': "All fields are required."})

        try:
            parsed_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({'success': False, 'error': "Invalid due date format"})

        if parsed_date < timezone.now().date():
            return JsonResponse({'success': False, 'error': "Due date cannot be in the past."})

        subtask = get_object_or_404(SubTask, uuid=subtask_uuid, task__uuid=task_uuid)

        try:
            subtask.title = title
            subtask.description = description
            subtask.due_date = parsed_date
            subtask.save()

            # Retrieve the client from the task
            client = subtask.task.client  # Assuming the task has a client attribute

            if subtask:
                create_notification(
                    recipient=client,
                    actor=request.user,
                    verb=f"Has Updated Subtask Under the {subtask.task.title} Project ",
                    target=subtask.task.title,
                    url=f"/tasks/client/taskdetail/{subtask.task.id}/"
                )
                Activity.objects.create(
                    user=request.user,
                    message=f"You have Updated the Subtask Under the '{subtask.task.title}' Project"
                )
        except Exception as e:
            print(f"Failed to update subtask: {e}")
            return JsonResponse({'success': False, 'error': "Failed to update subtask."})

        return JsonResponse({'success': True})

@method_decorator(login_required, name='dispatch')
class ClientTasksView(View):
    def get(self, request):

        tasks = Task.objects.filter(
            client=request.user,
            status__in=['in_progress', 'under_review', 'completed']
        ).order_by('-created_at')  # Order by creation date, most recent first
        print("client_tasks",tasks)

        # Filtering
        status_filter = request.GET.get('status')
        print("status_filter",status_filter)
        if status_filter:
            tasks = tasks.filter(status=status_filter)

        # Sorting
        sort_by = request.GET.get('sort')
        print("sort_by",sort_by)

        if sort_by and sort_by not in ['sooner', 'later']:
            print("Invalid sort type ignored.")

        if sort_by == 'sooner':
            print("comes under the sooner")
            tasks = tasks.order_by('deadline')
        elif sort_by == 'later':
            print("comes under the later")
            tasks = tasks.order_by('deadline')
        
        if not tasks.exists():
            print("No tasks found for client.")

        context = {
            'tasks': tasks,
            'status_filter': status_filter,
            'sort_by': sort_by,
        }
        return render(request, 'Tasks/client_task.html',context)


@method_decorator(login_required,name='dispatch')
class ClientTaskDetail(View):
    def get(self, request,uuid):

        task = get_object_or_404(Task, uuid=uuid,client=request.user)
        task_messages = Message.objects.filter(task=task).order_by('timestamp')
        attachments = [
            {
                'url': attachment.file.url,
                'name': attachment.original_name
            }
            for attachment in task.attachements.all()
        ]
        revision_requests = task.revision_requests.all().order_by('-created_at')

        context = {
            'task': task,
            'attachments': attachments,
            'task_messages': task_messages,
            'revision_requests': revision_requests,
        }

        return render(request, "Tasks/client_taskdetail.html", context)
    
    def post(self, request, uuid):
        task = get_object_or_404(Task, uuid=uuid, client=request.user)
        print("task",task)
        action = request.POST.get('action')
        print("action",action)

        revision_comment = request.POST.get('revision_comment', '').strip()
        print("revision_comment",revision_comment)

        if not action or action not in ['approve', 'request_revision']:
            messages.error(request,"Invalid action")
            # return JsonResponse({"message": "Invalid action."}, status=400)

        if action == 'approve' and task.status == 'completed':
            messages.error(request,"Task is already approved.")

            # return JsonResponse({"message": "Task is already approved."}, status=400)
        
        if action == 'request_revision' and not revision_comment:  # Define revision_comment here
            messages.error(request, "Please provide a revision comment.")
            return redirect('tasks:client_taskdetail', uuid=task.uuid)
            # return JsonResponse({"message": "Revision comment required."}, status=400)


        if action == 'approve':
            task.status = 'completed'
            task.save()
            
            Activity.objects.create(
                user=request.user,
                message=f"You approved the task '{task.title}'"
            )
            Activity.objects.create(
                user=task.freelancer,
                message=f"Client approved your task '{task.title}'"
            )
            create_notification(
                    recipient=task.freelancer,
                    actor=task.client,
                    verb=f"Has Approved your {task.title} Project ",
                    target=task.title,
                    url=f"/tasks/client/taskdetail/{task.uuid}/"
                )


            messages.success(request, "Task approved successfully.")
            return redirect('tasks:client_taskdetail', uuid=task.uuid)

        elif action == 'request_revision':

            # Save the revision comment to the database
            RevisionRequest.objects.create(task=task, comment=revision_comment,client=request.user,status='pending')
            task.status = 'in_progress'
            task.save()
            Activity.objects.create( 
                user=request.user,
                message=f"You requested a revision for task '{task.title}'"
            )
            Activity.objects.create(
                user=task.freelancer,
                message=f"Client requested a revision on '{task.title}'"
            )

            create_notification(
                recipient=task.freelancer,
                actor=task.client,
                verb=f"Has requested a Revision for the {task.title} Project ",
                target=task.title,
                url=f"/tasks/client/taskdetail/{task.uuid}/"
            )
            
            messages.success(request, "Revision requested successfully.")
            return redirect('tasks:client_taskdetail', uuid=task.uuid)

        # Handle unexpected actions
        # messages.error(request, "Invalid action.")
        return redirect('tasks:client_taskdetail', uuid=task.uuid)
    
class IncomingInvitation(View):
    def get(self, request):
        task = Task.objects.filter(client=request.user, status='awaiting')

        print("task",task)

        invitations = Invitation.objects.filter(
            task__in=task, 
            invited_email=request.user.email,
            status=Invitation.InvitationStatus.PENDING,
            )
        
        print("invitations",invitations)

        context = {
            'invitations': invitations,
            'tasks': task,
            }
        return render(request, 'Tasks/incoming_invitation.html', context)

    def post(self, request):
        invitation_id = request.POST.get("invitation_id")
        print("invitation_id",invitation_id)
        if not invitation_id:
            messages.error(request,"Invalid request")
            # return JsonResponse({"message": "Invalid request"}, status=400)

        # Step 1: Get invitation and validate ownership
        invitation = get_object_or_404(
            Invitation, 
            id=invitation_id,
            invited_email=request.user.email,
            status=Invitation.InvitationStatus.PENDING
        )
        print("invitation",invitation)
        if invitation.task.client != request.user:
            messages.error(request,"You are not authorized to accept this invitation.")
            return JsonResponse({"message": "You are not authorized to accept this invitation."}, status=403)
        
        print("invitation.task.client",invitation.task.client)
        print("request.user",request.user)

        # Step 2: Update invitation status
        invitation.status = Invitation.InvitationStatus.ACCEPTED
        invitation.save()

        # Step 3: Update task
        task = invitation.task
        task.status = 'in_progress'
        if task.client is None:
            task.client = request.user
        task.save()

        # Optional: Invalidate the token
        if invitation.auth_token:
            invitation.auth_token.is_valid = False
            invitation.auth_token.save()


        Activity.objects.create(
            user=request.user,
            message=f"You accepted an invitation to collaborate on task '{task.title}'"
        )

        create_notification(
            recipient=task.freelancer,
            actor=request.user,
            verb="accepted your invitation to collaborate on",
            target=task.title,
            url=f"/tasks/client/taskdetail/{task.uuid}/"
        )


        return redirect('tasks:incoming_invitations')
    
