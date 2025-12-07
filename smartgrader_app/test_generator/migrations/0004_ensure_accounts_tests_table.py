from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("test_generator", "0003_alter_testentry_table"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE IF EXISTS accounts_test RENAME TO accounts_tests;",
            reverse_sql="ALTER TABLE IF EXISTS accounts_tests RENAME TO accounts_test;",
        ),
    ]
