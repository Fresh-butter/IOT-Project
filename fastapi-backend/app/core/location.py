from typing import List, Dict, Any, Optional
from app.models.train import TrainModel
from app.models.route import RouteModel
from app.models.log import LogOperations
from app.models.alert import AlertModel
from app.utils import calculate_distance
from app.config import DISTANCE_THRESHOLDS, SYSTEM_SENDER_ID, get_current_utc_time

async def calculate_distance_to_route(location: List[float], route_checkpoints: List[Dict]) -> float:
    """
    Calculate minimum distance from a location to a route (defined by checkpoints)
    
    Args:
        location: [longitude, latitude] coordinates
        route_checkpoints: List of checkpoint dictionaries with 'location' field
        
    Returns:
        float: Minimum distance in meters
    """
    if not location or not route_checkpoints:
        return float('inf')
    
    # Calculate distance to each line segment in the route
    min_distance = float('inf')
    
    for i in range(len(route_checkpoints) - 1):
        cp1_loc = route_checkpoints[i].get("location")
        cp2_loc = route_checkpoints[i + 1].get("location")
        
        if not cp1_loc or not cp2_loc:
            continue
        
        # Simple approach - find distance to each line segment
        # by calculating distance to each endpoint
        d1 = calculate_distance(location, cp1_loc)
        d2 = calculate_distance(location, cp2_loc)
        
        segment_min = min(d1, d2)
        min_distance = min(min_distance, segment_min)
    
    return min_distance

async def detect_route_deviations(train_id: str, distance_threshold: float = None) -> Dict[str, Any]:
    """
    Detect if a train has deviated from its assigned route
    
    Args:
        train_id: Train identifier
        distance_threshold: Maximum allowed distance from route (meters)
        
    Returns:
        Dict: Route deviation assessment
    """
    # Use configured threshold if none provided
    if distance_threshold is None:
        distance_threshold = DISTANCE_THRESHOLDS["ROUTE_DEVIATION"]
        
    train = await TrainModel.get_by_train_id(train_id)
    if not train or not train.get("current_route_id"):
        return {
            "train_id": train_id,
            "deviation_detected": False,
            "message": "No route assigned"
        }
    
    # Get route details
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("checkpoints"):
        return {
            "train_id": train_id,
            "deviation_detected": False,
            "message": "Route has no checkpoints"
        }
    
    # Get latest log entry with location data
    latest_log = await LogOperations.get_latest_by_train(train_id)
    if not latest_log or not latest_log.get("location"):
        return {
            "train_id": train_id,
            "deviation_detected": False,
            "message": "No location data available"
        }
    
    # Calculate distance from route
    distance = await calculate_distance_to_route(latest_log["location"], route["checkpoints"])
    
    # Determine if deviation exists
    deviation_detected = distance > distance_threshold
    
    result = {
        "train_id": train_id,
        "deviation_detected": deviation_detected,
        "distance_from_route": distance,
        "location": latest_log["location"],
        "timestamp": latest_log["timestamp"]
    }
    
    # Create alert if deviation detected
    if deviation_detected:
        message = f"DEVIATION_WARNING: Train {train_id} deviated from route {train['current_route_id']} by {int(distance)}m"
        
        # Alert for the train
        train_alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": str(train["_id"]),
            "message": message,
            "location": latest_log["location"],
            "timestamp": get_current_utc_time()  # Changed from IST to UTC
        }
        await AlertModel.create(train_alert_data, create_guest_copy=False)
        
        # Guest alert
        guest_alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": "680142cff8db812a8b87617d",  # Guest account ID
            "message": message,
            "location": latest_log["location"],
            "timestamp": get_current_utc_time()  # Changed from IST to UTC
        }
        await AlertModel.create(guest_alert_data, create_guest_copy=False)
    
    return result

async def check_deviation_resolved(train_id: str) -> Optional[str]:
    """
    Check if a previously detected route deviation has been resolved
    
    Args:
        train_id: Train identifier
        
    Returns:
        Optional[str]: Alert ID if deviation resolved, None otherwise
    """
    # Get current deviation status
    current_status = await detect_route_deviations(train_id)
    
    # If there's no currently detected deviation, check if there was a previous one
    if not current_status.get("deviation_detected"):
        # Find recent deviation alerts for this train
        train = await TrainModel.get_by_train_id(train_id)
        if not train:
            return None
            
        alerts = await AlertModel.get_by_recipient(str(train["_id"]))
        
        # Look for recent deviation alerts
        deviation_alerts = [
            alert for alert in alerts 
            if "DEVIATION_WARNING" in alert.get("message", "") and "resolved" not in alert.get("message", "").lower()
        ]
        
        # If there were deviation alerts, create a resolution alert
        if deviation_alerts:
            message = f"DEVIATION_RESOLVED: Train {train_id} is back on its assigned route"
            
            # Alert for the train
            train_alert_data = {
                "sender_ref": SYSTEM_SENDER_ID,
                "recipient_ref": str(train["_id"]),
                "message": message,
                "location": current_status.get("location"),
                "timestamp": get_current_utc_time()  # Changed from IST to UTC
            }
            alert_id = await AlertModel.create(train_alert_data, create_guest_copy=False)
            
            # Guest alert
            guest_alert_data = {
                "sender_ref": SYSTEM_SENDER_ID,
                "recipient_ref": "680142cff8db812a8b87617d",  # Guest account ID
                "message": message,
                "location": current_status.get("location"),
                "timestamp": get_current_utc_time()  # Changed from IST to UTC
            }
            await AlertModel.create(guest_alert_data, create_guest_copy=False)
            
            return alert_id
    
    return None