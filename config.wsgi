import os
from dotenv import load_dotenv

# Load environment variables from the.env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app

# Create the application instance for the production environment
# The 'production' key maps to the ProductionConfig class in config.py
application = create_app(os.getenv('FLASK_CONFIG') or 'production')