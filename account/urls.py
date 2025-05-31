from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'account'  # Define the app namespace here

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('user-profile/', views.user_profile, name='user_profile'),
    path('user-register/', views.user_register, name='user_register'),
]