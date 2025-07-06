"""
WSGI config for project1 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')

application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), '..', 'staticfiles'))
application.add_files(os.path.join(os.path.dirname(__file__), '..', 'media'), prefix='media/')

# This is used by Render to run the application
if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    import sys
    
    # Use PORT environment variable if available, otherwise default to 8000 for local development
    port = os.environ.get('PORT', '8000')
    execute_from_command_line([sys.argv[0], 'runserver', f'0.0.0.0:{port}'])
