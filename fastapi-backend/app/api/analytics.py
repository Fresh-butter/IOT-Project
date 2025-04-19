"""
Analytics API module.
Provides specialized endpoints for data analysis and reporting.
"""
from fastapi import APIRouter, HTTPException, Body, Query, Path, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.models.train import TrainModel
from app.models.log import LogOperations
from app.models.route import RouteModel
from app.models.alert import AlertModel
from app.services.route_service import RouteService
from app.services.alert_service import AlertService
from app.core.tracking import get_active_trains_locations, check_route_deviation, check_schedule_adherence
from app.core.collision import check_all_train_collisions, check_collision_risk
from app.core.location import detect_route_deviations
from app.config import get_current_utc_time, SYSTEM_SENDER_ID, GUEST_RECIPIENT_ID
from app.utils import format_timestamp_ist, handle_exceptions
from app.database import get_collection
from app.tasks.monitor import generate_system_status_report

logger = logging.getLogger("app.api.analytics")
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
    last_hour = get_current_utc_time() - timedelta(hours=hours)
    
    # Get recent logs
    recent_logs = await LogOperations.get_logs_since(last_hour)
    
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
    current_time = get_current_utc_time()
    total_alerts = await get_collection(AlertModel.collection).count_documents(
        {"timestamp": {"$gte": current_time - timedelta(hours=hours)}}
    )
   
    # Create a proper response dict
    response = {
        "timestamp": format_timestamp_ist(get_current_utc_time()),
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
        "timestamp": format_timestamp_ist(get_current_utc_time()),
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
        "timestamp": format_timestamp_ist(get_current_utc_time()),
        "train_id": train_id,
        "result": deviation
    }

@router.post("/simulate/alert")
@handle_exceptions("simulating alert")
async def simulate_alert(data: dict = Body(...)):
    """Simulate a system alert"""
    recipient_id = data.get("recipient_id")
    
    # Check if recipient exists
    if recipient_id and recipient_id != GUEST_RECIPIENT_ID:
        train = await TrainModel.get_by_train_id(recipient_id)
        if not train:
            raise HTTPException(status_code=404, detail=f"Train with ID {recipient_id} not found")
        recipient_ref = str(train["_id"])
    else:
        recipient_ref = GUEST_RECIPIENT_ID
    
    # Create alert data
    alert_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": recipient_ref,
        "message": data.get("message", "Simulated system alert"),
        "location": data.get("location", [76.850, 28.700]),
        "timestamp": get_current_utc_time()
    }
    
    alert_id = await AlertModel.create(alert_data)
    
    return {
        "success": True,
        "alert_id": alert_id,
        "message": "Alert simulated successfully",
        "timestamp": format_timestamp_ist(get_current_utc_time())
    }

