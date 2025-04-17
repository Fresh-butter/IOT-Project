"""
Configuration module for the application.
Contains environment variables and configuration settings.
"""
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://cluster0.yaazbsw.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "iot-project")

# IST timezone settings
IST = timezone(timedelta(hours=5, minutes=30))

def get_current_ist_time():
    """Returns current time in IST timezone"""
    return datetime.now(IST)
