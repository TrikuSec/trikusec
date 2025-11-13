from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def error_response(message, status_code, error_code=None, details=None):
    """Return standardized error response."""
    response_data = {
        'error': {
            'message': message,
            'code': error_code or f'ERR_{status_code}'
        }
    }
    
    if details:
        response_data['error']['details'] = details
    
    logger.warning(f'Error response: {message} (status={status_code}, code={error_code})')
    
    return JsonResponse(response_data, status=status_code)

# Common error responses
def bad_request(message, details=None):
    return error_response(message, 400, 'BAD_REQUEST', details)

def unauthorized(message='Unauthorized'):
    return error_response(message, 401, 'UNAUTHORIZED')

def not_found(message='Resource not found'):
    return error_response(message, 404, 'NOT_FOUND')

def internal_error(message='Internal server error'):
    return error_response(message, 500, 'INTERNAL_ERROR')

