# Migration for requires_approvals and approvers_json

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0096_zrp_template_builder"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="zrpdocumenttemplate",
                    name="requires_approvals",
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name="zrpdocumenttemplate",
                    name="approvers_json",
                    field=models.TextField(blank=True, default="[]"),
                ),
            ],
        ),
    ]
