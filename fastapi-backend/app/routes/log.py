"""
Log routes module.
Defines API endpoints for log operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.log import LogModel
from app.schemas.log import LogCreate, LogUpdate, LogInDB
from app.config import get_current_ist_time
from app.utils import handle_exceptions

router = APIRouter()

@router.post("/", 
             response_model=LogInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new log entry",
             description="Create a new log entry for a train")
@handle_exceptions("creating log")
async def create_log(log: LogCreate = Body(...)):
    """Create a new log entry"""
    log_dict = log.dict()
    # Set current time if not provided
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
            description="Retrieve all logs with pagination and optional filtering")
@handle_exceptions("fetching logs")
async def get_logs(
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Limit the number of results returned"),
    skip: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
    is_test: Optional[bool] = Query(None, description="Filter logs by test status")
):
    """Fetch all logs with optional limit and test status filter"""
    logs = await LogModel.get_all(limit=limit, skip=skip, is_test=is_test)
    return [LogInDB(**log) for log in logs]

@router.get("/{id}", 
            response_model=LogInDB,
            summary="Get log by ID",
            description="Retrieve a specific log entry by its ID")
@handle_exceptions("fetching log")
async def get_log(
    id: str = Path(..., description="The ID of the log to retrieve")
):
    """Fetch a log by ID"""
    log = await LogModel.get_by_id(id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Log not found")
    return LogInDB(**log)

@router.get("/train/{train_id}", 
            response_model=List[LogInDB],
            summary="Get logs by train ID",
            description="Retrieve logs for a specific train")
@handle_exceptions("fetching logs for train")
async def get_logs_by_train(
    train_id: str = Path(..., description="The ID of the train to find logs for"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Limit the number of results returned")
):
    """Fetch logs by train ID"""
    logs = await LogModel.get_by_train_id(train_id, limit)
    return [LogInDB(**log) for log in logs]

@router.get("/train/{train_id}/latest", 
            response_model=LogInDB,
            summary="Get latest log for a train",
            description="Retrieve the most recent log entry for a specific train")
@handle_exceptions("fetching latest log for train")
async def get_latest_log_for_train(
    train_id: str = Path(..., description="The ID of the train to find the latest log for")
):
    """Fetch the latest log for a train"""
    log = await LogModel.get_latest_by_train(train_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"No logs found for train {train_id}")
    return LogInDB(**log)

@router.get("/rfid/{rfid_tag}", 
            response_model=List[LogInDB],
            summary="Get logs by RFID tag",
            description="Retrieve logs that contain a specific RFID tag")
@handle_exceptions("fetching logs by RFID tag")
async def get_logs_by_rfid(
    rfid_tag: str = Path(..., description="The RFID tag to search for"),
    limit: Optional[int] = Query(100, ge=1, le=500, description="Limit the number of results returned")
):
    """Fetch logs by RFID tag"""
    logs = await LogModel.get_logs_by_rfid(rfid_tag, limit)
    return [LogInDB(**log) for log in logs]

@router.get("/train/{train_id}/timerange", 
            response_model=List[LogInDB],
            summary="Get logs within time range",
            description="Retrieve logs for a train within a specific time range")
@handle_exceptions("fetching logs in time range")
async def get_logs_in_time_range(
    train_id: str = Path(..., description="The ID of the train"),
    start_time: datetime = Query(..., description="Start time (ISO format with timezone)"),
    end_time: datetime = Query(..., description="End time (ISO format with timezone)")
):
    """Fetch logs for a train within a time range"""
    logs = await LogModel.get_logs_in_time_range(train_id, start_time, end_time)
    return [LogInDB(**log) for log in logs]

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
              description="Delete a log entry by its ID")
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

@router.get("/accuracy-options", 
            response_model=Dict[str, str],
            summary="Get GPS accuracy categories",
            description="Retrieve a description of GPS accuracy categories used in the system")
async def get_accuracy_options():
    """Get GPS accuracy categories and their descriptions"""
    return {
        "excellent": "< 5 meter error (HDOP ≤ 1.0, satellites ≥ 6)",
        "good": "5-10 meter error (HDOP 1.0-2.0, satellites ≥ 5)",
        "moderate": "10-25 meter error (HDOP 2.0-5.0, satellites ≥ 4)",
        "poor": "25-50 meter error (HDOP 5.0-10.0, satellites ≥ 3)",
        "very_poor": "> 50 meter error (HDOP > 10.0, satellites < 3)",
        "invalid": "No GPS fix"
    }
