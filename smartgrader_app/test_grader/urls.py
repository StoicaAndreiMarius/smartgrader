from django.urls import path
from . import views

urlpatterns = [
    path('tests/<int:test_id>/upload-submissions/', views.upload_submissions, name='upload-submissions'),
    path('tests/<int:test_id>/submissions/', views.get_test_submissions, name='get-submissions'),
    path('tests/<int:test_id>/submissions/<int:submission_id>/', views.submission_detail_page, name='submission-detail'),
    path('tests/<int:test_id>/submissions/<int:submission_id>/update-name/', views.update_submission_name, name='update-submission-name'),
    path('tests/<int:test_id>/export-csv/', views.export_results_csv, name='export-csv'),
]
