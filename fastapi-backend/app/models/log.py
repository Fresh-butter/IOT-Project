"""
Log model module.
Defines the structure and operations for log data in MongoDB.
"""
from bson import ObjectId
from datetime import datetime, timedelta
from app.database import get_collection
from app.config import get_current_ist_time
from app.utils import round_coordinates
from typing import List, Optional, Dict, Any

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
        if "train_ref" in log_data and isinstance(log_data["train_ref"], str):
            log_data["train_ref"] = ObjectId(log_data["train_ref"])
        
        # Round coordinates if location is present
        if "location" in log_data and log_data["location"]:
            log_data["location"] = round_coordinates(log_data["location"])
            
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
        if "train_ref" in update_data and isinstance(update_data["train_ref"], str):
            update_data["train_ref"] = ObjectId(update_data["train_ref"])
        
        # Round coordinates if location is present
        if "location" in update_data and update_data["location"]:
            update_data["location"] = round_coordinates(update_data["location"])
        
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
    async def get_all(limit: int = 1000, skip: int = 0, is_test: Optional[bool] = None):
        """
        Fetch all logs with optional filtering and pagination
        
        Args:
            limit: Maximum number of logs to fetch
            skip: Number of logs to skip
            is_test: Optional filter for test logs
            
        Returns:
            list: List of log documents
        """
        filter_query = {}
        if is_test is not None:
            filter_query["is_test"] = is_test
            
        results = await get_collection(LogModel.collection).find(filter_query).sort(
            "timestamp", -1
        ).skip(skip).limit(limit).to_list(limit)
        return results
        
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

    @staticmethod
    async def get_logs_by_rfid(rfid_tag: str, limit: int = 100):
        """
        Get logs that contain a specific RFID tag
        
        Args:
            rfid_tag: RFID tag identifier
            limit: Maximum number of logs to return
            
        Returns:
            list: List of log documents containing the specified RFID tag
        """
        logs = await get_collection(LogModel.collection).find(
            {"rfid_tag": rfid_tag}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return logs
        
    @staticmethod
    async def get_logs_in_time_range(train_id: str, start_time: datetime, end_time: datetime):
        """
        Get logs for a train within a specific time range
        
        Args:
            train_id: Train identifier
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            list: List of log documents within the specified time range
        """
        logs = await get_collection(LogModel.collection).find({
            "train_id": train_id,
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }).sort("timestamp", 1).to_list(1000)
        return logs
        
    @staticmethod
    async def get_last_n_hours_logs(train_id: str, hours: int = 6):
        """
        Get logs for a train from the last N hours
        
        Args:
            train_id: Train identifier
            hours: Number of hours to look back
            
        Returns:
            list: List of log documents from the last N hours
        """
        time_threshold = get_current_ist_time() - timedelta(hours=hours)
        logs = await get_collection(LogModel.collection).find({
            "train_id": train_id,
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", 1).to_list(1000)
        return logs

    @classmethod
    async def get_logs_since(cls, timestamp):
        """
        Get all logs since the specified timestamp
        
        Args:
            timestamp (datetime): The timestamp to query logs from
            
        Returns:
            list: List of log documents
        """
        from app.database import get_collection
        logs = await get_collection(cls.collection).find({
            "timestamp": {"$gte": timestamp}
        }).to_list(length=None)
        
        return logs

    @classmethod
    async def get_logs_by_train_since(cls, train_id, timestamp):
        """
        Get logs for a specific train since the specified timestamp
        
        Args:
            train_id (str): The train ID to filter logs
            timestamp (datetime): The timestamp to query logs from
            
        Returns:
            list: List of log documents for the specified train
        """
        from app.database import get_collection
        logs = await get_collection(cls.collection).find({
            "train_id": train_id,
            "timestamp": {"$gte": timestamp}
        }).sort("timestamp", 1).to_list(length=None)
        
        return logs

    @classmethod
    async def count_logs_since(cls, timestamp):
        """
        Count logs since the specified timestamp
        
        Args:
            timestamp (datetime): The timestamp to query logs from
            
        Returns:
            int: Count of logs
        """
        from app.database import get_collection
        count = await get_collection(cls.collection).count_documents({
            "timestamp": {"$gte": timestamp}
        })
        
        return count

    @classmethod
    async def get_latest_log_for_each_train(cls):
        """
        Get the latest log entry for each train
        
        Returns:
            list: Latest log document for each train
        """
        from app.database import get_collection
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$train_id",
                "latest_log": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_log"}}
        ]
        
        logs = await get_collection(cls.collection).aggregate(pipeline).to_list(length=None)
        return logs
