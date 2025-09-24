#!/usr/bin/env python3
"""
SettleMate Django Backend with Socket.IO Integration

This file serves as the main entry point for the SettleMate backend application.
It integrates Django with Socket.IO for real-time chat functionality.

Usage:
    python app.py

Requirements:
    - Django 4.2+
    - python-socketio
    - eventlet
    - Redis (for Celery)
"""

import os
import sys
import django
from django.core.wsgi import get_wsgi_application
from django.conf import settings
import socketio
import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settlemate.settings')

# Initialize Django
django.setup()

# Import Socket.IO app after Django is initialized
from api.socketio_app import sio

if __name__ == '__main__':
    # Get Django WSGI application
    django_app = get_wsgi_application()

    # Mount Socket.IO on top of Django so both HTTP and Socket.IO share the same port
    socketio_app = socketio.WSGIApp(sio, django_app)

    print("Starting SettleMate Backend Server (eventlet)...")
    print("Django Admin: http://localhost:8000/admin/")
    print("API Endpoints: http://localhost:8000/api/")
    print("Socket.IO: http://localhost:8000/socket.io/")
    print("Press Ctrl+C to stop the server")

    listener = eventlet.listen(('0.0.0.0', 8000))
    wsgi.server(listener, socketio_app)
