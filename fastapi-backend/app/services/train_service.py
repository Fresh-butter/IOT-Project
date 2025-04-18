"""
Train service module.
Provides high-level operations for train management, combining models and business logic.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from bson import ObjectId

from app.models.train import TrainModel
from app.models.log import LogModel
from app.models.route import RouteModel
from app.models.alert import AlertModel
from app.core.tracking import get_train_position, is_train_on_schedule, update_train_progress
from app.core.collision import check_all_train_collisions
from app.config import get_current_ist_time, TRAIN_STATUS, SYSTEM_SENDER_ID

class TrainService:
    """Service for train-related operations"""
    
    @staticmethod
    async def get_train_with_related_data(train_id: str) -> Dict[str, Any]:
        """
        Get comprehensive train information including route and position
        
        Args:
            train_id: Train identifier
            
        Returns:
            Dict: Train details with related information
        """
        # Get basic train info
        train = await TrainModel.get_by_train_id(train_id)
        if not train:
            return {"error": "Train not found"}
        
        # Convert MongoDB _id to string
        train["_id"] = str(train["_id"])
        
        # Get position information
        position_info = await get_train_position(train_id)
        
        # Get latest log
        latest_log = await LogModel.get_latest_by_train(train_id)
        if latest_log:
            latest_log["_id"] = str(latest_log["_id"])
            # Don't keep very large fields in the summary
            latest_log.pop("raw_data", None)
        
        # Get route information if available
        route_info = None
        if train.get("current_route_id"):
            route = await RouteModel.get_by_route_id(train["current_route_id"])
            if route:
                route["_id"] = str(route["_id"])
                route_info = route
        
        # Get schedule information
        schedule_info = await is_train_on_schedule(train_id)
        
        # Get recent alerts (last 5)
        recent_alerts = await AlertModel.get_by_recipient(str(train["_id"]))
        recent_alerts = recent_alerts[:5]  # Limit to 5 most recent
        for alert in recent_alerts:
            alert["_id"] = str(alert["_id"])
            if "sender_ref" in alert and alert["sender_ref"]:
                alert["sender_ref"] = str(alert["sender_ref"])
            if "recipient_ref" in alert and alert["recipient_ref"]:
                alert["recipient_ref"] = str(alert["recipient_ref"])
        
        # Combine all information
        result = {
            "train": train,
            "position": position_info,
            "latest_log": latest_log,
            "route": route_info,
            "schedule": schedule_info,
            "recent_alerts": recent_alerts,
            "timestamp": get_current_ist_time()
        }
        
        return result
    
    @staticmethod
    async def update_train_status(train_id: str, new_status: str) -> Dict[str, Any]:
        """
        Update a train's status and handle related logic
        
        Args:
            train_id: Train identifier
            new_status: New status to set
            
        Returns:
            Dict: Result of the operation
        """
        # Validate status
        if new_status not in TRAIN_STATUS.values():
            return {
                "success": False,
                "error": f"Invalid status: {new_status}",
                "valid_statuses": list(TRAIN_STATUS.values())
            }
        
        # Get current train info
        train = await TrainModel.get_by_train_id(train_id)
        if not train:
            return {"success": False, "error": "Train not found"}
        
        # If status isn't changing, don't do anything
        if train.get("current_status") == new_status:
            return {"success": True, "message": "Status unchanged", "train_id": train_id}
        
        # Update the status
        updated = await TrainModel.update_status(str(train["_id"]), new_status)
        if not updated:
            return {"success": False, "error": "Failed to update train status"}
        
        # Get updated train
        updated_train = await TrainModel.get_by_train_id(train_id)
        
        # Create status change log
        log_data = {
            "train_id": train_id,
            "train_ref": str(train["_id"]),
            "event_type": "status_change",
            "details": {
                "old_status": train.get("current_status"),
                "new_status": new_status
            },
            "timestamp": get_current_ist_time()
        }
        
        log_id = await LogModel.create(log_data)
        
        return {
            "success": True,
            "train_id": train_id,
            "old_status": train.get("current_status"),
            "new_status": new_status,
            "log_id": log_id
        }
    
    @staticmethod
    async def process_new_log(train_id: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new log entry from a train and update tracking information
        
        Args:
            train_id: Train identifier
            log_data: Log data received from the train
            
        Returns:
            Dict: Result of the processing including tracking updates
        """
        # Ensure train exists
        train = await TrainModel.get_by_train_id(train_id)
        if not train:
            return {"success": False, "error": "Train not found"}
        
        # Add train references to the log
        log_data["train_id"] = train_id
        log_data["train_ref"] = str(train["_id"])
        
        # Set timestamp if not provided
        if "timestamp" not in log_data:
            log_data["timestamp"] = get_current_ist_time()
        
        # Create the log entry
        log_id = await LogModel.create(log_data)
        
        # Update train progress based on the new log
        progress_update = await update_train_progress(train_id, log_data)
        
        # Check for collision risks if we have location data
        collision_risks = []
        if log_data.get("location"):
            # This will check for collisions with all other active trains
            collision_risks = await check_all_train_collisions()
        
        # If route was completed, update train status
        if progress_update.get("route_completed"):
            await TrainService.update_train_status(
                train_id, 
                TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
            )
            
            # Create alert for route completion
            alert_data = {
                "sender_ref": SYSTEM_SENDER_ID,
                "recipient_ref": str(train["_id"]),
                "message": f"Train {train_id} has completed its route.",
                "location": log_data.get("location"),
                "timestamp": get_current_ist_time()
            }
            
            await AlertModel.create(alert_data)
        
        return {
            "success": True,
            "log_id": log_id,
            "train_id": train_id,
            "progress_update": progress_update,
            "collision_risks": collision_risks,
            "timestamp": get_current_ist_time()
        }
    
    @staticmethod
    async def assign_route_to_train(train_id: str, route_id: str) -> Dict[str, Any]:
        """
        Assign a route to a train and handle all related updates
        
        Args:
            train_id: Train identifier
            route_id: Route identifier
            
        Returns:
            Dict: Result of the assignment operation
        """
        # Check if train exists
        train = await TrainModel.get_by_train_id(train_id)
        if not train:
            return {"success": False, "error": "Train not found"}
        
        # Check if route exists
        route = await RouteModel.get_by_route_id(route_id)
        if not route:
            return {"success": False, "error": "Route not found"}
        
        # Check if route is already assigned to another train
        if route.get("assigned_train_id") and route["assigned_train_id"] != train_id:
            return {
                "success": False, 
                "error": f"Route already assigned to train {route['assigned_train_id']}"
            }
        
        # Perform the assignment
        await TrainModel.assign_route(str(train["_id"]), route["route_id"], str(route["_id"]))
        await RouteModel.assign_train(str(route["_id"]), train["train_id"], str(train["_id"]))
        
        # Update train status to running
        await TrainService.update_train_status(train_id, TRAIN_STATUS["IN_SERVICE_RUNNING"])
        
        # Create a log entry for the route assignment
        log_data = {
            "train_id": train_id,
            "train_ref": str(train["_id"]),
            "event_type": "route_assigned",
            "details": {
                "route_id": route_id,
                "route_name": route.get("name")
            },
            "timestamp": get_current_ist_time()
        }
        
        log_id = await LogModel.create(log_data)
        
        return {
            "success": True,
            "train_id": train_id,
            "route_id": route_id,
            "status": TRAIN_STATUS["IN_SERVICE_RUNNING"],
            "log_id": log_id,
            "timestamp": get_current_ist_time()
        }
    
    @staticmethod
    async def get_active_train_dashboard() -> Dict[str, Any]:
        """
        Get a dashboard summary of all active trains
        
        Returns:
            Dict: Dashboard data for active trains
        """
        # Get all active trains
        active_trains = await TrainModel.get_active_trains()
        
        dashboard_data = {
            "timestamp": get_current_ist_time(),
            "active_train_count": len(active_trains),
            "trains": [],
            "collision_risks": [],
            "alerts": []
        }
        
        # Get detailed information for each train
        for train in active_trains:
            train_id = train["train_id"]
            position = await get_train_position(train_id)
            schedule = await is_train_on_schedule(train_id)
            
            train_data = {
                "train_id": train_id,
                "name": train.get("name"),
                "status": train.get("current_status"),
                "position": {
                    "location": position.get("location"),
                    "nearest_checkpoint": position.get("nearest_checkpoint"),
                    "next_checkpoint": position.get("next_checkpoint")
                },
                "schedule": {
                    "on_schedule": schedule.get("on_schedule"),
                    "delay_seconds": schedule.get("delay_seconds")
                },
                "route_id": train.get("current_route_id")
            }
            
            dashboard_data["trains"].append(train_data)
        
        # Check for collision risks
        collision_risks = await check_all_train_collisions()
        if collision_risks:
            dashboard_data["collision_risks"] = collision_risks
            dashboard_data["collision_count"] = len(collision_risks)
        
        # Get recent alerts (last 5)
        recent_alerts = await AlertModel.get_recent_alerts(hours=2)
        dashboard_data["alerts"] = recent_alerts[:5]  # Limit to 5 most recent
        dashboard_data["alert_count"] = len(recent_alerts)
        
        return dashboard_data