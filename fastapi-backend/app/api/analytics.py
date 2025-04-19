"""
Analytics API module.
Provides specialized endpoints for data analysis and reporting.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.train import TrainModel
from app.models.log import LogModel
from app.models.route import RouteModel
from app.models.alert import AlertModel
from app.services.route_service import RouteService
from app.services.alert_service import AlertService
from app.core.tracking import get_active_trains_locations
from app.core.collision import check_all_train_collisions
from app.core.location import detect_route_deviations
from app.config import get_current_ist_time, SYSTEM_SENDER_ID
from app.utils import handle_exceptions
from app.database import get_collection
from app.tasks.monitor import generate_system_status_report

router = APIRouter()

@router.get("/system-status",
           response_model=Dict[str, Any],
           summary="Get system status dashboard",
           description="Provides an overview of the system status, including train counts, active alerts, and recent logs")
@handle_exceptions("retrieving system status")
async def get_system_status(
    hours: int = Query(24, description="Number of hours to include in the report")
):
    """Get system status dashboard"""
    # Get current time minus hours
    last_hour = get_current_ist_time() - timedelta(hours=hours)
    
    # Get recent logs
    recent_logs = await LogModel.get_logs_since(last_hour)
    
    # Count active trains
    trains = await TrainModel.get_all()
    
    # Only access current_status if it exists
    active_trains = []
    for t in trains:
        # Handle both dict and object access
        if isinstance(t, dict):
            if "current_status" in t and t["current_status"] != "out_of_service":
                active_trains.append(t)
        else:
            # For object-like access
            status = getattr(t, "current_status", None)
            if status and status != "out_of_service":
                active_trains.append(t)
    
    # Get total number of alerts for the specified time period
    current_time = get_current_ist_time()
    total_alerts = await get_collection(AlertModel.collection).count_documents(
        {"timestamp": {"$gte": current_time - timedelta(hours=hours)}}
    )
   
    # Create a proper response dict
    response = {
        "timestamp": get_current_ist_time(),
        "hours_included": hours,
        "train_count": {
            "total": len(trains),
            "active": len(active_trains),
            "out_of_service": len(trains) - len(active_trains)
        },
        "total_alerts": total_alerts,
        "log_count": len(recent_logs),
    }
    
    return response

@router.get("/dashboard",
           response_model=Dict[str, Any],
           summary="Get comprehensive dashboard data",
           description="Retrieves all information needed for the dashboard including trains, alerts, and system status")
@handle_exceptions("retrieving dashboard data")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    return await generate_system_status_report()

@router.get("/test-collision",
           response_model=Dict[str, Any],
           summary="Test collision detection",
           description="Manually trigger collision detection to test the system")
@handle_exceptions("running collision test")
async def test_collision_detection():
    """Test collision detection"""
    collision_risks = await check_all_train_collisions()
    return {
        "timestamp": get_current_ist_time(),
        "collision_risks_detected": len(collision_risks),
        "risks": collision_risks
    }

@router.get("/test-deviation/{train_id}",
           response_model=Dict[str, Any],
           summary="Test route deviation detection",
           description="Manually check if a train has deviated from its route")
@handle_exceptions("testing route deviation")
async def test_route_deviation(train_id: str):
    """Test route deviation detection for a specific train"""
    deviation = await detect_route_deviations(train_id)
    return {
        "timestamp": get_current_ist_time(),
        "train_id": train_id,
        "result": deviation
    }

@router.post("/simulate-alert",
            response_model=Dict[str, Any],
            summary="Simulate system alert",
            description="Create a test system alert to verify alert functionality")
@handle_exceptions("simulating system alert")
async def simulate_system_alert(
    recipient_train_id: str = Query(..., description="Train ID to receive the alert"),
    alert_type: str = Query("SYSTEM_WARNING", description="Alert type (COLLISION_WARNING, DEVIATION_WARNING, etc.)"),
    message: str = Query("Test system alert", description="Custom alert message")
):
    """Simulate a system alert for testing"""
    # Get train reference
    train = await TrainModel.get_by_train_id(recipient_train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train with ID {recipient_train_id} not found")
    
    # Format the alert message based on type
    if alert_type == "COLLISION_WARNING":
        full_message = f"COLLISION_WARNING: Potential collision risk between Train {recipient_train_id} and Train TEST"
    elif alert_type == "DEVIATION_WARNING":
        full_message = f"DEVIATION_WARNING: Train {recipient_train_id} deviated from route TEST by 150m"
    elif alert_type == "TRAIN_STOPPED":
        full_message = f"TRAIN_STOPPED: Train {recipient_train_id} stopped at current location"
    elif alert_type == "TRAIN_RESUMED":
        full_message = f"TRAIN_RESUMED: Train {recipient_train_id} resumed operation"
    else:
        full_message = f"SYSTEM_WARNING: {message}"
    
    # Get most recent train location or use default
    latest_log = await LogModel.get_latest_by_train(recipient_train_id)
    location = latest_log.get("location") if latest_log and latest_log.get("location") else [77.0, 28.0]
    
    # Create train alert
    train_alert_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": str(train["_id"]),
        "message": full_message,
        "location": location,
        "timestamp": get_current_ist_time()
    }
    train_alert_id = await AlertModel.create(train_alert_data, create_guest_copy=False)
    
    # Create guest alert
    guest_alert_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": "680142cff8db812a8b87617d",  # Guest account ID
        "message": full_message,
        "location": location,
        "timestamp": get_current_ist_time()
    }
    await AlertModel.create(guest_alert_data, create_guest_copy=False)
    
    return {
        "success": True,
        "alert_id": train_alert_id,
        "timestamp": get_current_ist_time(),
        "message": full_message,
        "recipient_train_id": recipient_train_id
    }

