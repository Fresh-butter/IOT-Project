"""
Configuration module for the application.
Contains environment variables and configuration settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://cluster0.yaazbsw.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "iot-project")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
