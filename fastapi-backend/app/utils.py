"""
Utility functions for the application.
Contains helper functions used throughout the application.
"""

from datetime import datetime, timezone, timedelta
import re
from fastapi import HTTPException
from app.config import IST
from typing import Optional, List, Dict, Any

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



def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Calculate the Haversine distance between two GPS coordinates in meters
    
    Args:
        point1: List containing [longitude, latitude]
        point2: List containing [longitude, latitude]
        
    Returns:
        float: Distance in meters
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth radius in meters
    R = 6371000
    
    # Extract coordinates
    lon1, lat1 = point1
    lon2, lat2 = point2
    
    # Convert to radians
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    
    # Haversine formula
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c