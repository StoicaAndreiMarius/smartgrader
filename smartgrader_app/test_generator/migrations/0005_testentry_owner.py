from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("test_generator", "0004_ensure_accounts_tests_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="testentry",
            name="owner",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="tests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
