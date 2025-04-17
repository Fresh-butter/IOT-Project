"""
Log model module.
Defines the structure and operations for log data in MongoDB.
"""
from bson import ObjectId
from datetime import datetime
from app.database import get_collection
from app.config import get_current_ist_time

class LogModel:
    collection = "logs"

    @staticmethod
    async def create(log_data: dict):
        """
        Create a new log entry in the database
        
        Args:
            log_data: Dictionary containing log details
            
        Returns:
            str: ID of the newly created log document
        """
        # Ensure we have a timestamp in IST
        if "timestamp" not in log_data or log_data["timestamp"] is None:
            log_data["timestamp"] = get_current_ist_time()
            
        # Convert train_ref string to ObjectId for MongoDB storage
        if "train_ref" in log_data and log_data["train_ref"]:
            log_data["train_ref"] = ObjectId(log_data["train_ref"])
            
        result = await get_collection(LogModel.collection).insert_one(log_data)
        return str(result.inserted_id)

    @staticmethod
    async def update(id: str, update_data: dict):
        """
        Update an existing log entry
        
        Args:
            id: Log document ID
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Handle ObjectId conversion for updates
        if "train_ref" in update_data and update_data["train_ref"]:
            update_data["train_ref"] = ObjectId(update_data["train_ref"])
        
        result = await get_collection(LogModel.collection).update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_by_id(id: str):
        """
        Fetch a log by MongoDB ID
        
        Args:
            id: Log document ID
            
        Returns:
            dict: Log document or None if not found
        """
        return await get_collection(LogModel.collection).find_one({"_id": ObjectId(id)})

    @staticmethod
    async def get_by_train_id(train_id: str, limit: int = 100):
        """
        Fetch logs for a specific train
        
        Args:
            train_id: Train identifier
            limit: Maximum number of logs to return
            
        Returns:
            list: List of log documents
        """
        logs = await get_collection(LogModel.collection).find(
            {"train_id": train_id}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return logs
        
    @staticmethod
    async def delete(id: str):
        """
        Delete a log by ID
        
        Args:
            id: Log document ID
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        result = await get_collection(LogModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_all(limit: int = 1000, is_test: bool = None):
        """
        Fetch all logs with optional filtering by test status
        
        Args:
            limit: Maximum number of logs to return
            is_test: Filter by test status if provided
            
        Returns:
            list: List of log documents
        """
        filter_query = {}
        if is_test is not None:
            filter_query["is_test"] = is_test
            
        logs = await get_collection(LogModel.collection).find(filter_query).sort(
            "timestamp", -1
        ).limit(limit).to_list(limit)
        return logs
        
    @staticmethod
    async def get_latest_by_train(train_id: str):
        """
        Get the most recent log entry for a specific train
        
        Args:
            train_id: Train identifier
            
        Returns:
            dict: Most recent log document or None if not found
        """
        logs = await get_collection(LogModel.collection).find(
            {"train_id": train_id}
        ).sort("timestamp", -1).limit(1).to_list(1)
        
        return logs[0] if logs else None
