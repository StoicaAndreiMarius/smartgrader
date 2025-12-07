from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("test_generator", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="testentry",
            table="accounts_test",
        ),
    ]
