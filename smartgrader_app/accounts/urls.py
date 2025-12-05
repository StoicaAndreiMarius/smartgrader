from django.urls import path 
from . import views
from .views import *

urlpatterns = [
    path('', views.landing, name = 'landing'),

    path("accounts/api-register/", register_user, name="api-register"),
    path("accounts/api-login/", login_user, name="api-login"),
    path("accounts/api-create-test/", views.create_test, name="api-create-test"),

    path("register/", register_page, name="register"),
    path("login/", login_page, name="login"),
    path("test-generator/", views.test_generator_page, name="test-generator"),
    path("tests/", views.test_list_page, name="test-list"),
]