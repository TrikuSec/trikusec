# Generated migration for Organization and LicenseKey extensions

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def create_default_organization_and_migrate_licenses(apps, schema_editor):
    """Create default organization and link existing licenses to it"""
    Organization = apps.get_model('api', 'Organization')
    LicenseKey = apps.get_model('api', 'LicenseKey')
    
    # Create default organization
    default_org, created = Organization.objects.get_or_create(
        slug='default',
        defaults={
            'name': 'Default Organization',
            'is_active': True,
        }
    )
    
    # Link all existing licenses to default organization and set defaults
    for license_key in LicenseKey.objects.all():
        if license_key.organization is None:
            license_key.organization = default_org
        # Always ensure name is set (required field)
        if not license_key.name or license_key.name.strip() == '':
            license_key.name = f"License {license_key.id}"
        # Set max_devices to None (unlimited) for existing licenses
        if license_key.max_devices is None:
            license_key.max_devices = None  # Already None, but explicit
        license_key.save()


def reverse_migration(apps, schema_editor):
    """Reverse migration - remove organization links"""
    LicenseKey = apps.get_model('api', 'LicenseKey')
    LicenseKey.objects.all().update(organization=None)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_add_performance_indexes'),
    ]

    operations = [
        # Create Organization model
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        # Add new fields to LicenseKey (make nullable first)
        migrations.AddField(
            model_name='licensekey',
            name='name',
            field=models.CharField(max_length=255, default=''),
        ),
        migrations.AddField(
            model_name='licensekey',
            name='organization',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='api.organization'),
        ),
        migrations.AddField(
            model_name='licensekey',
            name='max_devices',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='licensekey',
            name='expires_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='licensekey',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        # Make licensekey unique
        migrations.AlterField(
            model_name='licensekey',
            name='licensekey',
            field=models.CharField(max_length=255, unique=True, db_index=True),
        ),
        # Data migration: create default org and set max_devices=null for existing licenses
        migrations.RunPython(create_default_organization_and_migrate_licenses, reverse_migration),
    ]

