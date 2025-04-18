"""
Alert model module.
Defines the structure and operations for alert data in MongoDB.
"""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import get_collection
from app.config import get_current_ist_time
from app.utils import round_coordinates

class AlertModel:
    collection = "alerts"
    
    @staticmethod
    async def get_all(limit: int = 1000, skip: int = 0, filter_param=None):
        """
        Get all alerts with pagination and optional filtering
        
        Args:
            limit: Maximum number of alerts to return
            skip: Number of alerts to skip
            filter_param: Optional filter parameter
            
        Returns:
            list: List of alerts sorted by timestamp (newest first)
        """
        filter_query = {}
        if filter_param is not None:
            filter_query["field_name"] = filter_param
            
        alerts = await get_collection(AlertModel.collection).find(filter_query).sort(
            "timestamp", -1
        ).skip(skip).limit(limit).to_list(limit)
        return alerts
    
    @staticmethod
    async def get_by_id(id: str):
        """
        Get alert by ID
        
        Args:
            id: Alert document ID
            
        Returns:
            dict: Alert document or None if not found
        """
        return await get_collection(AlertModel.collection).find_one({"_id": ObjectId(id)})
    
    @staticmethod
    async def get_by_recipient(recipient_id: str):
        """
        Get alerts by recipient ID
        
        Args:
            recipient_id: ID of the train that should receive the alerts
            
        Returns:
            list: List of alert documents
        """
        alerts = await get_collection(AlertModel.collection).find(
            {"recipient_ref": ObjectId(recipient_id)}
        ).to_list(1000)
        return alerts
    
    @staticmethod
    async def create(alert_data: dict):
        """Create a new alert"""
        # Ensure timestamp is set if not provided
        if "timestamp" not in alert_data:
            alert_data["timestamp"] = get_current_ist_time()
            
        # Convert string IDs to ObjectIds
        if "sender_ref" in alert_data and isinstance(alert_data["sender_ref"], str):
            alert_data["sender_ref"] = ObjectId(alert_data["sender_ref"])
        if "recipient_ref" in alert_data and isinstance(alert_data["recipient_ref"], str):
            alert_data["recipient_ref"] = ObjectId(alert_data["recipient_ref"])
        
        # Round coordinates if location is present
        if "location" in alert_data and alert_data["location"]:
            alert_data["location"] = round_coordinates(alert_data["location"])
            
        result = await get_collection(AlertModel.collection).insert_one(alert_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def update(id: str, alert_data: dict):
        """Update an alert"""
        # Convert string IDs to ObjectIds
        if "sender_ref" in alert_data and isinstance(alert_data["sender_ref"], str):
            alert_data["sender_ref"] = ObjectId(alert_data["sender_ref"])
        if "recipient_ref" in alert_data and isinstance(alert_data["recipient_ref"], str):
            alert_data["recipient_ref"] = ObjectId(alert_data["recipient_ref"])
        
        # Round coordinates if location is present
        if "location" in alert_data and alert_data["location"]:
            alert_data["location"] = round_coordinates(alert_data["location"])
            
        result = await get_collection(AlertModel.collection).update_one(
            {"_id": ObjectId(id)}, {"$set": alert_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(id: str):
        """Delete an alert"""
        result = await get_collection(AlertModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    @staticmethod
    async def get_by_sender(sender_id: str, limit: int = 100):
        """
        Get alerts sent by a specific sender
        
        Args:
            sender_id: ID of the train that sent the alerts
            limit: Maximum number of alerts to return
            
        Returns:
            list: List of alert documents
        """
        alerts = await get_collection(AlertModel.collection).find(
            {"sender_ref": ObjectId(sender_id)}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return alerts
    
    @staticmethod
    async def get_recent_alerts(hours: int = 24):
        """
        Get all alerts from the last X hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            list: List of recent alert documents
        """
        time_threshold = get_current_ist_time() - datetime.timedelta(hours=hours)
        alerts = await get_collection(AlertModel.collection).find(
            {"timestamp": {"$gte": time_threshold}}
        ).sort("timestamp", -1).to_list(1000)
        return alerts
