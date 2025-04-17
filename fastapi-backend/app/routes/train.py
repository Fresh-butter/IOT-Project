"""
Train routes module.
Defines API endpoints for train operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query
from typing import List, Optional
from app.models.train import TrainModel
from app.schemas.train import TrainCreate, TrainUpdate, TrainInDB
from app.utils import handle_exceptions

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
        raise HTTPException(status_code=500, detail="Failed to retrieve created train")
    return TrainInDB(**created_train)

@router.put("/{id}", 
            response_model=TrainInDB,
            summary="Update an existing train",
            description="Update the details of an existing train by its ID")
async def update_train(
    id: str = Path(..., description="The ID of the train to update"),
    train: TrainUpdate = Body(...)
):
    """Update an existing train"""
    try:
        update_data = {k: v for k, v in train.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")
        
        updated = await TrainModel.update(id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Train not found")
        
        updated_train = await TrainModel.get_by_id(id)
        if not updated_train:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated train")
        
        return TrainInDB(**updated_train)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating train: {str(e)}")

@router.get("/", 
            response_model=List[TrainInDB],
            summary="Get all trains",
            description="Retrieve a list of all registered trains with optional status filtering")
async def get_trains(
    status: Optional[str] = Query(None, description="Filter trains by status")
):
    """Fetch all trains with optional status filtering"""
    try:
        trains = await TrainModel.get_all(status)
        return [TrainInDB(**train) for train in trains]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trains: {str(e)}")

@router.get("/status-options", 
            response_model=List[str],
            summary="Get valid train status options",
            description="Retrieve a list of all valid train status values")
async def get_status_options():
    """Get all valid train status options"""
    return ["in_service_running", "in_service_not_running", "maintenance", "out_of_service"]

@router.get("/{id}", 
            response_model=TrainInDB,
            summary="Get train by ID",
            description="Retrieve a specific train by its ID")
async def get_train(id: str = Path(..., description="The ID of the train to retrieve")):
    """Fetch a train by ID"""
    try:
        train = await TrainModel.get_by_id(id)
        if not train:
            raise HTTPException(status_code=404, detail="Train not found")
        return TrainInDB(**train)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching train: {str(e)}")

@router.get("/by-train-id/{train_id}", 
            response_model=TrainInDB,
            summary="Get train by train_id",
            description="Retrieve a specific train by its train_id field")
async def get_train_by_train_id(
    train_id: str = Path(..., description="The train_id field value to search for")
):
    """Fetch a train by train_id field"""
    try:
        train = await TrainModel.get_by_train_id(train_id)
        if not train:
            raise HTTPException(status_code=404, detail="Train not found")
        return TrainInDB(**train)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching train: {str(e)}")

@router.delete("/{id}", 
              response_model=dict,
              summary="Delete a train",
              description="Delete a train by its ID")
async def delete_train(id: str = Path(..., description="The ID of the train to delete")):
    """Delete a train by ID"""
    try:
        deleted = await TrainModel.delete(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Train not found")
        
        return {"message": "Train deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting train: {str(e)}")
