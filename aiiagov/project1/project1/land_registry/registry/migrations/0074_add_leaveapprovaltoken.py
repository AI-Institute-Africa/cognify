# Generated manual migration to add LeaveApprovalToken model
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0073_add_leaverequest_signed_document'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveApprovalToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=128, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('approver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_tokens', to='auth.user')),
                ('leave_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_tokens', to='registry.leaverequest')),
            ],
        ),
    ]
