from django.shortcuts import render,redirect,reverse
from Accounts.serializers import RegisterSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from Accounts.permissions import IsFreelancer, IsClient
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate,login,logout
from django.views import View
from Accounts.models import CustomUser
from Tasks.models import Task,Activity, Invitation
from datetime import timedelta
from django.utils import timezone
import json
from django.contrib import messages
from django.http import JsonResponse 
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail


# Create your views here.
@method_decorator(login_required(login_url='/login/'), name='dispatch')
class UserDashboard(View):
    def get(self, request):
        user = request.user
        total_tasks = Task.objects.filter(freelancer=user).count() or 1  # Avoid divide-by-zero

        in_progress_count = Task.objects.filter(freelancer=user, status='in_progress').count()
        review_count = Task.objects.filter(freelancer=user, status='under_review').count()
        completed_count = Task.objects.filter(freelancer=user, status='completed').count()
        recent_activity = Activity.objects.filter(user=request.user).order_by('-timestamp')[:5]
        now = timezone.now().date()
        next_week = now + timedelta(days=7)

        tasks_in_next_week = Task.objects.filter(
            freelancer=user,
            created_at__range=(now, next_week)
        ).count()

        # Alerts
        upcoming_deadlines = Task.objects.filter(
            freelancer=user,
            deadline__range=[now, next_week],
            status__in=['in_progress', 'under_review']
        )

        pending_invites = Invitation.objects.filter(
            task__freelancer=user,
            status=Invitation.InvitationStatus.PENDING
        )

        incomplete_tasks = Task.objects.filter(
            freelancer=user,
            status__in=['in_progress', 'under_review']
        )

        approval_needed = Task.objects.filter(
            client=user,
            status='under_review'
        )

        # Get 7-day completion trend
        labels = []
        data = []
        for i in range(6, -1, -1):
            day = timezone.now().date() - timedelta(days=i)
            labels.append(day.strftime("%a"))  # e.g. 'Tue', 'Wed'
            count = Task.objects.filter(freelancer=request.user, status='completed', deadline=day).count()
            data.append(count)
            print("labels",labels)
            print("data",data)
        context = {
            'total_tasks': total_tasks,
            'in_progress_count': in_progress_count,
            'review_count': review_count,
            'completed_count': completed_count,
            'in_progress_percent': int((in_progress_count / total_tasks) * 100),
            'review_percent': int((review_count / total_tasks) * 100),
            'completed_percent': int((completed_count / total_tasks) * 100),
            'recent_activity': recent_activity,
            'upcoming_deadlines': upcoming_deadlines,
            'pending_invites': pending_invites,
            'incomplete_tasks': incomplete_tasks,
            'approval_needed': approval_needed,
            'task_completion_labels': json.dumps(labels),
            'task_completion_data': json.dumps(data),
        }
        return render(request, 'Accounts/dashboard.html', context)

@method_decorator(login_required(login_url='/login/'), name='dispatch')
class ClientDashboard(View):
    def get(self, request):
        context = {'user': request.user}
        return render(request, 'Accounts/client.html', context)

@method_decorator(login_required(login_url='/login/'), name='dispatch')
class FreelancerDashboard(View):
    def get(self, request):
        context = {'user': request.user}
        return render(request, 'Accounts/freelance.html', context)


class RegisterView(View):
    def get(self, request):
        initial_email = request.session.pop('signup_hint_email', None) or ""
        print(f"Initial email: {initial_email}")
        return render(request, 'Accounts/register.html', {'initial_email': initial_email})
    def post(self, request):
        username = request.POST.get("username")
        print("username",username)
        email = request.POST.get("email")
        print("email",email)
        password = request.POST.get("password")
        print("password",password)

        if not username or not email or not password:
            return JsonResponse({"error": "All fields are required."}, status=400)

        if CustomUser.objects.filter(username=username).exists():
            return render(request, "Accounts/register.html", {"error": "Username already taken."})

        if CustomUser.objects.filter(email=email).exists():
            return render(request, "Accounts/register.html", {"error": "Email already in use."})

        user = CustomUser.objects.create_user(username=username, email=email, password=password)
        print("user",user)
        login(request, user)  
        next_url = request.session.pop('next_url', None)
        print("next_url",next_url)
        if next_url:
            print("comes under the next url found in register")
            return redirect(next_url)
        return redirect("/dashboard/")
        # return redirect(reverse('dashboard', kwargs={'username': user.username}))


class LoginView(View):

    def get(self, request):
        initial_email = request.session.pop('login_hint_email', None) or ""
        print(f"Initial email: {initial_email}")
        return render(request, 'Accounts/login.html', {'initial_email': initial_email})
    def post(self,request):
        email = request.POST.get('email')
        print("email",email)
        password = request.POST.get('password')
        print("password",password)

        if not email or not password:
            return JsonResponse({"error": "Email and password are required."}, status=400)


        try:
            user_obj = CustomUser.objects.get(email__iexact=email)
            print("user_obj",user_obj)
        except CustomUser.DoesNotExist:
            return render(request, 'Accounts/login.html', {
                'error': 'Email not found',
                'initial_email': email
            })

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            login(request,user)

            next_url = request.session.pop('next_url', None)
            print("next_url",next_url)
            if next_url:
                print("comes under the next url found in login")
                return redirect(next_url)
            return redirect("/dashboard/")
        else:
            print("comes under the invalid username or password")
            return render(request, 'Accounts/login.html', {'error': 'Invalid username or password.'})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("/login/")


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        return render(request, self.template_name, {'user': request.user})

    def post(self, request):
        user = request.user
        data = request.POST
        files = request.FILES

         # Use existing values as fallback for missing inputs
        first_name = data.get('first_name', user.first_name).strip()
        last_name = data.get('last_name', user.last_name).strip()
        email = data.get('email', user.email).strip()
        phone_number = data.get('phone_number', user.phone_number).strip()
        bio = data.get('bio', user.bio).strip()
        website = data.get('website', user.website).strip()
        linkedin_url = data.get('linkedin_url', user.linkedin_url).strip()
        location = data.get('location', user.location).strip()

        # Validate email
        if email:
            try:
                validate_email(email)
                if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                    # messages.error(request, 'This email is already in use by another account.')
                    # return redirect('accounts:profile')
                    return JsonResponse({'success': False, 'error': "This email is already in use by another account"})
            except ValidationError:
                # messages.error(request, 'Please enter a valid email address.')
                # return redirect('accounts:profile')
                return JsonResponse({'success': False, 'error': "Please enter a valid email address."})
        else:
            # messages.error(request, 'Email field cannot be empty.')
            # return redirect('accounts:profile')
            return JsonResponse({'success': False, 'error': "Email field cannot be empty."})

        # Validate phone number (basic check)
        if phone_number and not phone_number.isdigit():
            # messages.error(request, 'Phone number must contain only digits.')
            # return redirect('accounts:profile')
            return JsonResponse({'success': False, 'error': "Phone number must contain only digits."})

        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        user.bio = bio
        user.website = website
        user.linkedin_url = linkedin_url
        user.location = location

        # Handle profile photo upload
        if 'profile_photo' in files:
            profile_photo = files['profile_photo']
            if profile_photo.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
                # messages.error(request, 'Unsupported file type for profile photo. Please upload JPEG, PNG, or GIF images.')
                # return redirect('accounts:profile')
                return JsonResponse({'success': False, 'error': "Unsupported file type for profile photo. Please upload JPEG, PNG, or GIF images."})
            if profile_photo.size > 5 * 1024 * 1024:  # 5MB limit
                # messages.error(request, 'Profile photo size should not exceed 5MB.')
                # return redirect('accounts:profile')
                return JsonResponse({'success': False, 'error': "Profile photo size should not exceed 5MB."})
            user.profile_photo = profile_photo

        # Save the updated user information
        try:
            user.save()
            Activity.objects.create(
                user=request.user,
                message=f"You updated your profile successfully"
            )

            # return redirect('accounts:profile')
            # messages.success(request, 'Profile updated successfully.')
            return JsonResponse({'success': True})
        except Exception as e:
            # messages.error(request, f'An error occurred while updating your profile: {str(e)}')
            return JsonResponse({'success': False, 'error': "An error occurred while updating your profile"})

        



class ForgotPasswordView(View):
    def get(self, request):
        return render(request, 'Accounts/forgot_password.html')

    def post(self, request):
        email = request.POST.get('email')
        if not email:
            return render(request, 'Accounts/forgot_password.html', {'error': "Email is required."})

        try:
            user = CustomUser.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(f'/accounts/reset-password/{uid}/{token}/')

            send_mail(
                'Reset your password',
                f'Click the link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return render(request, 'Accounts/forgot_password.html', {'success': "Password reset link sent to your email."})
        except CustomUser.DoesNotExist:
            return render(request, 'Accounts/forgot_password.html', {'error': "Email not found."})


class ResetPasswordView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return render(request, 'Accounts/reset_password.html', {'validlink': True, 'uidb64': uidb64, 'token': token})
        except Exception:
            pass
        return render(request, 'Accounts/reset_password.html', {'validlink': False})

    def post(self, request, uidb64, token):
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if not password or not confirm:
            return render(request, 'Accounts/reset_password.html', {'validlink': True, 'uidb64': uidb64, 'token': token, 'error': "All fields are required."})

        if password != confirm:
            return render(request, 'Accounts/reset_password.html', {'validlink': True, 'uidb64': uidb64, 'token': token, 'error': "Passwords do not match."})

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.password = make_password(password)
                user.save()
                return redirect('/login/')
        except Exception:
            pass

        return render(request, 'Accounts/reset_password.html', {'validlink': False})
