import os
import sys

# Add the project root to the Python path
# This allows the app to be found when run by a WSGI server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app

application = create_app()
