from django.core.management.base import BaseCommand
from api.models import LicenseKey, User
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

    def generate_random_string(self, length):
        characters = 'abcdef0123456789'
        random_string = ''.join(random.choices(characters, k=length))
        return random_string

    def handle(self, *args, **kwargs):
        # Use provided license key if given, otherwise generate one
        provided_license_key = kwargs.get('licensekey')
        if not provided_license_key and LicenseKey.objects.exists():
            self.stdout.write(self.style.SUCCESS('License key already exists in the database'))
            return
        
        if not provided_license_key:
            # Generate a random license key in the format XXXXXXXX-XXXXXXXX-XXXXXXXX
            # with the following criteria: [a-f0-9-]
            license_key = (
                self.generate_random_string(8)
                + '-'
                + self.generate_random_string(8)
                + '-'
                + self.generate_random_string(8)
            )
        else:
            license_key = provided_license_key
        
        # Get first user in the database
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found in the database. License should be associated with a user'))
            return
        
        # Overwrite existing license or create a new one
        existing = LicenseKey.objects.first()
        if existing:
            existing.licensekey = license_key
            existing.created_by = user
            existing.save()
            self.stdout.write(self.style.SUCCESS('Successfully updated the existing license key'))
        else:
            LicenseKey.objects.create(licensekey=license_key, created_by=user)
            self.stdout.write(self.style.SUCCESS('Successfully generated and added a license key to the database'))
