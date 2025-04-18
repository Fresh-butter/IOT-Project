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
    update_data = {k: v for k, v in train.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
    
    updated = await TrainModel.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
    
    updated_train = await TrainModel.get_by_id(id)
    return TrainInDB(**updated_train)

@router.get("/", 
            response_model=List[TrainInDB],
            summary="Get all trains",
            description="Retrieve a list of all registered trains with optional status filtering")
@handle_exceptions("fetching trains")
async def get_trains(
    status: Optional[str] = Query(None, description="Filter trains by status")
):
    """Fetch all trains with optional status filtering"""
    # Validate status if provided
    if status is not None and status not in TRAIN_STATUS.values():
        valid_statuses = ", ".join(TRAIN_STATUS.values())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    trains = await TrainModel.get_all(status)
    return [TrainInDB(**train) for train in trains]

@router.get("/active", 
            response_model=List[TrainInDB],
            summary="Get active trains",
            description="Retrieve a list of all trains that are currently in service and running")
@handle_exceptions("fetching active trains")
async def get_active_trains():
    """Fetch all active trains"""
    trains = await TrainModel.get_active_trains()
    return [TrainInDB(**train) for train in trains]

@router.get("/status-options", 
            response_model=Dict[str, str],
            summary="Get valid train status options",
            description="Retrieve a list of all valid train status values with descriptions")
async def get_status_options():
    """Get all valid train status options with descriptions"""
    return {
        TRAIN_STATUS["IN_SERVICE_RUNNING"]: "Train is currently running on its assigned route",
        TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]: "Route assigned but train is currently halted (station/emergency)",
        TRAIN_STATUS["MAINTENANCE"]: "Train is under maintenance",
        TRAIN_STATUS["OUT_OF_SERVICE"]: "Train is out of service with no assigned route"
    }

@router.get("/{id}", 
            response_model=TrainInDB,
            summary="Get train by ID",
            description="Retrieve a specific train by its ID")
@handle_exceptions("fetching train")
async def get_train(id: str = Path(..., description="The ID of the train to retrieve")):
    """Fetch a train by ID"""
    train = await TrainModel.get_by_id(id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
    return TrainInDB(**train)

@router.get("/by-train-id/{train_id}", 
            response_model=TrainInDB,
            summary="Get train by train_id",
            description="Retrieve a specific train by its train_id field")
@handle_exceptions("fetching train by train_id")
async def get_train_by_train_id(
    train_id: str = Path(..., description="The train_id field value to search for")
):
    """Fetch a train by train_id field"""
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
    return TrainInDB(**train)

@router.put("/{id}/status", 
           response_model=TrainInDB,
           summary="Update train status",
           description="Update the operational status of a train")
@handle_exceptions("updating train status")
async def update_train_status(
    id: str = Path(..., description="The ID of the train to update"),
    status: str = Body(..., embed=True, description="The new status")
):
    """Update a train's status"""
    # Validate status value
    if status not in TRAIN_STATUS.values():
        valid_statuses = ", ".join(TRAIN_STATUS.values())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail=f"Invalid status. Must be one of: {valid_statuses}")
        
    updated = await TrainModel.update_status(id, status)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Train not found")
        
    updated_train = await TrainModel.get_by_id(id)
    return TrainInDB(**updated_train)

@router.put("/{train_id}/assign-route/{route_id}", 
           response_model=TrainInDB,
           summary="Assign route to train",
           description="Assign a route to a train and update train's status")
@handle_exceptions("assigning route to train")
async def assign_route_to_train(
    train_id: str = Path(..., description="The ID of the train"),
    route_id: str = Path(..., description="The ID of the route to assign")
):
    """Assign a route to a train"""
    # Find the route first
    route = await RouteModel.get_by_id(route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Route with ID {route_id} not found")
    
    # Find the train
    train = await TrainModel.get_by_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {train_id} not found")
    
    # Assign the route to the train
    await TrainModel.assign_route(train_id, route["route_id"], str(route["_id"]))
    
    # Also update the route to reference this train
    await RouteModel.assign_train(route_id, train["train_id"], str(train["_id"]))
    
    # Get updated train data
    updated_train = await TrainModel.get_by_id(train_id)
    return TrainInDB(**updated_train)

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
