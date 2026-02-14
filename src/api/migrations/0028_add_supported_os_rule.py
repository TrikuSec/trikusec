# Generated migration for adding supported OS rule

from django.db import migrations


def add_supported_os_rule(apps, schema_editor):
    """Add 'Supported Operating System' rule to Default baseline ruleset"""
    User = apps.get_model('auth', 'User')
    PolicyRule = apps.get_model('api', 'PolicyRule')
    PolicyRuleset = apps.get_model('api', 'PolicyRuleset')
    
    # Get system user
    try:
        system_user = User.objects.get(username='system')
    except User.DoesNotExist:
        # If system user doesn't exist, skip this migration
        # This shouldn't happen if 0012 migration ran successfully
        return
    
    # Create the new rule
    rule, created = PolicyRule.objects.get_or_create(
        name='Supported Operating System',
        defaults={
            'rule_query': '!(warning[*][0] | contains(@, \'GEN-0010\'))',
            'description': 'Operating system must be supported and not end-of-life (EOL)',
            'enabled': True,
            'alert': True,
            'created_by': system_user,
            'is_system': True,
        }
    )
    
    # If rule already exists but is not a system rule, update it
    if not created and not rule.is_system:
        rule.rule_query = '!(warning[*][0] | contains(@, \'GEN-0010\'))'
        rule.description = 'Operating system must be supported and not end-of-life (EOL)'
        rule.enabled = True
        rule.alert = True
        rule.created_by = system_user
        rule.is_system = True
        rule.save()
    
    # Get or create Default baseline ruleset
    try:
        baseline_ruleset = PolicyRuleset.objects.get(name='Default baseline')
    except PolicyRuleset.DoesNotExist:
        # Create it if it doesn't exist
        baseline_ruleset = PolicyRuleset.objects.create(
            name='Default baseline',
            description='Default baseline ruleset with essential security checks',
            created_by=system_user,
            is_system=True,
        )
    
    # Add the new rule to the ruleset if not already present
    if rule not in baseline_ruleset.rules.all():
        baseline_ruleset.rules.add(rule)
        baseline_ruleset.save()


def reverse_migration(apps, schema_editor):
    """Remove 'Supported Operating System' rule"""
    PolicyRule = apps.get_model('api', 'PolicyRule')
    PolicyRuleset = apps.get_model('api', 'PolicyRuleset')
    
    # Get the rule
    try:
        rule = PolicyRule.objects.get(name='Supported Operating System')
        
        # Remove from all rulesets first
        for ruleset in PolicyRuleset.objects.filter(rules=rule):
            ruleset.rules.remove(rule)
        
        # Delete the rule
        rule.delete()
    except PolicyRule.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_enrollmentsettings_enable_daily_reports'),
    ]

    operations = [
        migrations.RunPython(add_supported_os_rule, reverse_migration),
    ]
