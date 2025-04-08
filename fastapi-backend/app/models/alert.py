"""
Alert model module.
Defines the structure and operations for alert data in MongoDB.
"""
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from app.database import get_collection

class AlertModel:
    collection = "alerts"
    
    @staticmethod
    async def get_all():
        """Get all alerts"""
        alerts = await get_collection(AlertModel.collection).find().to_list(1000)
        return alerts
    
    @staticmethod
    async def get_by_id(id: str):
        """Get alert by ID"""
        return await get_collection(AlertModel.collection).find_one({"_id": ObjectId(id)})
    
    @staticmethod
    async def get_by_recipient(recipient_id: str):
        """Get alerts by recipient ID"""
        alerts = await get_collection(AlertModel.collection).find(
            {"recipient_id": ObjectId(recipient_id)}
        ).to_list(1000)
        return alerts
    
    @staticmethod
    async def create(alert_data: dict):
        """Create a new alert"""
        # Ensure timestamp is set if not provided
        if "timestamp" not in alert_data:
            alert_data["timestamp"] = datetime.utcnow()
            
        # Convert string IDs to ObjectIds
        if "sender_id" in alert_data and isinstance(alert_data["sender_id"], str):
            alert_data["sender_id"] = ObjectId(alert_data["sender_id"])
        if "recipient_id" in alert_data and isinstance(alert_data["recipient_id"], str):
            alert_data["recipient_id"] = ObjectId(alert_data["recipient_id"])
            
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
            
        result = await get_collection(AlertModel.collection).update_one(
            {"_id": ObjectId(id)}, {"$set": alert_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(id: str):
        """Delete an alert"""
        result = await get_collection(AlertModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
