"""
Log routes module.
Defines API endpoints for log operations.
"""
from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from app.models.log import LogModel
from app.schemas.log import LogCreate, LogUpdate, LogInDB

router = APIRouter()

@router.post("/", response_model=LogInDB, status_code=status.HTTP_201_CREATED)
async def create_log(log: LogCreate = Body(...)):
    try:
        log_id = await LogModel.create(log.dict())
        created_log = await LogModel.get_by_id(log_id)
        return LogInDB(**created_log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.put("/{id}", response_model=LogInDB)
async def update_log(id: str, log: LogUpdate = Body(...)):
    try:
        update_data = {k: v for k, v in log.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
            
        updated = await LogModel.update(id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Log not found")
            
        updated_log = await LogModel.get_by_id(id)
        return LogInDB(**updated_log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/", response_model=List[LogInDB])
async def get_logs():
    try:
        logs = await LogModel.get_all()
        return [LogInDB(**log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/{id}", response_model=LogInDB)
async def get_log(id: str):
    log = await LogModel.get_by_id(id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return LogInDB(**log)

@router.delete("/{id}", response_model=dict)
async def delete_log(id: str):
    deleted = await LogModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return {"message": "Log deleted successfully"}
