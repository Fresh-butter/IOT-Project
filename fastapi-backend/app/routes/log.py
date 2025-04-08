"""
Log routes module.
Defines API endpoints for log operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from bson import ObjectId

from app.models.log import LogModel
from app.schemas.log import LogCreate, LogUpdate, LogInDB

router = APIRouter()

@router.get("/", response_model=List[LogInDB])
async def get_logs():
    """Get all logs"""
    logs = await LogModel.get_all()
    return logs

@router.get("/{id}", response_model=LogInDB)
async def get_log(id: str):
    """Get a log by ID"""
    log = await LogModel.get_by_id(id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@router.get("/train/{train_id}", response_model=List[LogInDB])
async def get_logs_by_train(train_id: str):
    """Get logs by train ID"""
    logs = await LogModel.get_by_train_id(train_id)
    return logs

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_log(log: LogCreate = Body(...)):
    """Create a new log"""
    log_id = await LogModel.create(log.dict())
    return {"id": log_id, "message": "Log created successfully"}

@router.put("/{id}", response_model=dict)
async def update_log(id: str, log: LogUpdate = Body(...)):
    """Update a log"""
    # Filter out None values
    log_data = {k: v for k, v in log.dict().items() if v is not None}
    
    if not log_data:
        raise HTTPException(status_code=400, detail="No valid update data provided")
    
    updated = await LogModel.update(id, log_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {"message": "Log updated successfully"}

@router.delete("/{id}", response_model=dict)
async def delete_log(id: str):
    """Delete a log"""
    deleted = await LogModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {"message": "Log deleted successfully"}
