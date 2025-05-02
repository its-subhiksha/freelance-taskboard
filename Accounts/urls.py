from django.urls import path
from Accounts import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.UserDashboard.as_view(), name='dashboard'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('client/dashboard/', views.ClientDashboard.as_view(), name='client_dashboard'),
    path('freelancer/dashboard/', views.FreelancerDashboard.as_view(), name='freelancer_dashboard'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)