"""
Train tracking module.
Implements logic to track train movements, detect stops, and monitor status.
"""
from typing import List, Dict, Any, Optional
from app.models.train import TrainModel
from app.models.route import RouteModel
from app.models.log import LogOperations  # Changed from LogModel to LogOperations
from app.models.alert import AlertModel
from app.utils import calculate_distance
from app.config import SYSTEM_SENDER_ID, TRAIN_STATUS, DISTANCE_THRESHOLDS, GUEST_RECIPIENT_ID, get_current_ist_time
from app.core.location import detect_route_deviations, check_deviation_resolved

async def get_active_trains_locations() -> List[Dict[str, Any]]:
    """
    Get latest locations for all active trains
    
    Returns:
        List[Dict]: List of train locations with metadata
    """
    active_trains = await TrainModel.get_active_trains()
    locations = []
    
    for train in active_trains:
        latest_log = await LogOperations.get_latest_by_train(train["train_id"])  # Changed from LogModel to LogOperations
        if latest_log and latest_log.get("location"):
            locations.append({
                "train_id": train["train_id"],
                "name": train.get("name", f"Train {train['train_id']}"),
                "location": latest_log["location"],
                "timestamp": latest_log["timestamp"],
                "status": train.get("current_status"),
                "route_id": train.get("current_route_id")
            })
    
    return locations

async def detect_train_status_change(train_id: str, movement_threshold: float = 5.0) -> Dict[str, Any]:
    """
    Detect if a train has stopped or resumed movement
    
    Args:
        train_id: Train identifier
        movement_threshold: Minimum distance to consider movement (meters)
        
    Returns:
        Dict: Status change assessment
    """
    # Get last two logs to determine if train has moved
    logs = await LogOperations.get_by_train_id(train_id, limit=2)  # Changed from LogModel to LogOperations
    
    # Need at least 2 logs to detect movement
    if len(logs) < 2:
        return {
            "status_changed": False,
            "message": "Insufficient log data"
        }
    
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        return {
            "status_changed": False,
            "message": "Train not found"
        }
    
    # Check if both logs have location data
    if not logs[0].get("location") or not logs[1].get("location"):
        return {
            "status_changed": False,
            "message": "Missing location data"
        }
    
    # Calculate distance moved
    distance_moved = calculate_distance(logs[0]["location"], logs[1]["location"])
    
    # Determine current status and if it needs to change
    current_status = train.get("current_status")
    status_changed = False
    new_status = current_status
    
    # If train has moved less than threshold between logs and is currently running
    if distance_moved < movement_threshold and current_status == TRAIN_STATUS["IN_SERVICE_RUNNING"]:
        # Train has stopped
        new_status = TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
        status_changed = True
        
        # Create alert message
        message = f"TRAIN_STOPPED: Train {train_id} stopped at {logs[0]['location']}"
        
        # Alert for the train
        train_alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": str(train["_id"]),
            "message": message,
            "location": logs[0]["location"],
            "timestamp": get_current_ist_time()
        }
        await AlertModel.create(train_alert_data, create_guest_copy=False)
        
        # Guest alert
        guest_alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": GUEST_RECIPIENT_ID,
            "message": message,
            "location": logs[0]["location"],
            "timestamp": get_current_ist_time()
        }
        await AlertModel.create(guest_alert_data, create_guest_copy=False)
        
    # If train has moved more than threshold between logs and is currently not running
    elif distance_moved >= movement_threshold and current_status == TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]:
        # Train has resumed
        new_status = TRAIN_STATUS["IN_SERVICE_RUNNING"]
        status_changed = True
        
        # Create alert message
        message = f"TRAIN_RESUMED: Train {train_id} resumed operation"
        
        # Alert for the train
        train_alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": str(train["_id"]),
            "message": message,
            "location": logs[0]["location"],
            "timestamp": get_current_ist_time()
        }
        await AlertModel.create(train_alert_data, create_guest_copy=False)
        
        # Guest alert
        guest_alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": GUEST_RECIPIENT_ID,
            "message": message,
            "location": logs[0]["location"],
            "timestamp": get_current_ist_time()
        }
        await AlertModel.create(guest_alert_data, create_guest_copy=False)
    
    # If status changed, update in database
    if status_changed:
        await TrainModel.update_status(str(train["_id"]), new_status)
    
    return {
        "train_id": train_id,
        "status_changed": status_changed,
        "previous_status": current_status,
        "new_status": new_status,
        "distance_moved": distance_moved,
        "location": logs[0]["location"]
    }

async def update_train_progress(train_id: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update train progress based on new location data
    
    Args:
        train_id: Train identifier
        log_data: Log data including location
        
    Returns:
        Dict: Updated train status
    """
    # Ignore test data
    if log_data.get("test_data") is True:
        return {
            "train_id": train_id,
            "status": "ignored",
            "reason": "Test data ignored"
        }
    
    # Get train details
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        return {
            "train_id": train_id,
            "status": "error",
            "reason": "Train not found"
        }
    
    # Only track trains that are in-service (running or not running)
    current_status = train.get("current_status")
    valid_statuses = [TRAIN_STATUS["IN_SERVICE_RUNNING"], TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]]
    
    if current_status not in valid_statuses:
        return {
            "train_id": train_id,
            "status": "ignored",
            "reason": f"Train status '{current_status}' is not being tracked"
        }
    
    # First check for route deviations
    deviation = await detect_route_deviations(train_id)
    
    # Check if a previous deviation was resolved
    if not deviation.get("deviation_detected"):
        await check_deviation_resolved(train_id)
    
    # Check if train status (stopped/moving) has changed
    status_change = await detect_train_status_change(train_id)
    if status_change.get("status_changed"):
        return {
            "train_id": train_id,
            "status_changed": True,
            "new_status": status_change.get("new_status"),
            "timestamp": get_current_ist_time()
        }
    
    return {
        "train_id": train_id,
        "status": "unchanged",
        "timestamp": get_current_ist_time()
    }