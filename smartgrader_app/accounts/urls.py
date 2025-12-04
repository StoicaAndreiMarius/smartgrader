from django.urls import path 
from . import views
from .views import register_user, login_user

urlpatterns = [
    path('', views.landing, name = 'landing'),
    path("accounts/register/", register_user, name="register"),
    path("accounts/login/", login_user, name="login"),
]