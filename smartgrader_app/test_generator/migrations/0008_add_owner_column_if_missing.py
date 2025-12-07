from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("test_generator", "0007_merge_conflicts"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE accounts_tests
            ADD COLUMN IF NOT EXISTS owner_id integer;
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'accounts_tests_owner_id_fk'
                ) THEN
                    ALTER TABLE accounts_tests
                    ADD CONSTRAINT accounts_tests_owner_id_fk
                    FOREIGN KEY (owner_id)
                    REFERENCES accounts_customuser(id)
                    ON DELETE CASCADE;
                END IF;
            END$$;
            """,
            reverse_sql="""
            ALTER TABLE accounts_tests DROP CONSTRAINT IF EXISTS accounts_tests_owner_id_fk;
            ALTER TABLE accounts_tests DROP COLUMN IF EXISTS owner_id;
            """,
        )
    ]
