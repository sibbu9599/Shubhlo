import sys
import os

# Add parent directory to path so app.py is accessible
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel entrypoints (supports both WSGI app and handler conventions)
app.debug = False
handler = app
