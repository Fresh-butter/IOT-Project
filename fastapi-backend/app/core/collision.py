"""
Collision detection module.
Provides algorithms for detecting potential train collisions.
"""
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from app.models.log import LogModel
from app.models.train import TrainModel
from app.models.route import RouteModel
from app.models.alert import AlertModel
from app.config import get_current_ist_time, SYSTEM_SENDER_ID, COLLISION_WARNING_DISTANCE, COLLISION_CRITICAL_DISTANCE
from app.utils import calculate_distance
from app.core.location import get_expected_location, is_point_near_line

async def check_collision_risk(train_id1: str, train_id2: str) -> Dict[str, Any]:
    """
    Check the collision risk between two trains
    
    Args:
        train_id1: First train identifier
        train_id2: Second train identifier
        
    Returns:
        Dict: Collision risk assessment
    """
    # Get the latest logs for both trains
    latest_log1 = await LogModel.get_latest_by_train(train_id1)
    latest_log2 = await LogModel.get_latest_by_train(train_id2)
    
    # Default response
    result = {
        "train1_id": train_id1,
        "train2_id": train_id2,
        "collision_risk": "none",
        "distance": None,
        "estimated_time_to_collision": None,
        "location": None,
        "timestamp": get_current_ist_time()
    }
    
    # Check if we have valid location data for both trains
    if (not latest_log1 or not latest_log1.get("location") or 
        not latest_log2 or not latest_log2.get("location")):
        return result
    
    # Calculate current distance between trains
    current_distance = calculate_distance(
        latest_log1["location"], 
        latest_log2["location"]
    )
    result["distance"] = current_distance
    
    # Check immediate collision risk based on current distance
    if current_distance <= COLLISION_CRITICAL_DISTANCE:
        result["collision_risk"] = "critical"
        result["location"] = [
            (latest_log1["location"][0] + latest_log2["location"][0]) / 2,
            (latest_log1["location"][1] + latest_log2["location"][1]) / 2
        ]
        return result
    elif current_distance <= COLLISION_WARNING_DISTANCE:
        result["collision_risk"] = "warning"
        result["location"] = [
            (latest_log1["location"][0] + latest_log2["location"][0]) / 2,
            (latest_log1["location"][1] + latest_log2["location"][1]) / 2
        ]
        
    # Calculate expected future positions
    time_offsets = [5, 10, 15, 30, 60]  # minutes
    for minutes in time_offsets:
        future_time = get_current_ist_time() + timedelta(minutes=minutes)
        
        # Get expected locations at the future time
        expected_loc1 = await get_expected_location(train_id1, future_time)
        expected_loc2 = await get_expected_location(train_id2, future_time)
        
        if not expected_loc1 or not expected_loc2:
            continue
        
        # Calculate expected distance at that time
        future_distance = calculate_distance(expected_loc1, expected_loc2)
        
        # Check for collision risk at future time
        if future_distance <= COLLISION_CRITICAL_DISTANCE:
            result["collision_risk"] = "predicted"
            result["estimated_time_to_collision"] = minutes * 60  # in seconds
            result["location"] = [
                (expected_loc1[0] + expected_loc2[0]) / 2,
                (expected_loc1[1] + expected_loc2[1]) / 2
            ]
            break
    
    return result

async def check_all_train_collisions() -> List[Dict[str, Any]]:
    """
    Check collision risks between all active trains
    
    Returns:
        List[Dict]: List of collision risk assessments
    """
    active_trains = await TrainModel.get_active_trains()
    collision_risks = []
    
    # Compare each pair of trains
    for i in range(len(active_trains)):
        for j in range(i + 1, len(active_trains)):
            train1_id = active_trains[i]["train_id"]
            train2_id = active_trains[j]["train_id"]
            
            risk = await check_collision_risk(train1_id, train2_id)
            
            # Only include risks that aren't 'none'
            if risk["collision_risk"] != "none":
                collision_risks.append(risk)
                
                # If we found a critical or predicted collision, create an alert
                if risk["collision_risk"] in ["critical", "predicted"]:
                    await create_collision_alert(risk)
    
    return collision_risks

async def create_collision_alert(collision_risk: Dict[str, Any]) -> str:
    """
    Create an alert for a potential collision
    
    Args:
        collision_risk: Collision risk assessment
        
    Returns:
        str: ID of the created alert
    """
    # Craft appropriate message based on risk level
    if collision_risk["collision_risk"] == "critical":
        message = f"CRITICAL: Imminent collision risk between trains {collision_risk['train1_id']} and {collision_risk['train2_id']}. Current distance: {int(collision_risk['distance'])}m."
    else:  # predicted
        minutes = int(collision_risk["estimated_time_to_collision"] / 60)
        message = f"WARNING: Potential collision between trains {collision_risk['train1_id']} and {collision_risk['train2_id']} in approximately {minutes} minutes."
    
    # Create alerts for both trains
    alerts = []
    train1_ref = (await TrainModel.get_by_train_id(collision_risk["train1_id"]))["_id"]
    train2_ref = (await TrainModel.get_by_train_id(collision_risk["train2_id"]))["_id"]
    
    # Alert for train 1
    alert1_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": str(train1_ref),
        "message": message,
        "location": collision_risk["location"],
        "timestamp": get_current_ist_time()
    }
    alert1_id = await AlertModel.create(alert1_data)
    alerts.append(alert1_id)
    
    # Alert for train 2
    alert2_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": str(train2_ref),
        "message": message,
        "location": collision_risk["location"],
        "timestamp": get_current_ist_time()
    }
    alert2_id = await AlertModel.create(alert2_data)
    alerts.append(alert2_id)
    
    return alerts[0]  # Return the first alert ID

async def analyze_route_collision_risks(route_id: str) -> List[Dict[str, Any]]:
    """
    Analyze potential collision risks along a route
    
    Args:
        route_id: Route identifier
        
    Returns:
        List[Dict]: List of identified risk points
    """
    from app.core.tracking import detect_route_deviations
    
    route = await RouteModel.get_by_route_id(route_id)
    if not route or not route.get("checkpoints") or len(route["checkpoints"]) < 2:
        return []
    
    # Get all active trains except the one assigned to this route
    active_trains = await TrainModel.get_active_trains()
    assigned_train_id = route.get("assigned_train_id")
    
    other_active_trains = [t for t in active_trains if t["train_id"] != assigned_train_id]
    risk_points = []
    
    # For each other active train, check if it's crossing our route
    for train in other_active_trains:
        # Use the route deviation detection with this route's segments
        for i in range(len(route["checkpoints"]) - 1):
            segment_start = route["checkpoints"][i]["location"]
            segment_end = route["checkpoints"][i+1]["location"]
            
            # Check if train might cross this segment
            train_position = await get_train_position(train["train_id"])
            
            if train_position.get("location"):
                # Check if train is near this segment
                near_segment = is_point_near_line(
                    train_position["location"],
                    segment_start,
                    segment_end,
                    max_distance=100.0
                )
                
                if near_segment:
                    risk = {
                        "train_id": train["train_id"],
                        "route_id": route_id,
                        "segment": [i, i+1],
                        "collision_risk": "warning",
                        "location": train_position["location"],
                        "timestamp": get_current_ist_time()
                    }
                    
                    # Calculate approximate distance
                    risk["distance"] = min_distance_point_to_line(
                        train_position["location"],
                        segment_start,
                        segment_end
                    )
                    
                    risk_points.append(risk)
    
    return risk_points