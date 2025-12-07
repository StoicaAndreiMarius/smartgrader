from django.urls import path
from .views import generator_page, test_list_page, test_detail_page, create_test

urlpatterns = [
    path("test-generator/", generator_page, name="test-generator"),
    path("tests/", test_list_page, name="tests"),
    path("tests/<int:test_id>/", test_detail_page, name="test-detail"),
    path("accounts/api-create-test/", create_test, name="api-create-test"),
]
