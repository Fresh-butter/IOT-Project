"""
Train routes module.
Defines API endpoints for train operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from app.models.train import TrainModel
from app.models.route import RouteModel
from app.schemas.train import TrainCreate, TrainUpdate, TrainInDB
from app.utils import handle_exceptions
from app.config import TRAIN_STATUS
from app.database import safe_db_operation

router = APIRouter()

@router.post("/", 
             response_model=TrainInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new train",
             description="Create a new train with the provided information")
@handle_exceptions("creating train")
async def create_train(train: TrainCreate = Body(...)):
    """Create a new train"""
    train_id = await TrainModel.create(train.dict())
    created_train = await TrainModel.get_by_id(train_id)
    if not created_train:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to retrieve created train")
    return TrainInDB(**created_train)

@router.get("/", 
           response_model=List[TrainInDB],
           summary="Get all trains",
           description="Retrieve a list of all trains")
@handle_exceptions("retrieving trains")
async def get_trains(status: Optional[str] = Query(None, description="Filter trains by status")):
    """Get all trains with optional status filter"""
    trains = await TrainModel.get_all(status=status)
    return [TrainInDB(**train) for train in trains]

@router.get("/{id}", 
           response_model=TrainInDB,
           summary="Get a train by ID",
           description="Retrieve a train by its ID")
@handle_exceptions("retrieving train")
async def get_train(id: str = Path(..., description="The ID of the train to retrieve")):
    """Get a train by ID"""
    train = await TrainModel.get_by_id(id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
    return TrainInDB(**train)

@router.put("/{id}", 
            response_model=TrainInDB,
            summary="Update an existing train",
            description="Update the details of an existing train by its ID")
@handle_exceptions("updating train")
async def update_train(
    id: str = Path(..., description="The ID of the train to update"),
    train: TrainUpdate = Body(...)
):
    """Update an existing train"""
    # Convert Pydantic model to dict and keep null values
    update_data = {k: v for k, v in train.__dict__.items() 
                  if k != "__fields_set__" and k in train.__fields__}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
    
    updated = await TrainModel.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
    
    updated_train = await TrainModel.get_by_id(id)
    return TrainInDB(**updated_train)

@router.put("/{id}/status", 
            response_model=Dict[str, Any],
            summary="Update train status",
            description="Update the operational status of a train")
@handle_exceptions("updating train status")
async def update_train_status(
    id: str = Path(..., description="The ID of the train to update"),
    status: str = Body(..., description="New status (in_service_running, in_service_not_running, maintenance, out_of_service)")
):
    """Update train operational status"""
    # Validate status
    if status not in TRAIN_STATUS.values():
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    train = await TrainModel.get_by_id(id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {id} not found")
    
    # Update status
    await TrainModel.update_status(id, status)
    
    # Create status change alert
    old_status = train.get("current_status", "unknown")
    message = f"STATUS_CHANGED: Train {train['train_id']} status changed from {old_status} to {status}"
    
    # Alert for the train
    train_alert_data = {
        "sender_ref": SYSTEM_SENDER_ID,
        "recipient_ref": str(train["_id"]),
        "message": message,
        "timestamp": get_current_ist_time()
    }
    await AlertModel.create(train_alert_data, create_guest_copy=False)
    
    return {
        "id": id,
        "train_id": train["train_id"],
        "previous_status": old_status,
        "new_status": status,
        "timestamp": get_current_ist_time()
    }

@router.delete("/{id}", 
              response_model=Dict[str, str],
              summary="Delete a train",
              description="Delete a train by its ID")
@handle_exceptions("deleting train")
async def delete_train(id: str = Path(..., description="The ID of the train to delete")):
    """Delete a train by ID"""
    deleted = await TrainModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
    
    return {"message": "Train deleted successfully"}
