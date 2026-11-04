import sys
import os

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# WSGI Middleware to guarantee correct PATH_INFO on Vercel
class VercelWSGIMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Extract raw request URI from Vercel headers if rewritten
        raw_uri = (
            environ.get('HTTP_X_FORWARDED_URI') or 
            environ.get('HTTP_X_NOW_ROUTE_MATCHES') or
            environ.get('REQUEST_URI') or
            ''
        )
        if raw_uri:
            # Strip query parameters for clean WSGI path matching
            path = raw_uri.split('?')[0]
            if path and path != '/':
                environ['PATH_INFO'] = path
            elif path == '/':
                environ['PATH_INFO'] = '/home'
        
        # 2. If PATH_INFO is /api/index, /api, or /index, redirect directly to /home
        curr_path = environ.get('PATH_INFO', '')
        if curr_path in ('/api/index', '/api/index.py', '/api', '/index', ''):
            environ['PATH_INFO'] = '/home'
            
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
app.debug = False
handler = app
