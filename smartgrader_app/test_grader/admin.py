from django.contrib import admin

from .models import Submission, Test


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_by', 'num_questions', 'created_at')
    search_fields = ('title', 'created_by__email')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'full_name', 'score', 'percentage', 'submitted_at', 'processed')
    list_filter = ('processed',)
    search_fields = ('first_name', 'last_name', 'student_user__email', 'test__title')
