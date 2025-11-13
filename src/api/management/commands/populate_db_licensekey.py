from django.core.management.base import BaseCommand
from api.models import LicenseKey, User, Organization
from api.utils.license_utils import generate_license_key
import random
import string

class Command(BaseCommand):
    help = 'Generate a random license key and add it to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'licensekey',
            nargs='?',
            help='Optional license key to insert instead of generating a random one',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Name for the license key',
        )
        parser.add_argument(
            '--max-devices',
            type=int,
            help='Maximum number of devices for this license (leave empty for unlimited)',
        )

    def generate_random_string(self, length):
        characters = 'abcdef0123456789'
        random_string = ''.join(random.choices(characters, k=length))
        return random_string

    def handle(self, *args, **kwargs):
        # Use provided license key if given, otherwise generate one
        provided_license_key = kwargs.get('licensekey')
        license_name = kwargs.get('name', 'Default License')
        max_devices = kwargs.get('max_devices')
        
        if not provided_license_key and LicenseKey.objects.exists():
            self.stdout.write(self.style.SUCCESS('License key already exists in the database'))
            return
        
        if not provided_license_key:
            # Use the utility function to generate a unique license key
            license_key = generate_license_key()
        else:
            license_key = provided_license_key
        
        # Get first user in the database
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found in the database. License should be associated with a user'))
            return
        
        # Get or create default organization
        default_org, _ = Organization.objects.get_or_create(
            slug='default',
            defaults={'name': 'Default Organization', 'is_active': True}
        )
        
        # Overwrite existing license or create a new one
        existing = LicenseKey.objects.first()
        if existing:
            existing.licensekey = license_key
            # Ensure name is always set (required field)
            existing.name = license_name or f"License {existing.id}"
            existing.created_by = user
            existing.organization = default_org
            if max_devices is not None:
                existing.max_devices = max_devices
            existing.save()
            self.stdout.write(self.style.SUCCESS('Successfully updated the existing license key'))
        else:
            LicenseKey.objects.create(
                licensekey=license_key,
                name=license_name,
                created_by=user,
                organization=default_org,
                max_devices=max_devices
            )
            self.stdout.write(self.style.SUCCESS('Successfully generated and added a license key to the database'))
