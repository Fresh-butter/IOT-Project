"""
Log routes module.
Defines API endpoints for log operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.log import LogModel
from app.models.train import TrainModel
from app.schemas.log import LogCreate, LogUpdate, LogInDB
from app.utils import handle_exceptions
from app.database import safe_db_operation
from app.config import get_current_ist_time

router = APIRouter()

@router.post("/", 
            response_model=LogInDB, 
            status_code=status.HTTP_201_CREATED,
            summary="Create a new log entry",
            description="Create a new log entry for a train event")
@handle_exceptions("creating log")
async def create_log(
    log: LogCreate = Body(..., description="The log data to create")
):
    """Create a new log entry"""
    # Check if the train exists
    train = await TrainModel.get_by_train_id(log.train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {log.train_id} not found")
    
    # Set train_ref if not provided
    log_dict = log.dict()
    if "train_ref" not in log_dict or log_dict["train_ref"] is None:
        log_dict["train_ref"] = str(train["_id"])
    
    # Set timestamp if not provided
    if "timestamp" not in log_dict or log_dict["timestamp"] is None:
        log_dict["timestamp"] = get_current_ist_time()
        
    log_id = await LogModel.create(log_dict)
    created_log = await LogModel.get_by_id(log_id)
    if not created_log:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to retrieve created log")
    return LogInDB(**created_log)

@router.put("/{id}", 
            response_model=LogInDB,
            summary="Update a log entry",
            description="Update the details of an existing log entry")
@handle_exceptions("updating log")
async def update_log(
    id: str = Path(..., description="The ID of the log to update"),
    log: LogUpdate = Body(...)
):
    """Update an existing log entry"""
    update_data = {k: v for k, v in log.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
        
    updated = await LogModel.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Log not found")
        
    updated_log = await LogModel.get_by_id(id)
    return LogInDB(**updated_log)

@router.get("/", 
           response_model=List[LogInDB],
           summary="Get all logs",
           description="Retrieve a list of all logs with pagination")
@handle_exceptions("retrieving logs")
async def get_logs(
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    is_test: Optional[bool] = Query(None, description="Filter by test flag")
):
    """Get all logs with pagination"""
    logs = await LogModel.get_all(limit=limit, skip=skip, is_test=is_test)
    return [LogInDB(**log) for log in logs]

@router.get("/{id}", 
           response_model=LogInDB,
           summary="Get log by ID",
           description="Retrieve a specific log by its unique identifier")
@handle_exceptions("retrieving log")
async def get_log(
    id: str = Path(..., description="The ID of the log to retrieve")
):
    """Get a log by ID"""
    log = await LogModel.get_by_id(id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Log not found")
    return LogInDB(**log)

@router.get("/train/{train_id}", 
           response_model=List[LogInDB],
           summary="Get logs by train",
           description="Retrieve logs for a specific train")
@handle_exceptions("retrieving logs by train")
async def get_logs_by_train(
    train_id: str = Path(..., description="The ID of the train"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return")
):
    """Get logs by train ID"""
    # Check if the train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {train_id} not found")
    
    logs = await LogModel.get_by_train_id(train_id, limit)
    return [LogInDB(**log) for log in logs]

@router.get("/rfid/{rfid_tag}", 
           response_model=List[LogInDB],
           summary="Get logs by RFID tag",
           description="Retrieve logs containing a specific RFID tag")
@handle_exceptions("retrieving logs by RFID")
async def get_logs_by_rfid(
    rfid_tag: str = Path(..., description="The RFID tag to search for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return")
):
    """Get logs by RFID tag"""
    logs = await LogModel.get_logs_by_rfid(rfid_tag, limit)
    return [LogInDB(**log) for log in logs]

@router.get("/time-range/{train_id}", 
           response_model=List[LogInDB],
           summary="Get logs in time range",
           description="Retrieve logs for a train within a specified time range")
@handle_exceptions("retrieving logs in time range")
async def get_logs_in_time_range(
    train_id: str = Path(..., description="The ID of the train"),
    start_time: datetime = Query(..., description="Start of time range (ISO format)"),
    end_time: datetime = Query(..., description="End of time range (ISO format)")
):
    """Get logs for a train within a time range"""
    # Check if the train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {train_id} not found")
    
    logs = await LogModel.get_logs_in_time_range(train_id, start_time, end_time)
    return [LogInDB(**log) for log in logs]

@router.get("/latest/{train_id}", 
           response_model=Optional[LogInDB],
           summary="Get latest log",
           description="Retrieve the most recent log for a specific train")
@handle_exceptions("retrieving latest log")
async def get_latest_log(
    train_id: str = Path(..., description="The ID of the train")
):
    """Get the latest log for a train"""
    # Check if the train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {train_id} not found")
    
    log = await LogModel.get_latest_by_train(train_id)
    if not log:
        return None
    return LogInDB(**log)

@router.get("/train/{train_id}/hours/{hours}", 
            response_model=List[LogInDB],
            summary="Get logs from last N hours",
            description="Retrieve logs for a train from the last N hours")
@handle_exceptions("fetching recent logs")
async def get_logs_last_n_hours(
    train_id: str = Path(..., description="The ID of the train"),
    hours: int = Path(..., ge=1, le=48, description="Number of hours to look back")
):
    """Fetch logs from the last N hours for a train"""
    logs = await LogModel.get_last_n_hours_logs(train_id, hours)
    return [LogInDB(**log) for log in logs]

@router.delete("/{id}", 
              response_model=Dict[str, str],
              summary="Delete a log",
              description="Remove a log entry from the system")
@handle_exceptions("deleting log")
async def delete_log(
    id: str = Path(..., description="The ID of the log to delete")
):
    """Delete a log by ID"""
    deleted = await LogModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Log not found")
    
    return {"message": "Log deleted successfully"}


