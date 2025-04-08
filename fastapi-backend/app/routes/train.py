"""
Train routes module.
Defines API endpoints for train operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from bson import ObjectId

from app.models.train import TrainModel
from app.schemas.train import TrainCreate, TrainUpdate, TrainInDB

router = APIRouter()

@router.get("/", response_model=List[TrainInDB])
async def get_trains():
    """Get all trains"""
    trains = await TrainModel.get_all()
    return trains

@router.get("/{id}", response_model=TrainInDB)
async def get_train(id: str):
    """Get a train by ID"""
    train = await TrainModel.get_by_id(id)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return train

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_train(train: TrainCreate = Body(...)):
    """Create a new train"""
    train_id = await TrainModel.create(train.dict())
    return {"id": train_id, "message": "Train created successfully"}

@router.put("/{id}", response_model=dict)
async def update_train(id: str, train: TrainUpdate = Body(...)):
    """Update a train"""
    # Filter out None values
    train_data = {k: v for k, v in train.dict().items() if v is not None}
    
    if not train_data:
        raise HTTPException(status_code=400, detail="No valid update data provided")
    
    updated = await TrainModel.update(id, train_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Train not found")
    
    return {"message": "Train updated successfully"}

@router.delete("/{id}", response_model=dict)
async def delete_train(id: str):
    """Delete a train"""
    deleted = await TrainModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Train not found")
    
    return {"message": "Train deleted successfully"}
