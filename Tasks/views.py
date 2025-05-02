from django.shortcuts import render,redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from Tasks.models import Task, Invitation
from Coresystem.models import AuthTokens
from Accounts.models import CustomUser
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from Coresystem.security import AuthtokenGenerator,is_valid_email,is_ping_valid,isnt_temp_domain
from django.http import JsonResponse

# Create your views here.

@method_decorator(login_required(login_url="/accounts/login/"),name='dispatch')
class CreateTaskView(View):
    def get(self,request):
        return render(request, "Tasks/create_task.html")
    def post(self,request):
        title = request.POST.get("title")
        description = request.POST.get("description")
        deadline = request.POST.get("deadline")
        attachement = request.FILES.get("attachment")
        print("attachement",attachement)
        client_email = request.POST.get("client_email")

        result = is_valid_email.delay(client_email.lower())
        is_valid = result.get()  # This will block until the task completes
        print("is_valid",is_valid)
        
        if not is_valid:
            print("comes under is not valid email")
            return JsonResponse({"message": "Invalid Email, please enter correct email"}, status=400)

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
            attachement_files=attachement,
            freelancer = request.user,
            client = client if client_registered else None,
            status = 'awaiting')
        
        # generate Authtoken

        token_generator = AuthtokenGenerator(token_type=AuthTokens.TokenType.INVITATION, user_id=request.user.id)
        auth_token = token_generator.IssueAuthToken()


        #  create Invitation

        Invitation.objects.create(
            task = task,
            invited_email = client_email,
            member = request.user,
            status = Invitation.InvitationStatus.PENDING,
            auth_token = AuthTokens.objects.get(token=auth_token),
            expires_on = token_generator.get_token_expiry_time(AuthTokens.TokenType.INVITATION)
        )

 
        invite_link = f"http://yourdomain.com/invite/accept?token={auth_token}&task_id={task.id}"
        print(f"Send this invite link to {client_email}: {invite_link}")

        return redirect('/accounts/freelancer/dashboard/')