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
    Convert timestamp string to datetime object or return as is if already datetime
    
    Args:
        timestamp: Timestamp as string or datetime object
        
    Returns:
        Normalized datetime object
    """
    if isinstance(timestamp, str):
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
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