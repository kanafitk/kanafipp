import os
from dotenv import load_dotenv

# Load environment variables from .env (including Telegram credentials)
load_dotenv()

# Import the Flask app instance defined in app.py
from app import app as application  # noqa: F401
