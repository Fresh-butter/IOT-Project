"""
Configuration module for the application.
Contains environment variables and configuration settings.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import asyncio

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

# Alert severity levels
ALERT_SEVERITY = {
    "CRITICAL": "critical",
    "WARNING": "warning",
    "INFO": "info"
}

# Distance thresholds (in meters)
DISTANCE_THRESHOLDS = {
    "COLLISION_CRITICAL": 100,    # Critical collision risk if trains are within 100m
    "COLLISION_WARNING": 500,     # Warning collision risk if trains are within 500m
    "ROUTE_DEVIATION": 100,       # Route deviation if train is 100m from expected path
    "CHECKPOINT_PROXIMITY": 50    # Train is considered at checkpoint if within 50m
}

# Direct distance constants for backward compatibility
COLLISION_CRITICAL_DISTANCE = DISTANCE_THRESHOLDS["COLLISION_CRITICAL"]
COLLISION_WARNING_DISTANCE = DISTANCE_THRESHOLDS["COLLISION_WARNING"]
ROUTE_DEVIATION_DISTANCE = DISTANCE_THRESHOLDS["ROUTE_DEVIATION"]
CHECKPOINT_PROXIMITY_DISTANCE = DISTANCE_THRESHOLDS["CHECKPOINT_PROXIMITY"]

# Time thresholds (in seconds)
TIME_THRESHOLDS = {
    "SCHEDULE_DELAY": 300,        # 5 minutes delay is considered significant
    "LOG_EXPIRY": 30 * 24 * 60 * 60,  # Keep logs for 30 days
    "PREDICTION_WINDOW": 15 * 60  # Predict collisions 15 minutes in advance
}

# Schedule settings
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))
LOG_CLEANUP_DAYS = int(os.getenv("LOG_CLEANUP_DAYS", "30"))

# IST timezone settings
IST = timezone(timedelta(hours=5, minutes=30))

# System identifiers for alerts
SYSTEM_SENDER_ID = os.getenv("SYSTEM_SENDER_ID", "680142a4f8db812a8b87617c")
GUEST_RECIPIENT_ID = os.getenv("GUEST_RECIPIENT_ID", "680142cff8db812a8b87617d")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Monitoring settings
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"

def get_current_ist_time():
    """Returns current time in IST timezone"""
    return datetime.now(IST)

def configure_logging():
    """Configure application logging based on settings"""
    # Create a basic logging configuration
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Set third-party module logging levels to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    
    # Log configuration info
    logging.info(f"Logging configured with level {LOG_LEVEL}")

# Global asyncio event for graceful shutdown of background tasks
monitor_stop_event = asyncio.Event()

# Train collision risk calculation settings
TRAIN_SPEED_DEFAULT = 40  # Default train speed in km/h when not available
MAX_PREDICTION_MINUTES = 30  # Maximum time to look ahead for collision prediction
