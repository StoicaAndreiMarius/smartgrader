from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('questions', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('num_questions', models.IntegerField()),
                ('num_options', models.IntegerField(default=5)),
                (
                    'created_by',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='graded_tests',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('image', models.ImageField(upload_to='submissions/')),
                ('answers', models.JSONField()),
                ('score', models.IntegerField()),
                ('total_questions', models.IntegerField()),
                ('percentage', models.FloatField()),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True, null=True)),
                (
                    'student_user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='submissions',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'test',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='submissions',
                        to='test_grader.test',
                    ),
                ),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
    ]
