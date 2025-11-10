from django.test import TestCase
import os
from unittest.mock import patch


class SettingsDebugModeTestCase(TestCase):
    """Test cases for Django DEBUG setting security"""

    def setUp(self):
        """Store original DEBUG environment variable"""
        self.original_debug = os.environ.get('DJANGO_DEBUG')

    def tearDown(self):
        """Restore original DEBUG environment variable"""
        if self.original_debug is not None:
            os.environ['DJANGO_DEBUG'] = self.original_debug
        elif 'DJANGO_DEBUG' in os.environ:
            del os.environ['DJANGO_DEBUG']

    @patch.dict(os.environ, {'SECRET_KEY': 'test-key'}, clear=True)
    def test_debug_defaults_to_false(self):
        """Test that DEBUG defaults to False when DJANGO_DEBUG is not set"""
        # Remove DJANGO_DEBUG from environment
        if 'DJANGO_DEBUG' in os.environ:
            del os.environ['DJANGO_DEBUG']
        
        # Re-import settings to get fresh DEBUG value
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertFalse(settings.DEBUG, 
                        "DEBUG should default to False for security")

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'False', 'SECRET_KEY': 'test-key'})
    def test_debug_explicitly_false(self):
        """Test that DEBUG is False when DJANGO_DEBUG='False'"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertFalse(settings.DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'True', 'SECRET_KEY': 'test-key'})
    def test_debug_explicitly_true(self):
        """Test that DEBUG is True when DJANGO_DEBUG='True'"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertTrue(settings.DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': '1', 'SECRET_KEY': 'test-key'})
    def test_debug_numeric_one(self):
        """Test that DEBUG is True when DJANGO_DEBUG='1'"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertTrue(settings.DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'yes', 'SECRET_KEY': 'test-key'})
    def test_debug_yes_string(self):
        """Test that DEBUG is True when DJANGO_DEBUG='yes'"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertTrue(settings.DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': '0', 'SECRET_KEY': 'test-key'})
    def test_debug_numeric_zero(self):
        """Test that DEBUG is False when DJANGO_DEBUG='0'"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertFalse(settings.DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'no', 'SECRET_KEY': 'test-key'})
    def test_debug_no_string(self):
        """Test that DEBUG is False when DJANGO_DEBUG='no'"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertFalse(settings.DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'invalid', 'SECRET_KEY': 'test-key'})
    def test_debug_invalid_value(self):
        """Test that DEBUG is False for invalid values (secure default)"""
        from importlib import reload
        from compleasy import settings
        reload(settings)
        
        self.assertFalse(settings.DEBUG, 
                        "DEBUG should default to False for invalid values")
