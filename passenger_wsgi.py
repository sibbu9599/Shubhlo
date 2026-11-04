import os
import sys

# Ensure current directory is in Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app object as 'application' for cPanel/Passenger/Gunicorn
from app import app as application

if __name__ == "__main__":
    application.run()

