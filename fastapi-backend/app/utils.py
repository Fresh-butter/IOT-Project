"""
Utility functions for the application.
"""

from datetime import datetime, timezone, timedelta
import re
from fastapi import HTTPException, status
from app.config import IST
from typing import Optional, List, Dict, Any, Union, Tuple, Callable
import functools
import math
import logging
import traceback

logger = logging.getLogger("app.utils")

def round_coordinates(lat: Union[float, List[float], Tuple[float, float]], lon: Optional[float] = None, precision: int = 5) -> Union[List[float], Tuple[float, float]]:
    """
    Round latitude and longitude to the specified precision
    """
    # Handle case when input is already a tuple
    if isinstance(lat, tuple):
        return lat
        
    if isinstance(lat, list) and len(lat) == 2:
        lon, lat = lat  # Swap since the format is [lon, lat]
    return round(lat, precision), round(lon, precision)

def normalize_timestamp(timestamp: Union[str, datetime]) -> datetime:
    """
    Convert timestamp string to datetime object with IST timezone
    If already a datetime object, ensure it has IST timezone
    
    Args:
        timestamp: Timestamp as string or datetime object
        
    Returns:
        Normalized datetime object with IST timezone
    """
    ist = timezone(timedelta(hours=5, minutes=30))
    
    if isinstance(timestamp, str):
        try:
            # Parse string to datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # If timezone is not specified, assume it's already IST
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ist)
            # If timezone is specified but not IST, convert to IST
            elif dt.tzinfo != ist:
                dt = dt.astimezone(ist)
                
            return dt
        except ValueError:
            # For unparseable strings, return current IST time
            return get_current_ist_time()
            
    # If already a datetime
    if timestamp.tzinfo is None:
        # If no timezone, assume IST
        return timestamp.replace(tzinfo=ist)
    elif timestamp.tzinfo != ist:
        # If different timezone, convert to IST
        return timestamp.astimezone(ist)
        
    # Already has IST timezone
    return timestamp

def handle_exceptions(operation_name: str):
    """
    Decorator that handles exceptions for route handlers.
    
    Args:
        operation_name: A description of the operation being performed (for error messages)
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                logger.warning(f"Validation error while {operation_name}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            except HTTPException:
                # Re-raise HTTP exceptions as they already have the correct format
                raise
            except Exception as e:
                # Log the full traceback for debugging
                logger.error(f"Error while {operation_name}: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An error occurred while {operation_name}"
                )
        return wrapper
    return decorator

def calculate_distance(coord1, coord2):
    """
    Calculate the distance between two coordinates in meters
    
    Args:
        coord1: [longitude, latitude] of first point
        coord2: [longitude, latitude] of second point
        
    Returns:
        float: Distance in meters
    """
    # Basic implementation - can be enhanced with more accurate calculations
    import math
    
    # Convert to radians
    lon1, lat1 = math.radians(coord1[0]), math.radians(coord1[1])
    lon2, lat2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Earth radius in meters
    
    return c * r

def custom_json_encoder(obj):
    """
    Custom JSON encoder to properly handle datetime objects with timezone
    """
    if isinstance(obj, datetime):
        # Format datetime with ISO 8601 format including timezone
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Then include this in your FastAPI app initialization:
# app = FastAPI(..., json_encoders={datetime: custom_json_encoder})