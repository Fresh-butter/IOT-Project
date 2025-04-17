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
    async def get_all(limit: int = 1000, skip: int = 0):
        """
        Get all alerts with pagination
        
        Args:
            limit: Maximum number of alerts to return
            skip: Number of alerts to skip
            
        Returns:
            list: List of alerts sorted by timestamp (newest first)
        """
        alerts = await get_collection(AlertModel.collection).find().sort(
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
            {"recipient_id": ObjectId(recipient_id)}
        ).to_list(1000)
        return alerts
    
    @staticmethod
    async def create(alert_data: dict):
        """Create a new alert"""
        # Ensure timestamp is set if not provided
        if "timestamp" not in alert_data:
            alert_data["timestamp"] = get_current_ist_time()
            
        # Convert string IDs to ObjectIds
        if "sender_id" in alert_data and isinstance(alert_data["sender_id"], str):
            alert_data["sender_id"] = ObjectId(alert_data["sender_id"])
        if "recipient_id" in alert_data and isinstance(alert_data["recipient_id"], str):
            alert_data["recipient_id"] = ObjectId(alert_data["recipient_id"])
        
        # Round coordinates if location is present
        if "location" in alert_data and alert_data["location"]:
            alert_data["location"] = round_coordinates(alert_data["location"])
            
        result = await get_collection(AlertModel.collection).insert_one(alert_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def update(id: str, alert_data: dict):
        """Update an alert"""
        # Convert string IDs to ObjectIds
        if "sender_id" in alert_data and isinstance(alert_data["sender_id"], str):
            alert_data["sender_id"] = ObjectId(alert_data["sender_id"])
        if "recipient_id" in alert_data and isinstance(alert_data["recipient_id"], str):
            alert_data["recipient_id"] = ObjectId(alert_data["recipient_id"])
        
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
