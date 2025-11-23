import pytest
from django.urls import reverse, resolve
from django.conf import settings
import sys
import importlib

class TestSplitArchitecture:
    def test_frontend_settings_urls(self):
        """Verify frontend settings use frontend URLs and include admin."""
        # Simulate loading frontend settings
        # Note: We can't easily unload settings in Django during tests, 
        # so we inspect the module attributes directly
        
        from trikusec.settings import frontend as frontend_settings
        assert frontend_settings.ROOT_URLCONF == 'trikusec.urls_frontend'
        assert 'django.contrib.admin' in frontend_settings.INSTALLED_APPS
        assert 'django.contrib.sessions' in frontend_settings.INSTALLED_APPS
        
        # Verify URLconf content
        from trikusec import urls_frontend
        # URL patterns are list of resolvers
        has_admin = any(p.pattern.match('admin/') for p in urls_frontend.urlpatterns if hasattr(p, 'pattern'))
        assert has_admin, "Frontend URLs should include admin"

    def test_api_settings_urls(self):
        """Verify API settings use API URLs and exclude admin/sessions."""
        from trikusec.settings import api as api_settings
        assert api_settings.ROOT_URLCONF == 'trikusec.urls_api'
        
        # Check middleware/apps
        # Note: api settings imports from base, so we check what's defined in api.py
        # INSTALLED_APPS is redefined in api.py
        assert 'django.contrib.admin' not in api_settings.INSTALLED_APPS
        assert 'django.contrib.sessions' not in api_settings.INSTALLED_APPS
        
        # Verify URLconf content
        from trikusec import urls_api
        has_admin = any(p.pattern.match('admin/') for p in urls_api.urlpatterns if hasattr(p, 'pattern'))
        assert not has_admin, "API URLs should not include admin"
        
        has_api_v1 = any(p.pattern.match('api/v1/') for p in urls_api.urlpatterns if hasattr(p, 'pattern'))
        assert has_api_v1, "API URLs should include api/v1/"



