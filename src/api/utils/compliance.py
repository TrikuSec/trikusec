import logging

def check_device_compliance(device, report):
    """
    Check the compliance of a device and return both the compliance status and detailed rule results.
    """
    policy_rulesets = device.rulesets.all()
    policy_rulesets = list(policy_rulesets)
    
    logging.debug('Policy rulesets for device %s: %s', device, policy_rulesets)
    
    compliant = True
    evaluated_rulesets = []
    
    for policy_ruleset in policy_rulesets:
        ruleset_dict = {
            'id': policy_ruleset.id,
            'name': policy_ruleset.name,
            'description': policy_ruleset.description,
            'rules': []
        }
        
        ruleset_compliant = True
        for rule in policy_ruleset.rules.all():
            rule_compliant = rule.evaluate(report)
            ruleset_dict['rules'].append({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'enabled': rule.enabled,
                'alert': rule.alert,
                'compliant': rule_compliant
            })
            # Only enabled rules affect ruleset compliance status
            if rule.enabled and not rule_compliant:
                ruleset_compliant = False
        
        ruleset_dict['compliant'] = ruleset_compliant
        evaluated_rulesets.append(ruleset_dict)
        
        if not ruleset_compliant:
            compliant = False
    
    return compliant, evaluated_rulesets


def update_device_compliance(device, report):
    """
    Check compliance, update device status, and log event if status changed.
    Returns (compliant, evaluated_rulesets).
    """
    from api.models import DeviceEvent  # Avoid circular import
    
    # Check compliance
    compliant, evaluated_rulesets = check_device_compliance(device, report)
    
    # Check if status changed
    if device.compliant != compliant:
        old_status = 'Compliant' if device.compliant else 'Non-Compliant'
        new_status = 'Compliant' if compliant else 'Non-Compliant'
        
        logging.info(f"Device {device.hostname} compliance changed: {old_status} -> {new_status}")
        
        # Create event
        DeviceEvent.objects.create(
            device=device,
            event_type='compliance_changed',
            metadata={
                'old_status': old_status,
                'new_status': new_status,
                'hostname': device.hostname
            }
        )
        
        # Update device
        device.compliant = compliant
        device.save()
        
    return compliant, evaluated_rulesets

