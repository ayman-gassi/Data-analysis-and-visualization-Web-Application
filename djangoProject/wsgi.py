import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')

# Debugging: Log the PORT environment variable
port = os.getenv('PORT', '8000')  # Default to 8000 if PORT is not set
print(f"WSGI is binding to PORT: {port}")

application = get_wsgi_application()
