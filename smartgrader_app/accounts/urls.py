from django.urls import path 
from . import views
from .views import register_user, login_user

urlpatterns = [
    path('', views.landing, name = 'landing'),
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
]