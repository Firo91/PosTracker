from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_device_last_down_services'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='country_code',
            field=models.CharField(
                blank=True,
                help_text='ISO 2-letter country code (e.g., NO, IS)',
                max_length=2,
            ),
        ),
    ]
