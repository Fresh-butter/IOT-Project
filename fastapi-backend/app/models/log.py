"""
Log model module.
Defines the structure and operations for log data in MongoDB.
"""
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from app.database import get_collection, safe_db_operation
from app.config import get_current_utc_time, convert_to_ist
from app.utils import round_coordinates, normalize_timestamp
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, root_validator

class LogModel(BaseModel):
    train_id: str
    train_ref: str  
    timestamp: str
    rfid_tag: Optional[str] = None
    location: Optional[Any] = None  # Changed from List[float] to Any to accept null
    accuracy: str  # Changed from enum to str to accept any accuracy value
    is_test: bool = False
    
    @root_validator(pre=True)
    def validate_location(cls, values):
        """
        Custom validator to handle location field
        - If location is null/None, keep it as None
        - If location is a list with longitude and latitude, keep it as is
        """
        if 'location' in values and values['location'] is None:
            # Allow null for location
            pass
        elif 'location' in values and isinstance(values['location'], list) and len(values['location']) == 2:
            # Make sure both longitude and latitude are floats
            values['location'] = [float(values['location'][0]), float(values['location'][1])]
        
        return values

    class Config:
        # Allow arbitrary types for validation
        arbitrary_types_allowed = True
        # This makes Pydantic use the field names as-is (case-sensitive)
        populate_by_name = True

class LogOperations:
    collection = "logs"

    @classmethod
    async def create(cls, log_data: dict) -> str:
        """Create a new log entry with proper timezone handling"""
        async def operation():
            # Make a copy to avoid modifying the original
            log_data_copy = log_data.copy()
            
            # Timestamp handling - normalize all timestamps to UTC
            if "timestamp" not in log_data_copy or log_data_copy["timestamp"] is None:
                log_data_copy["timestamp"] = get_current_utc_time()
            else:
                # If string, parse it and normalize to UTC
                if isinstance(log_data_copy["timestamp"], str):
                    try:
                        # Parse with timezone awareness
                        dt = datetime.fromisoformat(log_data_copy["timestamp"].replace('Z', '+00:00'))
                        # Normalize to UTC
                        log_data_copy["timestamp"] = normalize_timestamp(dt)
                    except ValueError:
                        # If parsing fails, use current UTC time
                        log_data_copy["timestamp"] = get_current_utc_time()
                else:
                    # If already a datetime, ensure it's UTC
                    log_data_copy["timestamp"] = normalize_timestamp(log_data_copy["timestamp"])
            
            # Convert train_ref string to ObjectId for MongoDB storage
            if "train_ref" in log_data_copy and isinstance(log_data_copy["train_ref"], str):
                log_data_copy["train_ref"] = ObjectId(log_data_copy["train_ref"])
            
            # Round coordinates if location is present
            if "location" in log_data_copy and log_data_copy["location"]:
                log_data_copy["location"] = round_coordinates(log_data_copy["location"])
                
            result = await get_collection(LogOperations.collection).insert_one(log_data_copy)
            return str(result.inserted_id)
        
        return await safe_db_operation(operation, "Error creating log")

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
        
        # Handle timestamp normalization to UTC
        if "timestamp" in update_data:
            update_data["timestamp"] = normalize_timestamp(update_data["timestamp"])
        
        # Round coordinates if location is present
        if "location" in update_data and update_data["location"]:
            update_data["location"] = round_coordinates(update_data["location"])
        
        result = await get_collection(LogOperations.collection).update_one(
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
        return await get_collection(LogOperations.collection).find_one({"_id": ObjectId(id)})

    @staticmethod
    async def get_by_train_id(train_id: str, limit: int = 10):
        """Get logs for a train, excluding test logs"""
        logs = await db[COLLECTION_NAME].find(
            {"train_id": train_id, "is_test": False},
            sort=[("timestamp", -1)]
        ).limit(limit).to_list(length=limit)
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
        result = await get_collection(LogOperations.collection).delete_one({"_id": ObjectId(id)})
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
            
        results = await get_collection(LogOperations.collection).find(filter_query).sort(
            "timestamp", -1
        ).skip(skip).limit(limit).to_list(limit)
        return results

    @staticmethod
    async def get_latest_by_train(train_id: str):
        """Get the latest log for a train, excluding test logs"""
        log = await get_collection(LogOperations.collection).find_one(
            {"train_id": train_id, "is_test": False},
            sort=[("timestamp", -1)]
        )
        return log

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
        logs = await get_collection(LogOperations.collection).find(
            {"rfid_tag": rfid_tag}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return logs

    @staticmethod
    async def get_logs_in_time_range(train_id: str, start_time: datetime, end_time: datetime):
        """
        Get logs for a train within a specific time range
        
        Args:
            train_id: Train identifier
            start_time: Start of time range (will be normalized to UTC)
            end_time: End of time range (will be normalized to UTC)
            
        Returns:
            list: List of log documents within the specified time range
        """
        # Normalize input dates to UTC
        start_time_utc = normalize_timestamp(start_time)
        end_time_utc = normalize_timestamp(end_time)
        
        logs = await get_collection(LogOperations.collection).find({
            "train_id": train_id,
            "timestamp": {
                "$gte": start_time_utc,
                "$lte": end_time_utc
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
        time_threshold = get_current_utc_time() - timedelta(hours=hours)
        logs = await get_collection(LogOperations.collection).find({
            "train_id": train_id,
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", 1).to_list(1000)
        return logs

    @classmethod
    async def get_logs_since(cls, timestamp):
        """
        Get all logs since the specified timestamp
        
        Args:
            timestamp (datetime): The timestamp to query logs from (will be normalized to UTC)
            
        Returns:
            list: List of log documents
        """
        timestamp_utc = normalize_timestamp(timestamp)
        logs = await get_collection(cls.collection).find({
            "timestamp": {"$gte": timestamp_utc}
        }).to_list(length=None)
        
        return logs

    @classmethod
    async def get_logs_by_train_since(cls, train_id, timestamp):
        """
        Get logs for a specific train since the specified timestamp
        
        Args:
            train_id (str): The train ID to filter logs
            timestamp (datetime): The timestamp to query logs from (will be normalized to UTC)
            
        Returns:
            list: List of log documents for the specified train
        """
        timestamp_utc = normalize_timestamp(timestamp)
        logs = await get_collection(cls.collection).find({
            "train_id": train_id,
            "timestamp": {"$gte": timestamp_utc}
        }).sort("timestamp", 1).to_list(length=None)
        
        return logs

    @classmethod
    async def count_logs_since(cls, timestamp):
        """
        Count logs since the specified timestamp
        
        Args:
            timestamp (datetime): The timestamp to query logs from (will be normalized to UTC)
            
        Returns:
            int: Count of logs
        """
        timestamp_utc = normalize_timestamp(timestamp)
        count = await get_collection(cls.collection).count_documents({
            "timestamp": {"$gte": timestamp_utc}
        })
        
        return count

    @classmethod
    async def get_latest_log_for_each_train(cls):
        """
        Get the latest log entry for each train
        
        Returns:
            list: Latest log document for each train
        """
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
