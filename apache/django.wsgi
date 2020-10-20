import os
import sys
sys.path.append(os.path.split(os.path.split(os.path.abspath(__file__))[0])[0])
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.hegenv'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
