import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('audit')

class AuditLoggingMiddleware(MiddlewareMixin):
    """Middleware to log sensitive operations for audit trail."""
    
    SENSITIVE_PATHS = [
        '/admin/api/licensekey/add/',
        '/admin/api/licensekey/',
        '/api/lynis/upload/',
        '/admin/api/device/',
    ]
    
    def process_request(self, request):
        """Log incoming requests to sensitive endpoints."""
        if any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
            user = getattr(request, 'user', AnonymousUser())
            username = user.username if not user.is_anonymous else 'anonymous'
            
            logger.info(
                f'AUDIT: {request.method} {request.path} | '
                f'User: {username} | '
                f'IP: {self.get_client_ip(request)} | '
                f'User-Agent: {request.META.get("HTTP_USER_AGENT", "unknown")}'
            )
    
    def process_response(self, request, response):
        """Log responses from sensitive endpoints."""
        if any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
            user = getattr(request, 'user', AnonymousUser())
            username = user.username if not user.is_anonymous else 'anonymous'
            
            logger.info(
                f'AUDIT: {request.method} {request.path} | '
                f'User: {username} | '
                f'Status: {response.status_code}'
            )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

