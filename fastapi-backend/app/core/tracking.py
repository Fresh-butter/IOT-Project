"""
Train tracking module.
Provides functions for tracking train movement and status.
"""
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from app.models.log import LogModel
from app.models.train import TrainModel
from app.models.route import RouteModel
from app.config import get_current_ist_time, TRAIN_STATUS
from app.utils import calculate_distance
from app.core.location import find_nearest_checkpoint, verify_rfid_checkpoint

async def get_train_position(train_id: str) -> Dict[str, Any]:
    """
    Get the current position information for a train
    
    Args:
        train_id: Train identifier
        
    Returns:
        Dict: Information about the train's current position and status
    """
    # Get the most recent log for the train
    latest_log = await LogModel.get_latest_by_train(train_id)
    
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    
    result = {
        "train_id": train_id,
        "timestamp": get_current_ist_time(),
        "has_valid_position": False,
        "location": None,
        "last_update": None,
        "status": train.get("current_status") if train else None,
        "route_id": train.get("current_route_id") if train else None,
        "nearest_checkpoint": None,
        "checkpoint_index": -1,
        "next_checkpoint": None
    }
    
    if not latest_log or not train:
        return result
    
    # Update result with log information
    if latest_log.get("location"):
        result["has_valid_position"] = True
        result["location"] = latest_log["location"]
        result["last_update"] = latest_log["timestamp"]
        
        # If train has a route, get checkpoint information
        if train.get("current_route_id"):
            nearest_cp, cp_idx = await find_nearest_checkpoint(
                latest_log["location"], 
                train["current_route_id"]
            )
            
            result["nearest_checkpoint"] = nearest_cp
            result["checkpoint_index"] = cp_idx
            
            # If there's a next checkpoint, include it
            route = await RouteModel.get_by_route_id(train["current_route_id"])
            if route and route.get("checkpoints") and cp_idx < len(route["checkpoints"]) - 1:
                result["next_checkpoint"] = route["checkpoints"][cp_idx + 1]
    
    return result

async def is_train_on_schedule(train_id: str, tolerance_seconds: int = 300) -> Dict[str, Any]:
    """
    Check if a train is running on schedule based on expected position vs actual position
    
    Args:
        train_id: Train identifier
        tolerance_seconds: Acceptable delay in seconds
        
    Returns:
        Dict: Information about the train's schedule adherence
    """
    position_info = await get_train_position(train_id)
    
    result = {
        "train_id": train_id,
        "on_schedule": False,
        "delay_seconds": None,
        "scheduled_checkpoint": None,
        "actual_checkpoint": position_info.get("nearest_checkpoint"),
        "location": position_info.get("location")
    }
    
    if not position_info.get("has_valid_position") or not position_info.get("route_id"):
        return result
    
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    if not train or not train.get("current_route_id"):
        return result
    
    # Get route details
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("start_time") or not route.get("checkpoints"):
        return result
    
    # Calculate expected checkpoint based on elapsed time since route start
    current_time = get_current_ist_time()
    elapsed_seconds = (current_time - route["start_time"]).total_seconds()
    
    # Find expected checkpoint based on elapsed time
    expected_cp = None
    expected_cp_idx = -1
    
    for i, cp in enumerate(route["checkpoints"]):
        if elapsed_seconds < cp["interval"]:
            if i > 0:
                expected_cp = route["checkpoints"][i-1]
                expected_cp_idx = i-1
            break
    
    # If we've gone through all checkpoints, use the last one
    if expected_cp is None and route["checkpoints"]:
        expected_cp = route["checkpoints"][-1]
        expected_cp_idx = len(route["checkpoints"]) - 1
    
    result["scheduled_checkpoint"] = expected_cp
    
    # If we have a valid expected checkpoint, compare with actual position
    if expected_cp and position_info.get("checkpoint_index") is not None:
        actual_cp_idx = position_info["checkpoint_index"]
        
        # Check if current checkpoint is behind expected
        if actual_cp_idx < expected_cp_idx:
            # Calculate delay based on difference in checkpoints
            delay = 0
            for i in range(actual_cp_idx + 1, expected_cp_idx + 1):
                delay += route["checkpoints"][i]["interval"] - route["checkpoints"][i-1]["interval"]
            
            result["delay_seconds"] = delay
            result["on_schedule"] = delay <= tolerance_seconds
        else:
            # Train is at or ahead of schedule
            result["delay_seconds"] = 0
            result["on_schedule"] = True
    
    return result

async def update_train_progress(train_id: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update train progress based on new log data
    
    Args:
        train_id: Train identifier
        log_data: New log data including location and/or RFID
        
    Returns:
        Dict: Updated progress information
    """
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        return {"success": False, "error": "Train not found"}
    
    result = {
        "train_id": train_id,
        "timestamp": get_current_ist_time(),
        "location_updated": False,
        "checkpoint_updated": False,
        "route_completed": False,
        "current_checkpoint": None,
        "checkpoint_index": -1,
        "next_checkpoint": None
    }
    
    # If train doesn't have a route, just record the position
    if not train.get("current_route_id"):
        if log_data.get("location"):
            result["location_updated"] = True
        return result
    
    # Get current progress information
    position_info = await get_train_position(train_id)
    current_cp_idx = position_info.get("checkpoint_index", -1)
    
    # Get route details
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("checkpoints"):
        return {"success": False, "error": "Route not found or invalid"}
    
    # If we have a new RFID reading, verify against expected checkpoints
    if log_data.get("rfid_tag"):
        matched_checkpoint = await verify_rfid_checkpoint(
            log_data["rfid_tag"], 
            train["current_route_id"], 
            current_cp_idx
        )
        
        if matched_checkpoint:
            # Find the index of the matched checkpoint
            for i, cp in enumerate(route["checkpoints"]):
                if cp.get("rfid_tag") == log_data["rfid_tag"]:
                    result["checkpoint_updated"] = True
                    result["current_checkpoint"] = cp
                    result["checkpoint_index"] = i
                    
                    # Check if we've reached the end of the route
                    if i == len(route["checkpoints"]) - 1:
                        result["route_completed"] = True
                    elif i + 1 < len(route["checkpoints"]):
                        result["next_checkpoint"] = route["checkpoints"][i + 1]
                    
                    break
    
    # If we have a new location, update position
    if log_data.get("location"):
        result["location_updated"] = True
        
        # If checkpoint wasn't updated by RFID, try to update based on location
        if not result["checkpoint_updated"]:
            nearest_cp, cp_idx = await find_nearest_checkpoint(
                log_data["location"], 
                train["current_route_id"]
            )
            
            # Only update if we've advanced to a new checkpoint
            if cp_idx > current_cp_idx:
                result["checkpoint_updated"] = True
                result["current_checkpoint"] = nearest_cp
                result["checkpoint_index"] = cp_idx
                
                # Check if we've reached the end of the route
                if cp_idx == len(route["checkpoints"]) - 1:
                    result["route_completed"] = True
                elif cp_idx + 1 < len(route["checkpoints"]):
                    result["next_checkpoint"] = route["checkpoints"][cp_idx + 1]
    
    return result

async def get_active_trains_locations() -> List[Dict[str, Any]]:
    """
    Get current locations of all active trains
    
    Returns:
        List[Dict]: List of active trains with their current locations and status
    """
    active_trains = await TrainModel.get_active_trains()
    results = []
    
    for train in active_trains:
        position_info = await get_train_position(train["train_id"])
        
        if position_info.get("has_valid_position"):
            train_info = {
                "train_id": train["train_id"],
                "name": train.get("name"),
                "location": position_info["location"],
                "last_update": position_info["last_update"],
                "status": train["current_status"],
                "route_id": train.get("current_route_id"),
                "nearest_station": None
            }
            
            # Add nearest station information if available
            if position_info.get("nearest_checkpoint") and position_info["nearest_checkpoint"].get("name"):
                train_info["nearest_station"] = position_info["nearest_checkpoint"]["name"]
            
            results.append(train_info)
    
    return results

async def detect_route_deviations(train_id: str, distance_threshold: float = 100.0) -> Dict[str, Any]:
    """
    Detect if a train has deviated from its assigned route
    
    Args:
        train_id: Train identifier
        distance_threshold: Maximum allowable distance from route in meters
        
    Returns:
        Dict: Assessment of route deviation with details
    """
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    
    result = {
        "train_id": train_id,
        "deviation_detected": False,
        "distance_from_route": None,
        "location": None,
        "timestamp": get_current_ist_time(),
        "nearest_checkpoint": None,
        "expected_segment": None,
        "severity": "none"
    }
    
    if not train or not train.get("current_route_id"):
        return result
    
    # Get the latest log for the train
    latest_log = await LogModel.get_latest_by_train(train_id)
    if not latest_log or not latest_log.get("location"):
        return result
    
    # Get route details
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("checkpoints") or len(route["checkpoints"]) < 2:
        return result
    
    # Find nearest checkpoint and get expected segment
    nearest_cp, cp_idx = await find_nearest_checkpoint(
        latest_log["location"], 
        train["current_route_id"]
    )
    
    result["nearest_checkpoint"] = nearest_cp
    
    # Determine which segment the train should be on
    if cp_idx == -1:
        return result
    
    # Check if train is at the end of the route
    if cp_idx == len(route["checkpoints"]) - 1:
        # No next segment, so no deviation possible
        return result
    
    # Get the current segment the train should be on
    segment_start = route["checkpoints"][cp_idx]["location"]
    segment_end = route["checkpoints"][cp_idx + 1]["location"]
    
    result["expected_segment"] = [cp_idx, cp_idx + 1]
    
    # Check if the train is near this segment
    near_segment = is_point_near_line(
        latest_log["location"],
        segment_start,
        segment_end,
        distance_threshold
    )
    
    if not near_segment:
        # Train has deviated from its route
        result["deviation_detected"] = True
        
        # Calculate minimum distance to the expected segment
        min_distance = float('inf')
        
        # Check distance to current segment
        d_point_to_line = min_distance_point_to_line(
            latest_log["location"],
            segment_start,
            segment_end
        )
        
        min_distance = min(min_distance, d_point_to_line)
        
        # Also check adjacent segments in case train is between segments
        if cp_idx > 0:
            prev_segment_start = route["checkpoints"][cp_idx - 1]["location"]
            prev_segment_end = segment_start
            
            d_point_to_prev = min_distance_point_to_line(
                latest_log["location"],
                prev_segment_start,
                prev_segment_end
            )
            
            min_distance = min(min_distance, d_point_to_prev)
            
        if cp_idx + 2 < len(route["checkpoints"]):
            next_segment_start = segment_end
            next_segment_end = route["checkpoints"][cp_idx + 2]["location"]
            
            d_point_to_next = min_distance_point_to_line(
                latest_log["location"],
                next_segment_start,
                next_segment_end
            )
            
            min_distance = min(min_distance, d_point_to_next)
        
        result["distance_from_route"] = min_distance
        result["location"] = latest_log["location"]
        
        # Determine severity based on distance
        if min_distance > 3 * distance_threshold:
            result["severity"] = "critical"
        elif min_distance > 2 * distance_threshold:
            result["severity"] = "high"
        else:
            result["severity"] = "moderate"
    
    return result

def min_distance_point_to_line(point: List[float], line_start: List[float], line_end: List[float]) -> float:
    """
    Calculate the minimum distance from a point to a line segment
    
    Args:
        point: The point to check [longitude, latitude]
        line_start: Starting point of the line segment [longitude, latitude]
        line_end: Ending point of the line segment [longitude, latitude]
        
    Returns:
        float: Minimum distance in meters from point to line segment
    """
    # Calculate distances
    d_point_to_start = calculate_distance(point, line_start)
    d_point_to_end = calculate_distance(point, line_end)
    d_start_to_end = calculate_distance(line_start, line_end)
    
    # Handle case where line segment is very short
    if d_start_to_end < 1.0:
        return d_point_to_start
    
    # Calculate the projection of the point onto the line segment
    # using vector math to find the closest point on the line
    t = ((point[0] - line_start[0]) * (line_end[0] - line_start[0]) + 
         (point[1] - line_start[1]) * (line_end[1] - line_start[1])) / (d_start_to_end ** 2)
    
    # If t is outside [0,1], the closest point is one of the endpoints
    if t < 0:
        return d_point_to_start
    if t > 1:
        return d_point_to_end
    
    # Calculate the closest point on the line segment
    closest_point = [
        line_start[0] + t * (line_end[0] - line_start[0]),
        line_start[1] + t * (line_end[1] - line_start[1])
    ]
    
    # Calculate distance from the point to the closest point on the line
    return calculate_distance(point, closest_point)