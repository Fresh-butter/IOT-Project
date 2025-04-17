"""
Utility functions for the application.
Contains helper functions used throughout the application.
"""

from datetime import datetime, timezone, timedelta
import re
from fastapi import HTTPException
from app.config import IST

def round_coordinates(coordinates, decimal_places=5):
    """
    Round GPS coordinates to specified decimal places
    
    Args:
        coordinates: List containing [longitude, latitude]
        decimal_places: Number of decimal places to round to (default: 5)
        
    Returns:
        List of rounded coordinates
    """
    if not coordinates or len(coordinates) != 2:
        return coordinates
    return [round(coord, decimal_places) for coord in coordinates]

def normalize_timestamp(timestamp):
    """
    Normalize timestamp to ISO format with IST timezone
    
    Args:
        timestamp: Datetime object or string
        
    Returns:
        datetime: Normalized datetime object with IST timezone
    """
    if isinstance(timestamp, str):
        # Normalize timezone offset format (+05:30 → +0530)
        timestamp = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", timestamp)

        # Try parsing with different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",  # With milliseconds and timezone
            "%Y-%m-%dT%H:%M:%S%z",     # Without milliseconds, with timezone
            "%Y-%m-%dT%H:%M:%S",       # Without timezone (default to IST)
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(timestamp, fmt)
                # Add IST timezone if missing
                if not parsed.tzinfo:
                    parsed = parsed.replace(tzinfo=IST)
                return parsed
            except ValueError:
                continue

        raise ValueError(f"Invalid datetime format: {timestamp}")

    elif isinstance(timestamp, datetime):
        # Handle datetime objects directly
        if not timestamp.tzinfo:
            timestamp = timestamp.replace(tzinfo=IST)
        return timestamp

    raise ValueError("Timestamp must be a string or datetime object")

def handle_exceptions(operation_name, value_error_status=400, general_error_status=500):
    """
    Decorator for standardized exception handling in route functions
    
    Args:
        operation_name: Name of the operation (for error messages)
        value_error_status: Status code for ValueError exceptions
        general_error_status: Status code for general exceptions
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                raise HTTPException(status_code=value_error_status, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=general_error_status, 
                    detail=f"Error {operation_name}: {str(e)}"
                )
        return wrapper
    return decorator

def classify_gps_accuracy(hdop: float = None, satellites: int = None) -> dict:
    """
    Classify GPS accuracy based on HDOP and satellite count
    
    Args:
        hdop: Horizontal Dilution of Precision value
        satellites: Number of satellites used for fix
        
    Returns:
        dict: Classification with category, description and estimated error
    """
    if hdop is None or satellites is None or satellites == 0:
        return {
            "category": "invalid",
            "description": "No GPS fix",
            "error_m": None
        }

    if hdop <= 1.0 and satellites >= 6:
        return {
            "category": "excellent",
            "description": "< 5 meter error",
            "error_m": "<5"
        }
    elif 1.0 < hdop <= 2.0 and satellites >= 5:
        return {
            "category": "good",
            "description": "5–10 meter error",
            "error_m": "5–10"
        }
    elif 2.0 < hdop <= 5.0 and satellites >= 4:
        return {
            "category": "moderate",
            "description": "10–25 meter error",
            "error_m": "10–25"
        }
    elif 5.0 < hdop <= 10.0 and satellites >= 3:
        return {
            "category": "poor",
            "description": "25–50 meter error",
            "error_m": "25–50"
        }
    else:
        return {
            "category": "invalid",
            "description": "> 50 meter error or no fix",
            "error_m": ">50"
        }