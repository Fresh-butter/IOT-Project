"""
Alert routes module.
Defines API endpoints for alert operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from app.models.alert import AlertModel
from app.schemas.alert import AlertCreate, AlertUpdate, AlertInDB
from app.config import get_current_ist_time, SYSTEM_SENDER_ID
from app.utils import handle_exceptions

router = APIRouter()

@router.get("/", 
           response_model=List[AlertInDB],
           summary="Get all alerts",
           description="Retrieve a list of all alerts in the system with pagination")
@handle_exceptions("fetching alerts")
async def get_alerts(
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Limit the number of results returned"),
    skip: Optional[int] = Query(0, ge=0, description="Number of results to skip")
):
    """Get all alerts with pagination"""
    alerts = await AlertModel.get_all(limit=limit, skip=skip)
    return [AlertInDB(**alert) for alert in alerts]

@router.get("/{id}", 
           response_model=AlertInDB,
           summary="Get alert by ID",
           description="Retrieve a specific alert by its unique identifier")
@handle_exceptions("fetching alert")
async def get_alert(
    id: str = Path(..., description="The ID of the alert to retrieve")
):
    """Get an alert by ID"""
    alert = await AlertModel.get_by_id(id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Alert not found")
    return AlertInDB(**alert)

@router.get("/recipient/{recipient_id}", 
           response_model=List[AlertInDB],
           summary="Get alerts by recipient",
           description="Retrieve all alerts for a specific recipient train")
@handle_exceptions("fetching alerts by recipient")
async def get_alerts_by_recipient(
    recipient_id: str = Path(..., description="The ID of the train that receives the alerts")
):
    """Get alerts by recipient ID"""
    alerts = await AlertModel.get_by_recipient(recipient_id)
    return [AlertInDB(**alert) for alert in alerts]

@router.get("/sender/{sender_id}", 
           response_model=List[AlertInDB],
           summary="Get alerts by sender",
           description="Retrieve alerts sent by a specific train or the system")
@handle_exceptions("fetching alerts by sender")
async def get_alerts_by_sender(
    sender_id: str = Path(..., description="The ID of the train or system that sent the alerts"),
    limit: Optional[int] = Query(100, ge=1, le=500, description="Maximum number of alerts to return")
):
    """Get alerts by sender ID"""
    alerts = await AlertModel.get_by_sender(sender_id, limit)
    return [AlertInDB(**alert) for alert in alerts]

@router.get("/recent/{hours}", 
           response_model=List[AlertInDB],
           summary="Get recent alerts",
           description="Retrieve alerts from the last N hours")
@handle_exceptions("fetching recent alerts")
async def get_recent_alerts(
    hours: int = Path(..., ge=1, le=72, description="Number of hours to look back")
):
    """Get alerts from the last N hours"""
    alerts = await AlertModel.get_recent_alerts(hours)
    return [AlertInDB(**alert) for alert in alerts]

@router.post("/", 
            response_model=AlertInDB, 
            status_code=status.HTTP_201_CREATED,
            summary="Create a new alert",
            description="Create a new alert to be sent between trains")
@handle_exceptions("creating alert")
async def create_alert(
    alert: AlertCreate = Body(..., description="The alert data to create")
):
    """Create a new alert"""
    alert_dict = alert.dict()
    # Set current time if not provided
    if "timestamp" not in alert_dict or alert_dict["timestamp"] is None:
        alert_dict["timestamp"] = get_current_ist_time()
        
    # If sender_ref is not provided, use system sender ID
    if "sender_ref" not in alert_dict or alert_dict["sender_ref"] is None:
        alert_dict["sender_ref"] = SYSTEM_SENDER_ID
        
    alert_id = await AlertModel.create(alert_dict)
    created_alert = await AlertModel.get_by_id(alert_id)
    if not created_alert:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to retrieve created alert")
    return AlertInDB(**created_alert)

@router.put("/{id}", 
           response_model=AlertInDB,
           summary="Update an alert",
           description="Update the properties of an existing alert")
@handle_exceptions("updating alert")
async def update_alert(
    id: str = Path(..., description="The ID of the alert to update"),
    alert: AlertUpdate = Body(..., description="The updated alert data")
):
    """Update an alert"""
    # Filter out None values
    alert_data = {k: v for k, v in alert.dict().items() if v is not None}
    
    if not alert_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
    
    updated = await AlertModel.update(id, alert_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Alert not found")
    
    updated_alert = await AlertModel.get_by_id(id)
    return AlertInDB(**updated_alert)

@router.delete("/{id}", 
              response_model=Dict[str, str],
              summary="Delete an alert",
              description="Remove an alert from the system")
@handle_exceptions("deleting alert")
async def delete_alert(
    id: str = Path(..., description="The ID of the alert to delete")
):
    """Delete an alert"""
    deleted = await AlertModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}
