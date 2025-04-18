"""
Alert routes module.
Defines API endpoints for alert management.
"""
from typing import List
from fastapi import APIRouter, Body, Path, Query, status

from ..models.alert import AlertModel
from ..schemas.alert import AlertCreate, AlertUpdate, AlertInDB, AlertSummary
from app.utils import handle_exceptions
from ..services.alert_service import AlertService
from ..config import SYSTEM_SENDER_ID

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/", 
           response_model=List[AlertInDB],
           summary="Get all alerts",
           description="Retrieve a list of all alerts in the system")
@handle_exceptions("retrieving alerts")
async def get_all_alerts(
    limit: int = Query(100, ge=1, description="Limit the number of results"),
    skip: int = Query(0, ge=0, description="Skip the first N results")
):
    """Get all alerts"""
    alerts = await AlertModel.get_all(limit=limit, skip=skip)
    return alerts

@router.get("/{alert_id}", 
           response_model=AlertInDB,
           summary="Get alert by ID",
           description="Retrieve a specific alert by its ID")
@handle_exceptions("retrieving alert")
async def get_alert(
    alert_id: str = Path(..., description="The ID of the alert to retrieve")
):
    """Get alert by ID"""
    alert = await AlertModel.get_by_id(alert_id)
    return alert

@router.get("/recipient/{recipient_ref}", 
           response_model=List[AlertInDB],
           summary="Get alerts by recipient",
           description="Retrieve all alerts for a specific recipient")
@handle_exceptions("retrieving alerts by recipient")
async def get_alerts_by_recipient(
    recipient_ref: str = Path(..., description="The reference ID of the recipient")
):
    """Get alerts by recipient reference"""
    alerts = await AlertModel.get_by_recipient(recipient_ref)
    return alerts

@router.get("/sender/{sender_ref}", 
           response_model=List[AlertInDB],
           summary="Get alerts by sender",
           description="Retrieve all alerts from a specific sender")
@handle_exceptions("retrieving alerts by sender")
async def get_alerts_by_sender(
    sender_ref: str = Path(..., description="The reference ID of the sender"),
    limit: int = Query(100, ge=1, description="Limit the number of results")
):
    """Get alerts by sender reference"""
    alerts = await AlertModel.get_by_sender(sender_ref, limit=limit)
    return alerts

@router.post("/", 
            response_model=AlertInDB,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new alert",
            description="Create a new alert with the provided information")
@handle_exceptions("creating alert")
async def create_alert(
    alert: AlertCreate = Body(...)
):
    """Create a new alert"""
    alert_data = alert.dict()
    
    # Ensure system-generated alerts use the correct sender_ref
    if alert_data.get("sender_ref") == "SYSTEM":
        alert_data["sender_ref"] = SYSTEM_SENDER_ID
        
    # Set create_guest_copy=False for API-created alerts
    alert_id = await AlertModel.create(alert_data, create_guest_copy=False)
    created_alert = await AlertModel.get_by_id(alert_id)
    return created_alert

@router.put("/{alert_id}", 
           response_model=AlertInDB,
           summary="Update an alert",
           description="Update an existing alert with the provided information")
@handle_exceptions("updating alert")
async def update_alert(
    alert_id: str = Path(..., description="The ID of the alert to update"),
    alert_update: AlertUpdate = Body(...)
):
    """Update an alert"""
    update_data = alert_update.dict(exclude_unset=True)
    updated_alert = await AlertModel.update(alert_id, update_data)
    return updated_alert

@router.delete("/{alert_id}", 
              status_code=status.HTTP_204_NO_CONTENT,
              summary="Delete an alert",
              description="Delete an alert by its ID")
@handle_exceptions("deleting alert")
async def delete_alert(
    alert_id: str = Path(..., description="The ID of the alert to delete")
):
    """Delete an alert"""
    await AlertModel.delete(alert_id)
    return None
#I don't need this request
# @router.get("/summary/recent", 
#            response_model=AlertSummary,
#            summary="Get alert summary",
#            description="Get summary statistics for recent alerts")
# @handle_exceptions("generating alert summary")
# async def get_alert_summary(
#     hours: int = Query(24, ge=1, le=168, description="Number of hours to look back")
# ):
#     """Get summary of recent alerts"""
#     summary = await AlertService.generate_alert_summary(hours)
#     return summary
