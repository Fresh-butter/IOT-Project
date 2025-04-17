"""
Alert routes module.
Defines API endpoints for alert operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.models.alert import AlertModel
from app.schemas.alert import AlertCreate, AlertUpdate, AlertInDB
from app.config import get_current_ist_time

router = APIRouter()

@router.get("/", 
           response_model=List[AlertInDB],
           summary="Get all alerts",
           description="Retrieve a list of all alerts in the system")
async def get_alerts(
    limit: Optional[int] = Query(100, description="Limit the number of results returned")
):
    """Get all alerts with optional limit"""
    alerts = await AlertModel.get_all()
    return alerts[:limit]

@router.get("/{id}", 
           response_model=AlertInDB,
           summary="Get alert by ID",
           description="Retrieve a specific alert by its unique identifier")
async def get_alert(
    id: str = Path(..., description="The ID of the alert to retrieve")
):
    """Get an alert by ID"""
    alert = await AlertModel.get_by_id(id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.get("/recipient/{recipient_id}", 
           response_model=List[AlertInDB],
           summary="Get alerts by recipient",
           description="Retrieve all alerts for a specific recipient train")
async def get_alerts_by_recipient(
    recipient_id: str = Path(..., description="The ID of the train that receives the alerts")
):
    """Get alerts by recipient ID"""
    alerts = await AlertModel.get_by_recipient(recipient_id)
    return alerts

@router.post("/", 
            response_model=AlertInDB, 
            status_code=status.HTTP_201_CREATED,
            summary="Create a new alert",
            description="Create a new alert to be sent between trains")
async def create_alert(
    alert: AlertCreate = Body(..., description="The alert data to create")
):
    """Create a new alert"""
    try:
        alert_dict = alert.dict()
        # Set current time if not provided
        if "timestamp" not in alert_dict or alert_dict["timestamp"] is None:
            alert_dict["timestamp"] = get_current_ist_time()
            
        alert_id = await AlertModel.create(alert_dict)
        created_alert = await AlertModel.get_by_id(alert_id)
        if not created_alert:
            raise HTTPException(status_code=500, detail="Failed to retrieve created alert")
        return AlertInDB(**created_alert)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating alert: {str(e)}")

@router.put("/{id}", 
           response_model=AlertInDB,
           summary="Update an alert",
           description="Update the properties of an existing alert")
async def update_alert(
    id: str = Path(..., description="The ID of the alert to update"),
    alert: AlertUpdate = Body(..., description="The updated alert data")
):
    """Update an alert"""
    try:
        # Filter out None values
        alert_data = {k: v for k, v in alert.dict().items() if v is not None}
        
        if not alert_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")
        
        updated = await AlertModel.update(id, alert_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        updated_alert = await AlertModel.get_by_id(id)
        return AlertInDB(**updated_alert)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating alert: {str(e)}")

@router.delete("/{id}", 
              response_model=dict,
              summary="Delete an alert",
              description="Remove an alert from the system")
async def delete_alert(
    id: str = Path(..., description="The ID of the alert to delete")
):
    """Delete an alert"""
    deleted = await AlertModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}
