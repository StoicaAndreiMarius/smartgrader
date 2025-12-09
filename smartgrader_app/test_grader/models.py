from django.db import models
from django.conf import settings

class Test(models.Model):
    """Persisted graded test definition with correct answers and metadata."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    questions = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='graded_tests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    num_questions = models.IntegerField()
    num_options = models.IntegerField(default=5)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.created_by.email}"


class Submission(models.Model):
    """Student submission with detected answers, scores, and uploaded sheet."""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='submissions')
    student_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='submissions', blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='submissions/')
    answers = models.JSONField()
    score = models.FloatField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    @property
    def full_name(self):
        """Return full name of student"""
        if self.student_user:
            return f"{self.student_user.first_name} {self.student_user.last_name}".strip() or self.student_user.email
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown"
    
    @property
    def grade(self):
        """Calculate letter grade based on percentage"""
        if self.percentage >= 90:
            return 'A'
        elif self.percentage >= 80:
            return 'B'
        elif self.percentage >= 70:
            return 'C'
        elif self.percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def __str__(self):
        return f"{self.full_name} - {self.test.title} - {self.score}/{self.total_questions}"
