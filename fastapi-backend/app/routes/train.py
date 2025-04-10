from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from app.models.train import TrainModel
from app.schemas.train import TrainCreate, TrainUpdate, TrainInDB

router = APIRouter()

@router.post("/", response_model=TrainInDB, status_code=status.HTTP_201_CREATED)
async def create_train(train: TrainCreate = Body(...)):
    """Create a new train"""
    try:
        train_id = await TrainModel.create(train.dict())
        created_train = await TrainModel.get_by_id(train_id)
        if not created_train:
            raise HTTPException(status_code=500, detail="Failed to retrieve created train")
        return TrainInDB(**created_train)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating train: {str(e)}")

@router.put("/{id}", response_model=TrainInDB)
async def update_train(id: str, train: TrainUpdate = Body(...)):
    """Update an existing train"""
    try:
        update_data = {k: v for k, v in train.dict().items() if v is not None}
        
        updated = await TrainModel.update(id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Train not found")
        
        updated_train = await TrainModel.get_by_id(id)
        if not updated_train:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated train")
        
        return TrainInDB(**updated_train)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating train: {str(e)}")

@router.get("/", response_model=List[TrainInDB])
async def get_trains():
    """Fetch all trains"""
    try:
        trains = await TrainModel.get_all()
        return [TrainInDB(**train) for train in trains]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trains: {str(e)}")

@router.get("/{id}", response_model=TrainInDB)
async def get_train(id: str):
    """Fetch a train by ID"""
    try:
        train = await TrainModel.get_by_id(id)
        if not train:
            raise HTTPException(status_code=404, detail="Train not found")
        return TrainInDB(**train)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching train: {str(e)}")

@router.delete("/{id}", response_model=dict)
async def delete_train(id: str):
    """Delete a train by ID"""
    try:
        deleted = await TrainModel.delete(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Train not found")
        
        return {"message": "Train deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting train: {str(e)}")
