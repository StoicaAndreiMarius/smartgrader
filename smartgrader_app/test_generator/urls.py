from django.urls import path
from .views import (
    generator_page,
    test_list_page,
    test_detail_page,
    create_test,
    delete_test,
    pdf_test,
    ai_generate_questions,
)

urlpatterns = [
    path("test-generator/", generator_page, name="test-generator"),
    path("tests/", test_list_page, name="tests"),
    path("tests/<int:test_id>/", test_detail_page, name="test-detail"),
    path("tests/<int:test_id>/pdf/", pdf_test, name="test-pdf"),
    path("accounts/api-create-test/", create_test, name="api-create-test"),
    path("accounts/api-ai-generate/", ai_generate_questions, name="api-ai-generate"),
    path("tests/<int:test_id>/delete/", delete_test, name="test-delete"),
]
