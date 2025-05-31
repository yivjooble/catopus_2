from django.urls import path
from . import views

app_name = 'search'  # Define the app namespace here

urlpatterns = [
    path('', views.index, name='index'),
    path('result/<str:identifier>/', views.share_results, name='result'),
    path('history/', views.history, name='history'),
    path('remote/', views.remote, name='remote'),
    path('saved_scripts/', views.saved_scripts, name='saved_scripts'),
    path('python_etl/', views.python_etl, name='python_etl'),
    path('run_bat_file/', views.run_bat_file, name='run_bat_file'),
]