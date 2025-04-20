"""
Utility functions for the application.
"""
from typing import List, Dict, Any, Callable, Awaitable, TypeVar, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
import math
import functools
import logging
import traceback

from app.config import IST
from app.database import is_connected

T = TypeVar('T')

def round_coordinates(coords, precision: int = 5):
    """
    Round coordinates to reduce precision noise
    
    Supports both formats:
    - List format: [longitude, latitude]
    - Dict format: {'lng': longitude, 'lat': latitude}
    """
    # Handle empty input
    if not coords:
        return coords
    
    # For dictionary format (common in GPS data)
    if isinstance(coords, dict):
        if 'lat' in coords and 'lng' in coords:
            return {
                'lat': round(coords['lat'], precision),
                'lng': round(coords['lng'], precision)
            }
        return coords
    
    # For list format [lng, lat]
    if isinstance(coords, list) and len(coords) == 2:
        return [round(coords[0], precision), round(coords[1], precision)]
    
    # Return original if format not recognized
    return coords

def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Calculate distance between two points in meters using Haversine formula
    """
    # Convert decimal degrees to radians
    lat1 = math.radians(point1[1])
    lon1 = math.radians(point1[0])
    lat2 = math.radians(point2[1])
    lon2 = math.radians(point2[0])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r

def normalize_timestamp(dt: datetime) -> datetime:
    """
    Normalize a timestamp to ensure it has UTC timezone information.
    If the timestamp is timezone-naive, assume it's UTC and add timezone info.
    If the timestamp already has timezone info, convert to UTC.
    """
    if dt is None:
        return None
        
    # If datetime has no timezone, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # Otherwise convert to UTC
    else:
        dt = dt.astimezone(timezone.utc)
        
    return dt

def format_timestamp_ist(dt: Optional[datetime]) -> Optional[str]:
    """
    Format a datetime for API response in IST timezone with proper ISO format
    """
    if dt is None:
        return None
        
    # Normalize to UTC first (in case it's naive or in a different timezone)
    dt = normalize_timestamp(dt)
    
    # Convert to IST for display
    ist_dt = dt.astimezone(IST)
    
    # Format with proper ISO 8601 notation including timezone
    return ist_dt.isoformat()

def handle_exceptions(operation_name: str):
    """
    Decorator for handling exceptions in route handlers
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as they are already formatted correctly
                raise
            except Exception as e:
                logger = logging.getLogger("app.utils")
                logger.error(f"Error {operation_name}: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"An error occurred while {operation_name}")
        return wrapper
    return decorator

def check_db_connection() -> bool:
    """
    Safely check if database connection is established
    Returns True if connected, False otherwise
    """
    try:
        return is_connected()
    except Exception as e:
        logging.error(f"Error checking database connection: {str(e)}")
        return False