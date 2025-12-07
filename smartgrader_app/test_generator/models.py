from django.conf import settings
from django.db import models


class TestEntry(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tests",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "accounts_tests"

    def __str__(self):
        return self.title
