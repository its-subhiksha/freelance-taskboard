from django.shortcuts import render,redirect
from Accounts.serializers import RegisterSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from Accounts.permissions import IsFreelancer, IsClient

from rest_framework.exceptions import AuthenticationFailed
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate,login,logout
from django.views import View
from Accounts.models import CustomUser
# Create your views here.

@method_decorator(login_required(login_url='/accounts/login/'), name='dispatch')
class UserDashboard(View):
    def get(self, request):
        context = {'user': request.user}
        return render(request, 'Accounts/dashboard.html', context)

@method_decorator(login_required(login_url='/accounts/login/'), name='dispatch')
class ClientDashboard(View):
    def get(self, request):
        context = {'user': request.user}
        return render(request, 'Accounts/client.html', context)

@method_decorator(login_required(login_url='/accounts/login/'), name='dispatch')
class FreelancerDashboard(View):
    def get(self, request):
        context = {'user': request.user}
        return render(request, 'Accounts/freelance.html', context)


class RegisterView(View):
    def get(self, request):
        return render(request, 'Accounts/register.html')
    def post(self, request):
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if CustomUser.objects.filter(username=username).exists():
            return render(request, "Accounts/register.html", {"error": "Username already taken."})

        if CustomUser.objects.filter(email=email).exists():
            return render(request, "Accounts/register.html", {"error": "Email already in use."})

        user = CustomUser.objects.create_user(username=username, email=email, password=password)
        login(request, user)  
        return redirect("/accounts/dashboard/")


class LoginView(View):

    def get(self, request):
        return render(request, 'Accounts/login.html')
    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request,user)
            return redirect("/accounts/dashboard/")
        else:
            return render(request, 'Accounts/login.html', {'error': 'Invalid username or password.'})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("/accounts/login/")

