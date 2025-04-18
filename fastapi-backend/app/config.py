"""
Configuration module for the application.
Contains environment variables and configuration settings.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    logging.warning("MONGODB_URL not set in environment variables. Using default value.")
    MONGODB_URL = "mongodb+srv://cluster0.yaazbsw.mongodb.net/"
    
DB_NAME = os.getenv("DB_NAME", "iot-project")

# API settings
API_PREFIX = "/api"
API_TITLE = "Train Collision Avoidance System API"
API_DESCRIPTION = "API for IoT-based Train Collision Avoidance System using GPS and RFID technology"
API_VERSION = "1.0.0"

# CORS settings
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")

# Train status constants
TRAIN_STATUS = {
    "IN_SERVICE_RUNNING": "in_service_running",
    "IN_SERVICE_NOT_RUNNING": "in_service_not_running",
    "MAINTENANCE": "maintenance",
    "OUT_OF_SERVICE": "out_of_service"
}

# IST timezone settings
IST = timezone(timedelta(hours=5, minutes=30))

# System identifiers for alerts
SYSTEM_SENDER_ID = os.getenv("SYSTEM_SENDER_ID", "680142a4f8db812a8b87617c")
GUEST_RECIPIENT_ID = os.getenv("GUEST_RECIPIENT_ID", "680142cff8db812a8b87617d")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def get_current_ist_time():
    """Returns current time in IST timezone"""
    return datetime.now(IST)

def configure_logging():
    """Configure application logging based on settings"""
    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Logging configured with level: {LOG_LEVEL}")
