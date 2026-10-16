# Hand-written migration — all schema changes go directly to registry_zmcdocumenttemplate
# using RunSQL (the real existing table).  Django state is updated via SeparateDatabaseAndState.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0095_institutionalpolicydocument_zmcdocumenttemplate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ─── 1. Real DDL — add columns to the existing SQLite table ────────
        migrations.RunSQL(
            sql=[
                "ALTER TABLE registry_zmcdocumenttemplate ADD COLUMN template_body TEXT NOT NULL DEFAULT '';",
                "ALTER TABLE registry_zmcdocumenttemplate ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1;",
                "ALTER TABLE registry_zmcdocumenttemplate ADD COLUMN created_by_id INTEGER REFERENCES auth_user(id);",
                "ALTER TABLE registry_zmcdocumenttemplate ADD COLUMN updated_at DATETIME NOT NULL DEFAULT '2026-01-01 00:00:00';",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ─── 2. State-only updates — tell Django's ORM about the new fields ─
        migrations.SeparateDatabaseAndState(
            database_operations=[],   # DDL already done above
            state_operations=[
                migrations.AlterField(
                    model_name="zrpdocumenttemplate",
                    name="category",
                    field=models.CharField(blank=True, default="General", max_length=120),
                ),
                migrations.AddField(
                    model_name="zrpdocumenttemplate",
                    name="template_body",
                    field=models.TextField(blank=True, default=""),
                ),
                migrations.AddField(
                    model_name="zrpdocumenttemplate",
                    name="is_active",
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name="zrpdocumenttemplate",
                    name="created_by",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AddField(
                    model_name="zrpdocumenttemplate",
                    name="updated_at",
                    field=models.DateTimeField(auto_now=True),
                ),
                migrations.AlterModelOptions(
                    name="zrpdocumenttemplate",
                    options={"ordering": ["category", "title"]},
                ),
                migrations.AlterModelTable(
                    name="zrpdocumenttemplate",
                    table="registry_zmcdocumenttemplate",
                ),
            ],
        ),
    ]
