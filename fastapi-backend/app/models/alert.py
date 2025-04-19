"""
Alert model module.
Defines the structure and operations for alert data in MongoDB.
"""
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
import datetime as dt
import logging

from app.database import get_collection, safe_db_operation, PyObjectId
from app.config import get_current_utc_time, SYSTEM_SENDER_ID, GUEST_RECIPIENT_ID
from app.utils import round_coordinates, normalize_timestamp

class AlertModel:
    collection = "alerts"
    
    @staticmethod
    async def get_all(limit: int = 1000, skip: int = 0, filter_param=None):
        """Get all alerts with optional filtering"""
        async def operation():
            filter_dict = filter_param or {}
            alerts = await get_collection(AlertModel.collection).find(
                filter_dict
            ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
            
            # Convert ObjectIds to strings
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
                if isinstance(alert.get("sender_ref"), ObjectId):
                    alert["sender_ref"] = str(alert["sender_ref"])
                if isinstance(alert.get("recipient_ref"), ObjectId):
                    alert["recipient_ref"] = str(alert["recipient_ref"])
                    
            return alerts
        
        return await safe_db_operation(operation, "Error retrieving alerts")

    @staticmethod
    async def get_by_id(id: str):
        """Get an alert by ID"""
        async def operation():
            alert = await get_collection(AlertModel.collection).find_one({"_id": ObjectId(id)})
            if alert:
                alert["_id"] = str(alert["_id"])
                if isinstance(alert.get("sender_ref"), ObjectId):
                    alert["sender_ref"] = str(alert["sender_ref"])
                if isinstance(alert.get("recipient_ref"), ObjectId):
                    alert["recipient_ref"] = str(alert["recipient_ref"])
            return alert
        
        return await safe_db_operation(operation, "Error retrieving alert by ID")

    @staticmethod
    async def get_by_recipient(recipient_id: str):
        """
        Get alerts by recipient ID
        
        Args:
            recipient_id: ID of the train that should receive the alerts
            
        Returns:
            list: List of alert documents
        """
        async def operation():
            try:
                recipient_obj_id = ObjectId(recipient_id)
                filter_dict = {"recipient_ref": recipient_obj_id}
            except:
                # If conversion fails, try string match
                filter_dict = {"recipient_ref": recipient_id}
                
            alerts = await get_collection(AlertModel.collection).find(
                filter_dict
            ).sort("timestamp", -1).to_list(1000)
            
            # Convert ObjectIds to strings
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
                if isinstance(alert.get("sender_ref"), ObjectId):
                    alert["sender_ref"] = str(alert["sender_ref"])
                if isinstance(alert.get("recipient_ref"), ObjectId):
                    alert["recipient_ref"] = str(alert["recipient_ref"])
                    
            return alerts
        
        return await safe_db_operation(operation, "Error retrieving alerts by recipient")

    @staticmethod
    async def create(alert_data: dict, create_guest_copy: bool = True):
        """
        Create a new alert
        
        Args:
            alert_data: Alert data
            create_guest_copy: Whether to create a copy for the guest account
        """
        async def operation():
            # Ensure timestamp is set if not provided and normalized to UTC
            if "timestamp" not in alert_data:
                alert_data["timestamp"] = get_current_utc_time()
            else:
                # If timestamp is provided, normalize it to UTC
                alert_data["timestamp"] = normalize_timestamp(alert_data["timestamp"])
                
            # Handle ID conversions if needed
            if "sender_ref" in alert_data and isinstance(alert_data["sender_ref"], str):
                try:
                    alert_data["sender_ref"] = ObjectId(alert_data["sender_ref"])
                except:
                    # Keep as string if it's not a valid ObjectId
                    pass
                    
            if "recipient_ref" in alert_data and isinstance(alert_data["recipient_ref"], str):
                try:
                    alert_data["recipient_ref"] = ObjectId(alert_data["recipient_ref"])
                except:
                    # Keep as string if it's not a valid ObjectId
                    pass
            
            # Round coordinates if location is present
            if "location" in alert_data and alert_data["location"]:
                alert_data["location"] = round_coordinates(alert_data["location"])
            
            # Create the alert
            result = await get_collection(AlertModel.collection).insert_one(alert_data)
            alert_id = str(result.inserted_id)
            
            # Create duplicate alert for guest account if requested and this isn't already for the guest
            if create_guest_copy and str(alert_data.get("recipient_ref")) != GUEST_RECIPIENT_ID:
                try:
                    guest_alert = alert_data.copy()
                    guest_alert["recipient_ref"] = GUEST_RECIPIENT_ID
                    guest_alert["_id"] = ObjectId()  # New ObjectId to avoid duplicate key error
                    await get_collection(AlertModel.collection).insert_one(guest_alert)
                except Exception as e:
                    # Log error but don't fail the whole operation
                    logging.error(f"Failed to create guest alert: {str(e)}")
            
            return alert_id
        
        return await safe_db_operation(operation, "Error creating alert")

    @staticmethod
    async def update(id: str, alert_data: dict):
        """Update an alert"""
        async def operation():
            # Convert string IDs to ObjectIds if needed
            if "sender_ref" in alert_data and isinstance(alert_data["sender_ref"], str):
                try:
                    alert_data["sender_ref"] = ObjectId(alert_data["sender_ref"])
                except:
                    # Keep as string if it's not a valid ObjectId
                    pass
                    
            if "recipient_ref" in alert_data and isinstance(alert_data["recipient_ref"], str):
                try:
                    alert_data["recipient_ref"] = ObjectId(alert_data["recipient_ref"])
                except:
                    # Keep as string if it's not a valid ObjectId
                    pass
            
            # If timestamp is being updated, normalize it to UTC
            if "timestamp" in alert_data:
                alert_data["timestamp"] = normalize_timestamp(alert_data["timestamp"])
                
            # Round coordinates if location is present
            if "location" in alert_data and alert_data["location"]:
                alert_data["location"] = round_coordinates(alert_data["location"])
                
            # Update the alert
            result = await get_collection(AlertModel.collection).update_one(
                {"_id": ObjectId(id)}, {"$set": alert_data}
            )
            
            if result.modified_count > 0:
                return await AlertModel.get_by_id(id)
            return None
        
        return await safe_db_operation(operation, "Error updating alert")
    
    @staticmethod
    async def delete(id: str):
        """Delete an alert"""
        async def operation():
            result = await get_collection(AlertModel.collection).delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        
        return await safe_db_operation(operation, "Error deleting alert")
    
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
        async def operation():
            try:
                sender_obj_id = ObjectId(sender_id)
                filter_dict = {"sender_ref": sender_obj_id}
            except:
                # If conversion fails, try string match
                filter_dict = {"sender_ref": sender_id}
                
            alerts = await get_collection(AlertModel.collection).find(
                filter_dict
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            # Convert ObjectIds to strings
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
                if isinstance(alert.get("sender_ref"), ObjectId):
                    alert["sender_ref"] = str(alert["sender_ref"])
                if isinstance(alert.get("recipient_ref"), ObjectId):
                    alert["recipient_ref"] = str(alert["recipient_ref"])
                    
            return alerts
        
        return await safe_db_operation(operation, "Error retrieving alerts by sender")
    
    @staticmethod
    async def get_recent_alerts(hours: int = 24):
        """
        Get all alerts from the last X hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            list: List of recent alert documents
        """
        async def operation():
            time_threshold = get_current_utc_time() - dt.timedelta(hours=hours)
            alerts = await get_collection(AlertModel.collection).find(
                {"timestamp": {"$gte": time_threshold}}
            ).sort("timestamp", -1).to_list(1000)
            
            # Convert ObjectIds to strings
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
                if isinstance(alert.get("sender_ref"), ObjectId):
                    alert["sender_ref"] = str(alert["sender_ref"])
                if isinstance(alert.get("recipient_ref"), ObjectId):
                    alert["recipient_ref"] = str(alert["recipient_ref"])
                    
            return alerts
        
        return await safe_db_operation(operation, "Error retrieving recent alerts")
