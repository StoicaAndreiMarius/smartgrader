from django.urls import path
from . import views

urlpatterns = [
    # Existing teacher routes
    path('tests/<int:test_id>/upload-submissions/', views.upload_submissions, name='upload-submissions'),
    path('tests/<int:test_id>/submissions/', views.get_test_submissions, name='get-submissions'),
    path('tests/<int:test_id>/submissions/<int:submission_id>/', views.submission_detail_page, name='submission-detail'),
    path('tests/<int:test_id>/submissions/<int:submission_id>/update-name/', views.update_submission_name, name='update-submission-name'),
    path('tests/<int:test_id>/export-csv/', views.export_results_csv, name='export-csv'),

    # Teacher share code management
    path('tests/<int:test_id>/generate-share-code/', views.generate_share_code_view, name='generate-share-code'),
    path('tests/<int:test_id>/toggle-submissions/', views.toggle_submissions, name='toggle-submissions'),
    path('tests/<int:test_id>/share-info/', views.get_share_info, name='share-info'),

    # Student routes
    path('student/dashboard/', views.student_dashboard, name='student-dashboard'),
    path('student/test/<str:share_code>/', views.student_test_access, name='student-test-access'),
    path('student/test/<str:share_code>/submit/', views.student_submit_answers, name='student-submit-answers'),
    path('student/test/<str:share_code>/result/<int:submission_id>/', views.student_submission_result, name='student-submission-result'),
    path('student/test/<str:share_code>/result/<int:submission_id>/delete/', views.student_delete_submission, name='student-delete-submission'),

    # General pages
    path('help/', views.help_page, name='help'),
    path('information/', views.information_page, name='information'),
    path('about/', views.about_page, name='about'),
    path('support/', views.support_page, name='support'),
    path('privacy/', views.privacy_page, name='privacy'),
    path('terms/', views.terms_page, name='terms'),
]
