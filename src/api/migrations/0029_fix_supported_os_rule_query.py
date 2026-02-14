# Generated migration to fix supported OS rule query

from django.db import migrations


def fix_supported_os_rule_query(apps, schema_editor):
    """Fix the query for 'Supported Operating System' rule to handle null warnings"""
    PolicyRule = apps.get_model('api', 'PolicyRule')
    
    # Get the rule
    try:
        rule = PolicyRule.objects.get(name='Supported Operating System')
        # Update the query to handle null/missing warnings
        rule.rule_query = '!warning || !(contains(warning[*][0], \'GEN-0010\'))'
        rule.save()
    except PolicyRule.DoesNotExist:
        pass


def reverse_migration(apps, schema_editor):
    """Revert to the original query"""
    PolicyRule = apps.get_model('api', 'PolicyRule')
    
    try:
        rule = PolicyRule.objects.get(name='Supported Operating System')
        rule.rule_query = '!(warning[*][0] | contains(@, \'GEN-0010\'))'
        rule.save()
    except PolicyRule.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_add_supported_os_rule'),
    ]

    operations = [
        migrations.RunPython(fix_supported_os_rule_query, reverse_migration),
    ]
