from typing import List, Dict, Any
from app.models.train import TrainModel
from app.models.log import LogModel
from app.models.alert import AlertModel
from app.utils import calculate_distance
from app.config import DISTANCE_THRESHOLDS, SYSTEM_SENDER_ID, get_current_utc_time

async def check_collision_risk(train1_id: str, train2_id: str) -> Dict[str, Any]:
    """
    Check collision risk between two trains
    
    Args:
        train1_id: First train identifier
        train2_id: Second train identifier
        
    Returns:
        Dict: Collision risk assessment
    """
    # Get latest logs for both trains
    log1 = await LogModel.get_latest_by_train(train1_id)
    log2 = await LogModel.get_latest_by_train(train2_id)
    
    # Initialize result
    result = {
        "train1_id": train1_id,
        "train2_id": train2_id,
        "collision_risk": "none",
        "distance": None,
        "location": None
    }
    
    # Cannot determine collision if missing location data
    if not log1 or not log2 or not log1.get("location") or not log2.get("location"):
        return result
    
    # Calculate distance between trains
    distance = calculate_distance(log1["location"], log2["location"])

    # Use the configured threshold
    if distance < DISTANCE_THRESHOLDS["COLLISION_WARNING"]:
        result["collision_risk"] = "warning"
        # Use midpoint as the collision location
        result["location"] = [
            (log1["location"][0] + log2["location"][0]) / 2,
            (log1["location"][1] + log2["location"][1]) / 2
        ]
    
    result["distance"] = distance
    return result

async def create_collision_alert(collision_risk: Dict[str, Any]) -> str:
    """
    Create an alert for a potential collision
    """
    # Format the message according to the standard format
    message = f"COLLISION_WARNING: Potential collision risk between Train {collision_risk['train1_id']} and Train {collision_risk['train2_id']}"
    
    # Get train references
    train1 = await TrainModel.get_by_train_id(collision_risk["train1_id"])
    train2 = await TrainModel.get_by_train_id(collision_risk["train2_id"])
    
    if not train1 or not train2:
        return None
    
    # Alert for train 1
    alert1_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": str(train1["_id"]),
        "message": message,
        "location": collision_risk["location"],
        "timestamp": get_current_utc_time()  # Changed from IST to UTC
    }
    alert1_id = await AlertModel.create(alert1_data, create_guest_copy=False)
    
    # Alert for train 2
    alert2_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": str(train2["_id"]),
        "message": message,
        "location": collision_risk["location"],
        "timestamp": get_current_utc_time()  # Changed from IST to UTC
    }
    await AlertModel.create(alert2_data, create_guest_copy=False)
    
    # Single guest alert
    guest_alert_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": "680142cff8db812a8b87617d",  # Guest account ID
        "message": message,
        "location": collision_risk["location"],
        "timestamp": get_current_utc_time()  # Changed from IST to UTC
    }
    await AlertModel.create(guest_alert_data, create_guest_copy=False)
    
    return alert1_id

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
                
                # Create alerts for all types of collision risks
                await create_collision_alert(risk)
    
    return collision_risks