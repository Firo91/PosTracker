from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0006_agentstatushistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentstatushistory',
            name='old_status',
            field=models.BooleanField(
                blank=True,
                null=True,
                help_text='Previous agent health status (True=healthy, False=unhealthy, None=no contact)'
            ),
        ),
        migrations.AlterField(
            model_name='agentstatushistory',
            name='new_status',
            field=models.BooleanField(
                blank=True,
                null=True,
                help_text='New agent health status (True=healthy, False=unhealthy, None=no contact)'
            ),
        ),
    ]
