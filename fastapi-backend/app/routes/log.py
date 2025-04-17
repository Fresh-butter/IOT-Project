"""
Log routes module.
Defines API endpoints for log operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query
from typing import List, Optional, Dict
from app.models.log import LogModel
from app.schemas.log import LogCreate, LogUpdate, LogInDB
from app.config import get_current_ist_time

router = APIRouter()

@router.post("/", 
             response_model=LogInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new log entry",
             description="Create a new log entry for a train")
async def create_log(log: LogCreate = Body(...)):
    """Create a new log entry"""
    try:
        log_dict = log.dict()
        # Set current time if not provided
        if "timestamp" not in log_dict or log_dict["timestamp"] is None:
            log_dict["timestamp"] = get_current_ist_time()
            
        log_id = await LogModel.create(log_dict)
        created_log = await LogModel.get_by_id(log_id)
        if not created_log:
            raise HTTPException(status_code=500, detail="Failed to retrieve created log")
        return LogInDB(**created_log)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating log: {str(e)}")

@router.put("/{id}", 
            response_model=LogInDB,
            summary="Update a log entry",
            description="Update the details of an existing log entry")
async def update_log(
    id: str = Path(..., description="The ID of the log to update"),
    log: LogUpdate = Body(...)
):
    """Update an existing log entry"""
    try:
        update_data = {k: v for k, v in log.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")
            
        updated = await LogModel.update(id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Log not found")
            
        updated_log = await LogModel.get_by_id(id)
        return LogInDB(**updated_log)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating log: {str(e)}")

@router.get("/", 
            response_model=List[LogInDB],
            summary="Get all logs",
            description="Retrieve a list of all log entries with options for filtering")
async def get_logs(
    limit: Optional[int] = Query(100, description="Limit the number of results returned"),
    is_test: Optional[bool] = Query(None, description="Filter logs by test status")
):
    """Fetch all logs with optional limit and test status filter"""
    try:
        logs = await LogModel.get_all(limit=limit, is_test=is_test)
        return [LogInDB(**log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.get("/{id}", 
            response_model=LogInDB,
            summary="Get log by ID",
            description="Retrieve a specific log entry by its ID")
async def get_log(
    id: str = Path(..., description="The ID of the log to retrieve")
):
    """Fetch a log by ID"""
    try:
        log = await LogModel.get_by_id(id)
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        return LogInDB(**log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching log: {str(e)}")

@router.get("/train/{train_id}", 
            response_model=List[LogInDB],
            summary="Get logs by train ID",
            description="Retrieve logs for a specific train")
async def get_logs_by_train(
    train_id: str = Path(..., description="The ID of the train to find logs for"),
    limit: Optional[int] = Query(100, description="Limit the number of results returned")
):
    """Fetch logs by train ID"""
    try:
        logs = await LogModel.get_by_train_id(train_id, limit)
        return [LogInDB(**log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.get("/train/{train_id}/latest", 
            response_model=LogInDB,
            summary="Get latest log for a train",
            description="Retrieve the most recent log entry for a specific train")
async def get_latest_log_for_train(
    train_id: str = Path(..., description="The ID of the train to find the latest log for")
):
    """Fetch the latest log for a train"""
    try:
        log = await LogModel.get_latest_by_train(train_id)
        if not log:
            raise HTTPException(status_code=404, detail=f"No logs found for train {train_id}")
        return LogInDB(**log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching log: {str(e)}")

@router.delete("/{id}", 
              response_model=dict,
              summary="Delete a log",
              description="Delete a log entry by its ID")
async def delete_log(
    id: str = Path(..., description="The ID of the log to delete")
):
    """Delete a log by ID"""
    try:
        deleted = await LogModel.delete(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Log not found")
        
        return {"message": "Log deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting log: {str(e)}")

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
        "invalid": "No GPS fix or very high error (HDOP > 10.0, satellites < 3)"
    }
