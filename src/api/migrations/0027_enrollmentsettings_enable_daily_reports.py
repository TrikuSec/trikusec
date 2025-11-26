from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_device_ip_address_device_mac_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollmentsettings',
            name='enable_daily_reports',
            field=models.BooleanField(default=True),
        ),
    ]

