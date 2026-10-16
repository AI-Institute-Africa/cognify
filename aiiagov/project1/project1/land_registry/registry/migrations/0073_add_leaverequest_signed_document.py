from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0072_leaverequest_approvers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverequest',
            name='signed_document',
            field=models.FileField(blank=True, null=True, upload_to='leave_documents/signed/'),
        ),
    ]
