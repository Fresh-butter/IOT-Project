"""
Monitoring tasks module.
Implements background tasks for system monitoring and automated alerts.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.models.train import TrainModel
from app.models.log import LogOperations  # Changed from LogModel to LogOperations
from app.models.alert import AlertModel
from app.core.collision import check_all_train_collisions
from app.core.location import detect_route_deviations, check_deviation_resolved
from app.core.tracking import detect_train_status_change, get_active_trains_locations
from app.config import get_current_ist_time, get_current_utc_time, MONITOR_INTERVAL_SECONDS, TRAIN_STATUS

logger = logging.getLogger("app.tasks.monitor")

# Store previous collision risks for comparison
previous_collision_risks = {}
previous_deviations = {}

async def monitor_train_collisions():
    """Check for collision risks between active trains"""
    logger.info("Running collision detection check")
    
    try:
        # Get all active trains
        collision_risks = await check_all_train_collisions()
        
        # Log results
        if collision_risks:
            logger.warning(f"Detected {len(collision_risks)} potential collision risks")
            for risk in collision_risks:
                logger.warning(f"Collision risk between Train {risk['train1_id']} and Train {risk['train2_id']}, distance: {risk['distance']}m")
        else:
            logger.info("No collision risks detected")
            
        # Check for resolved collisions
        global previous_collision_risks
        risk_key = lambda risk: f"{risk['train1_id']}-{risk['train2_id']}"
        
        current_risk_keys = {risk_key(risk) for risk in collision_risks}
        previous_risk_keys = set(previous_collision_risks.keys())
        
        # Find resolved risks
        resolved_risks = previous_risk_keys - current_risk_keys
        for risk_id in resolved_risks:
            # Create resolution alert
            risk = previous_collision_risks[risk_id]
            message = f"COLLISION_RESOLVED: Collision risk between Train {risk['train1_id']} and Train {risk['train2_id']} resolved"
            
            # Get train references
            train1 = await TrainModel.get_by_train_id(risk['train1_id'])
            train2 = await TrainModel.get_by_train_id(risk['train2_id'])
            
            if train1 and train2:
                # Alert for train 1
                alert1_data = {
                    "sender_ref": "680142a4f8db812a8b87617c",  # System sender ID
                    "recipient_ref": str(train1["_id"]),
                    "message": message,
                    "location": risk["location"],
                    "timestamp": get_current_utc_time()  # Changed from IST to UTC
                }
                await AlertModel.create(alert1_data, create_guest_copy=False)
                
                # Alert for train 2
                alert2_data = {
                    "sender_ref": "680142a4f8db812a8b87617c",  # System sender ID
                    "recipient_ref": str(train2["_id"]),
                    "message": message,
                    "location": risk["location"],
                    "timestamp": get_current_utc_time()  # Changed from IST to UTC
                }
                await AlertModel.create(alert2_data, create_guest_copy=False)
                
                # Guest alert
                guest_alert_data = {
                    "sender_ref": "680142a4f8db812a8b87617c",  # System sender ID
                    "recipient_ref": "680142cff8db812a8b87617d",  # Guest account ID
                    "message": message,
                    "location": risk["location"],
                    "timestamp": get_current_utc_time()  # Changed from IST to UTC
                }
                await AlertModel.create(guest_alert_data, create_guest_copy=False)
                
                logger.info(f"Created resolution alert for {risk_id}")
        
        # Update previous risks
        previous_collision_risks = {risk_key(risk): risk for risk in collision_risks}
        
        return collision_risks
    except Exception as e:
        logger.error(f"Error in collision monitoring: {str(e)}")
        return []

async def monitor_train_deviations():
    """Check for route deviations for all active trains"""
    logger.info("Running route deviation check")
    
    try:
        # Get all trains in either running or stopped state
        valid_statuses = [
            TRAIN_STATUS["IN_SERVICE_RUNNING"], 
            TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
        ]
        
        active_trains = []
        for status in valid_statuses:
            trains = await TrainModel.get_all(status=status)
            active_trains.extend(trains)
        
        deviation_results = []
        
        for train in active_trains:
            train_id = train["train_id"]
            deviation = await detect_route_deviations(train_id)
            
            if deviation.get("deviation_detected"):
                logger.warning(f"Train {train_id} deviation detected: {deviation.get('distance_from_route')}m")
                deviation_results.append(deviation)
            
            # Check if previous deviation is now resolved
            global previous_deviations
            if train_id in previous_deviations and previous_deviations[train_id].get("deviation_detected"):
                if not deviation.get("deviation_detected"):
                    await check_deviation_resolved(train_id)
                    logger.info(f"Train {train_id} deviation resolved")
            
            # Update previous deviation status
            previous_deviations[train_id] = deviation
        
        return deviation_results
    except Exception as e:
        logger.error(f"Error in route deviation monitoring: {str(e)}")
        return []

async def monitor_train_status():
    """Check for train status changes (stopped/resumed)"""
    logger.info("Running train status check")
    
    try:
        # Get all active trains
        active_trains = await TrainModel.get_active_trains()
        status_changes = []
        
        for train in active_trains:
            train_id = train["train_id"]
            status = await detect_train_status_change(train_id)
            
            if status.get("status_changed"):
                logger.info(f"Train {train_id} status changed to {status.get('new_status')}")
                status_changes.append(status)
        
        return status_changes
    except Exception as e:
        logger.error(f"Error in train status monitoring: {str(e)}")
        return []

async def generate_system_status_report() -> Dict[str, Any]:
    """Generate a comprehensive system status report"""
    try:
        # Get active trains locations
        train_locations = await get_active_trains_locations()
        
        # Get recent alerts (last 5)
        recent_alerts = await AlertModel.get_recent_alerts(hours=6)
        recent_alerts_sample = recent_alerts[:5] if recent_alerts else []
        
        # Count alerts by type
        alert_types = {
            "collision_warnings": 0,
            "deviation_warnings": 0,
            "status_changes": 0,
            "other": 0
        }
        
        for alert in recent_alerts:
            message = alert.get("message", "").upper()
            if "COLLISION_WARNING" in message:
                alert_types["collision_warnings"] += 1
            elif "DEVIATION_WARNING" in message:
                alert_types["deviation_warnings"] += 1
            elif "TRAIN_STOPPED" in message or "TRAIN_RESUMED" in message:
                alert_types["status_changes"] += 1
            else:
                alert_types["other"] += 1
        
        # Get recent logs (last 20)
        recent_logs = []
        for train_loc in train_locations:
            train_id = train_loc.get("train_id")
            if train_id:
                logs = await LogOperations.get_by_train_id(train_id, limit=3)
                recent_logs.extend(logs)
        
        # Create the report
        report = {
            "timestamp": get_current_ist_time(),
            "active_trains_count": len(train_locations),
            "active_trains": train_locations,
            "recent_alerts": {
                "count": len(recent_alerts),
                "by_type": alert_types,
                "samples": recent_alerts_sample
            },
            "recent_logs_count": len(recent_logs),
            "system_status": "operational"
        }
        
        return report
    except Exception as e:
        logger.error(f"Error generating system status report: {str(e)}")
        return {
            "timestamp": get_current_ist_time(),
            "error": str(e),
            "system_status": "error"
        }

async def start_monitoring(interval_seconds: int = 60, stop_event=None):
    """
    Start background monitoring tasks with specified interval
    
    Args:
        interval_seconds: How often to run monitoring tasks (in seconds)
        stop_event: Event to signal task termination
    """
    logger.info(f"Starting background monitoring with {interval_seconds}s interval")
    
    while True:
        try:
            if stop_event and stop_event.is_set():
                logger.info("Stop event detected, terminating monitoring")
                break
                
            # Run all monitoring tasks
            await monitor_train_collisions()
            await monitor_train_deviations()
            await monitor_train_status()
            
            # Wait for next interval
            await asyncio.sleep(interval_seconds)
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            # Continue despite errors
            await asyncio.sleep(interval_seconds)
    
    logger.info("Background monitoring stopped")