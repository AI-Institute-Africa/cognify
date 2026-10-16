# Generated migration: Add signature and issuer confirmation fields to Borrow model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0076_borrow_folder_permission_borrow_folder_zip_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='borrow',
            name='borrower_signature',
            field=models.TextField(blank=True, help_text='Base64-encoded PNG signature from borrower upon return', null=True),
        ),
        migrations.AddField(
            model_name='borrow',
            name='return_confirmed',
            field=models.BooleanField(default=False, help_text='Issuer has confirmed receipt and acceptance of returned file'),
        ),
        migrations.AddField(
            model_name='borrow',
            name='confirmed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_returns', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='borrow',
            name='confirmed_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp when issuer confirmed the return'),
        ),
        migrations.AddField(
            model_name='borrow',
            name='issuer_signature',
            field=models.TextField(blank=True, help_text='Base64-encoded PNG signature from issuer upon acceptance', null=True),
        ),
    ]
