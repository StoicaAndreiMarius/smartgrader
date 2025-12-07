from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("test_generator", "0005_testentry_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="testentry",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="tests",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
