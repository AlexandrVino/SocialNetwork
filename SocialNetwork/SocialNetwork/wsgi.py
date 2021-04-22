"""
WSGI config for chat project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from socketio_app.views import sio
import socketio
import eventlet
import eventlet.wsgi
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SocialNetwork.settings')

application = StaticFilesHandler(get_wsgi_application())
application = socketio.WSGIApp(sio, application)

eventlet.wsgi.server(eventlet.listen(('', 8000)), application)
