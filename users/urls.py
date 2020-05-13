"""URLs for the users app"""
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegistration.as_view(), name='register'),
]
