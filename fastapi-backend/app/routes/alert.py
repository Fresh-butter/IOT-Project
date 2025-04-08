"""
Alert routes module.
Defines API endpoints for alert operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from bson import ObjectId

from app.models.alert import AlertModel
from app.schemas.alert import AlertCreate, AlertUpdate, AlertInDB

router = APIRouter()

@router.get("/", response_model=List[AlertInDB])
async def get_alerts():
    """Get all alerts"""
    alerts = await AlertModel.get_all()
    return alerts

@router.get("/{id}", response_model=AlertInDB)
async def get_alert(id: str):
    """Get an alert by ID"""
    alert = await AlertModel.get_by_id(id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.get("/recipient/{recipient_id}", response_model=List[AlertInDB])
async def get_alerts_by_recipient(recipient_id: str):
    """Get alerts by recipient ID"""
    alerts = await AlertModel.get_by_recipient(recipient_id)
    return alerts

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_alert(alert: AlertCreate = Body(...)):
    """Create a new alert"""
    alert_id = await AlertModel.create(alert.dict())
    return {"id": alert_id, "message": "Alert created successfully"}

@router.put("/{id}", response_model=dict)
async def update_alert(id: str, alert: AlertUpdate = Body(...)):
    """Update an alert"""
    # Filter out None values
    alert_data = {k: v for k, v in alert.dict().items() if v is not None}
    
    if not alert_data:
        raise HTTPException(status_code=400, detail="No valid update data provided")
    
    updated = await AlertModel.update(id, alert_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert updated successfully"}

@router.delete("/{id}", response_model=dict)
async def delete_alert(id: str):
    """Delete an alert"""
    deleted = await AlertModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}
