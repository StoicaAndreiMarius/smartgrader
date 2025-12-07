from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("test_generator", "0002_alter_testentry_table"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="testentry",
            table="accounts_tests",
        ),
    ]
