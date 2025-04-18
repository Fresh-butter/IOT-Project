"""
Location utilities module.
Provides functions for GPS and RFID data processing.
"""
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import math
from app.utils import calculate_distance, round_coordinates
from app.models.log import LogModel
from app.models.route import RouteModel

def is_point_near_line(point: List[float], line_start: List[float], line_end: List[float], 
                       max_distance: float = 100.0) -> bool:
    """
    Check if a point is within a specified distance of a line segment
    
    Args:
        point: The point to check [longitude, latitude]
        line_start: Starting point of the line segment [longitude, latitude]
        line_end: Ending point of the line segment [longitude, latitude]
        max_distance: Maximum distance in meters to consider "near"
        
    Returns:
        bool: True if the point is within max_distance of the line segment
    """
    # Calculate distances
    d_point_to_start = calculate_distance(point, line_start)
    d_point_to_end = calculate_distance(point, line_end)
    d_start_to_end = calculate_distance(line_start, line_end)
    
    # If either end of the line is very close to the point, return True
    if d_point_to_start <= max_distance or d_point_to_end <= max_distance:
        return True
    
    # Handle case where line segment is very short
    if d_start_to_end < 1.0:
        return d_point_to_start <= max_distance
    
    # Calculate the projection of the point onto the line segment
    # using vector math to find the closest point on the line
    t = ((point[0] - line_start[0]) * (line_end[0] - line_start[0]) + 
         (point[1] - line_start[1]) * (line_end[1] - line_start[1])) / (d_start_to_end ** 2)
    
    # If t is outside [0,1], the closest point is one of the endpoints
    if t < 0:
        return d_point_to_start <= max_distance
    if t > 1:
        return d_point_to_end <= max_distance
    
    # Calculate the closest point on the line segment
    closest_point = [
        line_start[0] + t * (line_end[0] - line_start[0]),
        line_start[1] + t * (line_end[1] - line_start[1])
    ]
    
    # Calculate distance from the point to the closest point on the line
    d_point_to_line = calculate_distance(point, closest_point)
    
    return d_point_to_line <= max_distance

async def find_nearest_checkpoint(location: List[float], route_id: str) -> Tuple[Optional[Dict], int]:
    """
    Find the nearest checkpoint on a route to a given location
    
    Args:
        location: Current location [longitude, latitude]
        route_id: Route identifier
        
    Returns:
        Tuple[Dict, int]: The nearest checkpoint and its index in the route's checkpoints list,
                         or (None, -1) if route not found or has no checkpoints
    """
    route = await RouteModel.get_by_route_id(route_id)
    if not route or not route.get("checkpoints"):
        return None, -1
    
    checkpoints = route["checkpoints"]
    nearest_checkpoint = None
    nearest_index = -1
    min_distance = float('inf')
    
    for i, checkpoint in enumerate(checkpoints):
        checkpoint_location = checkpoint.get("location")
        if not checkpoint_location:
            continue
            
        distance = calculate_distance(location, checkpoint_location)
        if distance < min_distance:
            min_distance = distance
            nearest_checkpoint = checkpoint
            nearest_index = i
    
    return nearest_checkpoint, nearest_index

async def get_expected_location(train_id: str, current_time: Optional[datetime] = None) -> Optional[List[float]]:
    """
    Calculate expected location of a train based on its route and the elapsed time
    
    Args:
        train_id: Train identifier
        current_time: Time to calculate for (defaults to current time)
        
    Returns:
        List[float]: Expected [longitude, latitude] or None if not determinable
    """
    from app.models.train import TrainModel
    
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    if not train or not train.get("current_route_id"):
        return None
    
    # Get route details
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("checkpoints") or len(route["checkpoints"]) < 2:
        return None
    
    # Get most recent log for actual location and time
    latest_log = await LogModel.get_latest_by_train(train_id)
    if not latest_log or not latest_log.get("timestamp"):
        return None
    
    log_time = latest_log["timestamp"]
    if not current_time:
        from app.config import get_current_ist_time
        current_time = get_current_ist_time()
    
    # Calculate elapsed time since log in seconds
    elapsed_seconds = (current_time - log_time).total_seconds()
    
    # Find nearest checkpoint to last log position
    if latest_log.get("location"):
        nearest_checkpoint, checkpoint_idx = await find_nearest_checkpoint(
            latest_log["location"], 
            train["current_route_id"]
        )
    else:
        return None
    
    if nearest_checkpoint is None or checkpoint_idx == -1:
        return None
    
    # If there's no next checkpoint, we can't interpolate
    if checkpoint_idx >= len(route["checkpoints"]) - 1:
        return route["checkpoints"][-1]["location"]
    
    current_checkpoint = route["checkpoints"][checkpoint_idx]
    next_checkpoint = route["checkpoints"][checkpoint_idx + 1]
    
    # Calculate expected time between checkpoints
    time_between_checkpoints = next_checkpoint["interval"] - current_checkpoint["interval"]
    if time_between_checkpoints <= 0:
        return current_checkpoint["location"]
    
    # Calculate progress ratio between checkpoints
    progress_ratio = min(1.0, elapsed_seconds / time_between_checkpoints)
    
    # Interpolate location between checkpoints
    current_loc = current_checkpoint["location"]
    next_loc = next_checkpoint["location"]
    
    interpolated_location = [
        current_loc[0] + progress_ratio * (next_loc[0] - current_loc[0]),
        current_loc[1] + progress_ratio * (next_loc[1] - current_loc[1])
    ]
    
    # Round to 5 decimal places
    return round_coordinates(interpolated_location)

async def verify_rfid_checkpoint(rfid_tag: str, route_id: str, last_checkpoint_idx: int) -> Optional[Dict]:
    """
    Verify if an RFID tag matches the next expected checkpoint in a route
    
    Args:
        rfid_tag: The RFID tag that was detected
        route_id: Route identifier
        last_checkpoint_idx: Index of the last confirmed checkpoint
        
    Returns:
        Dict: The matching checkpoint or None if no match found
    """
    route = await RouteModel.get_by_route_id(route_id)
    if not route or not route.get("checkpoints"):
        return None
    
    checkpoints = route["checkpoints"]
    
    # Calculate expected next checkpoint index
    expected_idx = last_checkpoint_idx + 1
    
    # If we've reached the end of the route
    if expected_idx >= len(checkpoints):
        return None
    
    # Check if the RFID tag matches what's expected at the next checkpoint
    expected_checkpoint = checkpoints[expected_idx]
    if expected_checkpoint.get("rfid_tag") == rfid_tag:
        return expected_checkpoint
    
    # If not, check if it matches any upcoming checkpoint within reasonable range
    # (e.g., might have missed a checkpoint that didn't have an RFID tag)
    for i in range(expected_idx + 1, min(expected_idx + 3, len(checkpoints))):
        if checkpoints[i].get("rfid_tag") == rfid_tag:
            return checkpoints[i]
    
    return None