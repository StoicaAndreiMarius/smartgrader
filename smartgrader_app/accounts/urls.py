from django.urls import path 
from . import views
from .views import *

urlpatterns = [
    path('', views.landing, name = 'landing'),

    path("accounts/api-register/", register_user, name="api-register"),
    path("accounts/api-login/", login_user, name="api-login"),
    path("logout/", logout_user, name="logout"),

    path("register/", register_page, name="register"),
    path("login/", login_page, name="login"),
]
