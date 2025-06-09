from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.conf import settings
from Tasks.models import Invitation
from Accounts.models import CustomUser

class DashboardAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Block unauthenticated access to any dashboard-related pages
        if 'dashboard' in request.path:
            if not request.user.is_authenticated:
                return redirect('/accounts/login/')
        
        # Prefill email if user is visiting an invitation link
        if '/accept' in request.path_info and 'task_id' in request.GET:
            token = request.GET.get('token')
            task_id = request.GET.get('task_id')

            try:
                # Look up the invitation
                invitation = Invitation.objects.select_related('auth_token','member').get(auth_token__token=token, task_id=task_id)

                email = None
                
                
                email = invitation.invited_email
                print(f"Prefilling email: {email}")

                if email:
                    email = email.lower()
                    user_exists = CustomUser.objects.filter(email=email).only("id").first()
                    if user_exists:
                        request.session['login_hint_email'] = email
                    else:
                        request.session['signup_hint_email'] = email

            except Exception as e:
                print(f"Middleware failed to prefill invite email: {e}")

        
        # Always return a response
        return self.get_response(request)
