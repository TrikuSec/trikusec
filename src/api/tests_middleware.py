import pytest
import logging
from io import StringIO
from django.test import Client, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from api.middleware import AuditLoggingMiddleware
from api.models import LicenseKey


@pytest.mark.django_db
class TestAuditLoggingMiddleware:
    """Tests for the audit logging middleware."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.factory = RequestFactory()
        self.middleware = AuditLoggingMiddleware(lambda request: None)
        # Capture log output
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.addHandler(self.handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.audit_logger.removeHandler(self.handler)
        self.handler.close()
    
    def test_logs_sensitive_path_upload(self, test_license_key, sample_lynis_report):
        """Test that upload endpoint requests are logged."""
        url = reverse('upload_report')
        
        response = self.client.post(url, {
            'licensekey': test_license_key.licensekey,
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        assert response.status_code == 200
        log_output = self.log_capture.getvalue()
        
        # Check that request was logged
        assert 'AUDIT:' in log_output
        assert '/api/lynis/upload/' in log_output
        assert 'POST' in log_output
        assert 'Status: 200' in log_output
    
    def test_logs_sensitive_path_admin_licensekey(self, test_user):
        """Test that admin license key paths are logged."""
        self.client.force_login(test_user)
        url = '/admin/api/licensekey/'
        
        response = self.client.get(url)
        
        log_output = self.log_capture.getvalue()
        
        # Check that request was logged
        assert 'AUDIT:' in log_output
        assert '/admin/api/licensekey/' in log_output
        assert 'GET' in log_output
    
    def test_logs_sensitive_path_admin_device(self, test_user):
        """Test that admin device paths are logged."""
        self.client.force_login(test_user)
        url = '/admin/api/device/'
        
        response = self.client.get(url)
        
        log_output = self.log_capture.getvalue()
        
        # Check that request was logged
        assert 'AUDIT:' in log_output
        assert '/admin/api/device/' in log_output
        assert 'GET' in log_output
    
    def test_logs_anonymous_user(self, test_license_key, sample_lynis_report):
        """Test that anonymous users are logged correctly."""
        url = reverse('upload_report')
        
        response = self.client.post(url, {
            'licensekey': test_license_key.licensekey,
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        log_output = self.log_capture.getvalue()
        
        # Check that anonymous user is logged
        assert 'User: anonymous' in log_output
    
    def test_logs_authenticated_user(self, test_user):
        """Test that authenticated users are logged correctly."""
        self.client.force_login(test_user)
        url = '/admin/api/licensekey/'
        
        response = self.client.get(url)
        
        log_output = self.log_capture.getvalue()
        
        # Check that authenticated user is logged
        assert f'User: {test_user.username}' in log_output
    
    def test_logs_client_ip(self, test_license_key, sample_lynis_report):
        """Test that client IP is logged."""
        url = reverse('upload_report')
        
        response = self.client.post(url, {
            'licensekey': test_license_key.licensekey,
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        log_output = self.log_capture.getvalue()
        
        # Check that IP is logged
        assert 'IP:' in log_output
    
    def test_logs_user_agent(self, test_license_key, sample_lynis_report):
        """Test that User-Agent is logged."""
        url = reverse('upload_report')
        
        response = self.client.post(
            url,
            {
                'licensekey': test_license_key.licensekey,
                'hostid': 'test-host-id-1',
                'hostid2': 'test-host-id-2',
                'data': sample_lynis_report
            },
            HTTP_USER_AGENT='Test-Agent/1.0'
        )
        
        log_output = self.log_capture.getvalue()
        
        # Check that User-Agent is logged
        assert 'User-Agent:' in log_output
        assert 'Test-Agent/1.0' in log_output
    
    def test_logs_response_status(self, test_license_key, sample_lynis_report):
        """Test that response status codes are logged."""
        url = reverse('upload_report')
        
        # Test successful response
        response = self.client.post(url, {
            'licensekey': test_license_key.licensekey,
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        log_output = self.log_capture.getvalue()
        assert 'Status: 200' in log_output
        
        # Test error response
        self.log_capture.seek(0)
        self.log_capture.truncate(0)
        
        response = self.client.post(url, {
            'licensekey': 'invalid-license',
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        log_output = self.log_capture.getvalue()
        assert 'Status: 401' in log_output
    
    def test_does_not_log_non_sensitive_paths(self):
        """Test that non-sensitive paths are not logged."""
        url = '/health/'
        
        response = self.client.get(url)
        
        log_output = self.log_capture.getvalue()
        
        # Check that non-sensitive path is not logged
        assert 'AUDIT:' not in log_output or '/health/' not in log_output
    
    def test_get_client_ip_from_remote_addr(self):
        """Test getting client IP from REMOTE_ADDR."""
        request = self.factory.get('/api/lynis/upload/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = AuditLoggingMiddleware.get_client_ip(request)
        
        assert ip == '192.168.1.1'
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header."""
        request = self.factory.get('/api/lynis/upload/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        
        ip = AuditLoggingMiddleware.get_client_ip(request)
        
        # Should get the first IP from X-Forwarded-For
        assert ip == '10.0.0.1'
    
    def test_get_client_ip_prefers_x_forwarded_for(self):
        """Test that X-Forwarded-For is preferred over REMOTE_ADDR."""
        request = self.factory.get('/api/lynis/upload/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = AuditLoggingMiddleware.get_client_ip(request)
        
        # Should prefer X-Forwarded-For
        assert ip == '10.0.0.1'
    
    def test_logs_both_request_and_response(self, test_license_key, sample_lynis_report):
        """Test that both request and response are logged."""
        url = reverse('upload_report')
        
        response = self.client.post(url, {
            'licensekey': test_license_key.licensekey,
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        log_output = self.log_capture.getvalue()
        
        # Should have two log entries: one for request, one for response
        audit_lines = [line for line in log_output.split('\n') if 'AUDIT:' in line]
        assert len(audit_lines) >= 2  # At least request and response
    
    def test_logs_admin_licensekey_add_path(self, test_user):
        """Test that admin license key add path is logged."""
        self.client.force_login(test_user)
        url = '/admin/api/licensekey/add/'
        
        response = self.client.get(url)
        
        log_output = self.log_capture.getvalue()
        
        # Check that add path is logged
        assert 'AUDIT:' in log_output
        assert '/admin/api/licensekey/add/' in log_output
    
    def test_middleware_returns_response(self, test_license_key, sample_lynis_report):
        """Test that middleware properly returns the response."""
        url = reverse('upload_report')
        
        response = self.client.post(url, {
            'licensekey': test_license_key.licensekey,
            'hostid': 'test-host-id-1',
            'hostid2': 'test-host-id-2',
            'data': sample_lynis_report
        })
        
        # Middleware should not interfere with response
        assert response.status_code == 200
        assert response.content == b'OK'

