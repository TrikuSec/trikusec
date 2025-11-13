"""
License utility functions for generating and validating license keys.
"""
import random
import string
from django.utils import timezone
from api.models import LicenseKey


def generate_license_key():
    """
    Generate a unique license key in format: xxxxxxxx-xxxxxxxx-xxxxxxxx
    Uses lowercase hex characters (a-f0-9) to match existing format.
    
    Returns:
        str: A unique license key string
    """
    characters = 'abcdef0123456789'
    
    # Generate until we find a unique key
    max_attempts = 100
    for _ in range(max_attempts):
        license_key = (
            ''.join(random.choices(characters, k=8))
            + '-'
            + ''.join(random.choices(characters, k=8))
            + '-'
            + ''.join(random.choices(characters, k=8))
        )
        
        # Check if key already exists
        if not LicenseKey.objects.filter(licensekey=license_key).exists():
            return license_key
    
    # If we couldn't generate a unique key after max attempts, raise error
    raise ValueError("Unable to generate unique license key after multiple attempts")


def validate_license(licensekey):
    """
    Check if license is valid, active, and not expired.
    
    Args:
        licensekey (str): The license key to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        license = LicenseKey.objects.get(licensekey=licensekey)
    except LicenseKey.DoesNotExist:
        return False, "License key does not exist"
    
    if not license.is_active:
        return False, "License key is inactive"
    
    if license.expires_at and license.expires_at < timezone.now():
        return False, "License key has expired"
    
    return True, None


def check_license_capacity(licensekey):
    """
    Check if license can accept more devices.
    
    Args:
        licensekey (str): The license key to check
        
    Returns:
        tuple: (has_capacity: bool, error_message: str or None)
    """
    is_valid, error = validate_license(licensekey)
    if not is_valid:
        return False, error
    
    try:
        license = LicenseKey.objects.get(licensekey=licensekey)
    except LicenseKey.DoesNotExist:
        return False, "License key does not exist"
    
    if not license.has_capacity():
        if license.max_devices is not None:
            return False, f"License has reached maximum device limit ({license.max_devices})"
        return False, "License cannot accept more devices"
    
    return True, None

