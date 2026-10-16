from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0069_brd_forwarded_to_pl_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectphase',
            name='pmt_required',
            field=models.PositiveIntegerField(
                default=5,
                help_text='Number of PMT members required to advance to HODs',
            ),
        ),
        migrations.AddField(
            model_name='projectphase',
            name='hods_required',
            field=models.PositiveIntegerField(
                default=5,
                help_text='Number of HODs members required to advance to Board',
            ),
        ),
        migrations.AddField(
            model_name='projectphase',
            name='board_required',
            field=models.PositiveIntegerField(
                default=5,
                help_text='Number of Board members required to close the phase',
            ),
        ),
    ]
