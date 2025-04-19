"""
Alert service module.
Defines business logic for alert management.
"""
from typing import Dict, Any, List, Optional
from ..models.alert import AlertModel
from ..models.train import TrainModel
from app.config import get_current_utc_time, convert_to_ist, SYSTEM_SENDER_ID, GUEST_RECIPIENT_ID
from app.utils import format_timestamp_ist

class AlertService:
    """Alert service for business logic"""
    
    @staticmethod
    async def create_system_alert(recipient_id: str, message: str, location: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Create a system-generated alert for a train
        
        Args:
            recipient_id: Train ID to receive the alert
            message: Alert message
            location: Optional location coordinates [longitude, latitude]
            
        Returns:
            Dict: Result of the alert creation
        """
        # Verify recipient train exists
        train = await TrainModel.get_by_train_id(recipient_id)
        if not train:
            return {"success": False, "error": "Recipient train not found"}
        
        # Create alert
        alert_data = {
            "sender_ref": SYSTEM_SENDER_ID,
            "recipient_ref": str(train["_id"]),
            "message": message,
            "location": location,
            "timestamp": get_current_utc_time()  # Always use UTC for storage
        }
        
        alert_id = await AlertModel.create(alert_data)
        
        return {
            "success": True,
            "alert_id": alert_id,
            "recipient_id": recipient_id,
            "timestamp": format_timestamp_ist(get_current_utc_time())  # Convert to IST for response
        }

    @staticmethod
    async def generate_alert_summary(hours: int = 24) -> Dict[str, Any]:
        """
        Generate a summary of alerts from the past N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dict: Alert summary statistics
        """
        alerts = await AlertModel.get_recent_alerts(hours)
        
        # Initialize counters
        total = len(alerts)
        collision_alerts = 0
        deviation_alerts = 0
        schedule_alerts = 0
        system_alerts = 0
        train_to_train_alerts = 0
        other_alerts = 0
        
        severity_counts = {}
        recipient_counts = {}
        
        # Process alerts
        for alert in alerts:
            # Count by sender
            if alert.get("sender_ref") == SYSTEM_SENDER_ID:
                system_alerts += 1
            
            # Count by content (simplistic, would be better with categories field)
            message = alert.get("message", "").lower()
            
            if "collision" in message:
                collision_alerts += 1
            elif "deviat" in message:
                deviation_alerts += 1
            elif "schedule" in message or "delay" in message:
                schedule_alerts += 1
            else:
                other_alerts += 1
                
            # Count by recipient
            recipient = alert.get("recipient_ref")
            if recipient == GUEST_RECIPIENT_ID:
                # Skip guest alerts to avoid double counting
                continue
                
            if recipient:
                recipient_counts[recipient] = recipient_counts.get(recipient, 0) + 1
            
            # Count train-to-train alerts
            if alert.get("sender_ref") != SYSTEM_SENDER_ID and alert.get("recipient_ref") != GUEST_RECIPIENT_ID:
                train_to_train_alerts += 1
                
            # Extract severity from message for counts
            if "critical" in message.lower():
                severity_counts["critical"] = severity_counts.get("critical", 0) + 1
            elif "high" in message.lower():
                severity_counts["high"] = severity_counts.get("high", 0) + 1
            elif "warning" in message.lower():
                severity_counts["warning"] = severity_counts.get("warning", 0) + 1
            else:
                severity_counts["info"] = severity_counts.get("info", 0) + 1
        
        # Get recent critical alerts
        critical_alerts = []
        for alert in alerts:
            if "critical" in alert.get("message", "").lower():
                critical_alerts.append({
                    "id": alert.get("_id"),
                    "message": alert.get("message"),
                    "timestamp": alert.get("timestamp"),  # Will be converted to IST by the schema
                    "recipient_ref": alert.get("recipient_ref")
                })
                if len(critical_alerts) >= 5:  # Limit to 5 most recent
                    break
        
        return {
            "total_alerts": total,
            "collision_alerts": collision_alerts,
            "deviation_alerts": deviation_alerts,
            "schedule_alerts": schedule_alerts,
            "system_alerts": system_alerts,
            "train_to_train_alerts": train_to_train_alerts,
            "other_alerts": other_alerts,
            "by_severity": severity_counts,
            "by_recipient": recipient_counts,
            "recent_critical": critical_alerts,
            "timestamp": get_current_utc_time(),  # Will be converted to IST by the schema
            "period_hours": hours
        }