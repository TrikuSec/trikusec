import functools
from django.core.cache import cache
from django.http import HttpResponse


def ratelimit(key='ip', rate='100/h'):
    """Simple rate limiter using Django's cache framework."""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped(request, *args, **kwargs):
            # Parse rate string (e.g. '100/h' -> 100 per 3600s)
            num, period = rate.split('/')
            num = int(num)
            seconds = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period]

            # Build cache key from IP
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            if not ip:
                ip = request.META.get('REMOTE_ADDR', '')
            cache_key = f'ratelimit:{view_func.__name__}:{ip}'

            # Check and increment
            count = cache.get(cache_key, 0)
            if count >= num:
                return HttpResponse('Rate limit exceeded', status=429)
            cache.set(cache_key, count + 1, seconds)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
