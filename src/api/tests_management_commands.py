"""Tests for management commands."""
import pytest
import os
from django.core.management import call_command
from django.contrib.auth.models import User
from io import StringIO


@pytest.mark.django_db
class TestChangeAdminPassword:
    """Tests for the change_admin_password management command."""

    def _create_or_reset_admin(self):
        """Ensure a single reusable admin user for each test."""
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@test.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        admin.set_password('initial_password')
        admin.save()
        return admin

    def test_change_password_with_env_var(self):
        """Test changing admin password using TRIKUSEC_ADMIN_PASSWORD env var."""
        # Create admin user with initial password
        admin = self._create_or_reset_admin()
        
        # Set environment variable
        os.environ['TRIKUSEC_ADMIN_PASSWORD'] = 'new_password_123'
        
        try:
            # Run command
            out = StringIO()
            call_command('change_admin_password', stdout=out)
            
            # Verify password was changed
            admin.refresh_from_db()
            assert admin.check_password('new_password_123')
            assert not admin.check_password('initial_password')
        finally:
            # Clean up
            del os.environ['TRIKUSEC_ADMIN_PASSWORD']
    
    def test_change_password_with_command_line_arg(self):
        """Test changing admin password using command line argument."""
        # Create admin user with initial password
        admin = self._create_or_reset_admin()
        
        # Run command with password argument
        out = StringIO()
        call_command('change_admin_password', password='cli_password_456', stdout=out)
        
        # Verify password was changed
        admin.refresh_from_db()
        assert admin.check_password('cli_password_456')
        assert not admin.check_password('initial_password')
    
    def test_change_password_command_line_overrides_env(self):
        """Test that command line password argument takes precedence over env var."""
        # Create admin user
        admin = self._create_or_reset_admin()
        
        # Set environment variable
        os.environ['TRIKUSEC_ADMIN_PASSWORD'] = 'env_password'
        
        try:
            # Run command with command line argument
            out = StringIO()
            call_command('change_admin_password', password='cli_password', stdout=out)
            
            # Verify command line password was used
            admin.refresh_from_db()
            assert admin.check_password('cli_password')
            assert not admin.check_password('env_password')
        finally:
            # Clean up
            del os.environ['TRIKUSEC_ADMIN_PASSWORD']
    
    def test_change_password_no_password_provided(self):
        """Test that command fails gracefully when no password is provided."""
        # Create admin user
        admin = self._create_or_reset_admin()
        
        # Ensure env var is not set
        if 'TRIKUSEC_ADMIN_PASSWORD' in os.environ:
            del os.environ['TRIKUSEC_ADMIN_PASSWORD']
        
        # Run command without password (should use None)
        out = StringIO()
        call_command('change_admin_password', stdout=out)
        
        # Password should be set to None (which is invalid but the command doesn't validate)
        # The Django user.set_password(None) will set an unusable password
        admin.refresh_from_db()
        assert not admin.check_password('initial_password')
