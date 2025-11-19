# Generated migration for extending ActivityIgnorePattern

from django.db import migrations, models


def migrate_pattern_to_key_pattern(apps, schema_editor):
    """Copy pattern field to key_pattern field"""
    ActivityIgnorePattern = apps.get_model('api', 'ActivityIgnorePattern')
    for pattern in ActivityIgnorePattern.objects.all():
        pattern.key_pattern = pattern.pattern
        pattern.save(update_fields=['key_pattern'])


def reverse_migration(apps, schema_editor):
    """Reverse migration - copy key_pattern back to pattern"""
    ActivityIgnorePattern = apps.get_model('api', 'ActivityIgnorePattern')
    for pattern in ActivityIgnorePattern.objects.all():
        pattern.pattern = pattern.key_pattern
        pattern.save(update_fields=['pattern'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_refactor_diff_system'),
    ]

    operations = [
        # Add new fields first
        migrations.AddField(
            model_name='activityignorepattern',
            name='event_type',
            field=models.CharField(choices=[('all', 'All'), ('added', 'Added'), ('changed', 'Changed'), ('removed', 'Removed')], default='all', max_length=10),
        ),
        migrations.AddField(
            model_name='activityignorepattern',
            name='host_pattern',
            field=models.CharField(default='*', max_length=255),
        ),
        # Add key_pattern field (temporary, will replace pattern)
        migrations.AddField(
            model_name='activityignorepattern',
            name='key_pattern',
            field=models.CharField(max_length=255, null=True),
        ),
        # Copy data from pattern to key_pattern
        migrations.RunPython(migrate_pattern_to_key_pattern, reverse_migration),
        # Make key_pattern non-nullable
        migrations.AlterField(
            model_name='activityignorepattern',
            name='key_pattern',
            field=models.CharField(max_length=255),
        ),
        # Remove old unique_together constraint that references pattern
        migrations.AlterUniqueTogether(
            name='activityignorepattern',
            unique_together=(),
        ),
        # Remove old pattern field
        migrations.RemoveField(
            model_name='activityignorepattern',
            name='pattern',
        ),
        # Add new unique_together constraint with new fields
        migrations.AlterUniqueTogether(
            name='activityignorepattern',
            unique_together={('organization', 'key_pattern', 'event_type', 'host_pattern')},
        ),
        # Add new index for event_type filtering
        migrations.AddIndex(
            model_name='activityignorepattern',
            index=models.Index(fields=['organization', 'event_type', 'is_active'], name='api_activi_organiz_event_idx'),
        ),
    ]

