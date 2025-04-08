"""
Log model module.
Defines the structure and operations for log data in MongoDB.
"""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import get_collection

class LogModel:
    collection = "logs"
    
    @staticmethod
    async def get_all():
        """Get all logs"""
        logs = await get_collection(LogModel.collection).find().to_list(1000)
        return logs
    
    @staticmethod
    async def get_by_id(id: str):
        """Get log by ID"""
        return await get_collection(LogModel.collection).find_one({"_id": ObjectId(id)})
    
    @staticmethod
    async def get_by_train_id(train_id: str):
        """Get logs by train ID"""
        logs = await get_collection(LogModel.collection).find(
            {"train_id": train_id}
        ).to_list(1000)
        return logs
    
    @staticmethod
    async def create(log_data: dict):
        """Create a new log"""
        # Ensure timestamp is set if not provided
        if "timestamp" not in log_data:
            log_data["timestamp"] = datetime.utcnow()
            
        # Convert string IDs to ObjectIds if needed
        if "train_ref" in log_data and isinstance(log_data["train_ref"], str):
            log_data["train_ref"] = ObjectId(log_data["train_ref"])
            
        result = await get_collection(LogModel.collection).insert_one(log_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def update(id: str, log_data: dict):
        """Update a log"""
        # Convert string IDs to ObjectIds if needed
        if "train_ref" in log_data and isinstance(log_data["train_ref"], str):
            log_data["train_ref"] = ObjectId(log_data["train_ref"])
            
        result = await get_collection(LogModel.collection).update_one(
            {"_id": ObjectId(id)}, {"$set": log_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(id: str):
        """Delete a log"""
        result = await get_collection(LogModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
