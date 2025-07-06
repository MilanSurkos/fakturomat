"""
ASGI config for project1 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project1.settings')

application = get_asgi_application()

# This is used by Render to run the application with daphne/uvicorn
if __name__ == "__main__":
    import uvicorn
    
    # Use PORT environment variable if available, otherwise default to 8000 for local development
    port = int(os.environ.get('PORT', '8000'))
    uvicorn.run(
        "project1.asgi:application",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
