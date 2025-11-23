"""WSGI config for API process"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trikusec.settings.api')
application = get_wsgi_application()



