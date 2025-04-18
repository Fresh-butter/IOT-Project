"""
Monitor tasks module.
Provides background tasks for monitoring train positions, potential collisions,
route deviations, and system health.
"""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.models.train import TrainModel
from app.models.log import LogModel
from app.models.alert import AlertModel
from app.models.route import RouteModel
from app.core.collision import check_all_train_collisions
from app.core.tracking import get_active_trains_locations, detect_route_deviations, is_train_on_schedule
from app.config import get_current_ist_time, SYSTEM_SENDER_ID

# Configure logging
logger = logging.getLogger("monitor")

async def monitor_train_collisions():
    """
    Monitor all active trains for potential collisions
    
    This task:
    1. Checks for potential collisions between all active trains
    2. Logs collision risks
    3. Returns a list of detected collision risks
    """
    logger.info("Starting collision monitoring task")
    try:
        collision_risks = await check_all_train_collisions()
        
        if collision_risks:
            logger.warning(f"Detected {len(collision_risks)} potential collision risks")
            for risk in collision_risks:
                logger.warning(f"Collision risk between {risk['train1_id']} and {risk['train2_id']}: {risk['collision_risk']}")
        else:
            logger.info("No collision risks detected")
            
        return collision_risks
    except Exception as e:
        logger.error(f"Error in collision monitoring task: {str(e)}")
        return []

# Update monitor_train_deviations function to use AlertService
async def monitor_train_deviations():
    """
    Monitor all active trains for route deviations
    
    This task:
    1. Checks if trains have deviated from their assigned routes
    2. Creates alerts for significant deviations using AlertService
    3. Returns a list of detected deviations
    """
    from app.services.alert_service import AlertService
    
    logger.info("Starting route deviation monitoring task")
    deviations = []
    
    try:
        active_trains = await TrainModel.get_active_trains()
        
        for train in active_trains:
            deviation_assessment = await detect_route_deviations(train["train_id"])
            
            if deviation_assessment["deviation_detected"]:
                logger.warning(f"Train {train['train_id']} has deviated from its route: {deviation_assessment['severity']} severity")
                deviations.append(deviation_assessment)
                
                # Create an alert for significant deviations using AlertService
                if deviation_assessment["severity"] in ["moderate", "high", "critical"]:
                    # Create message based on severity
                    if deviation_assessment["severity"] == "critical":
                        message = f"CRITICAL: Train {train['train_id']} has severely deviated from its route. Distance from route: {int(deviation_assessment['distance_from_route'])}m."
                    elif deviation_assessment["severity"] == "high":
                        message = f"HIGH ALERT: Train {train['train_id']} has significantly deviated from its route. Distance from route: {int(deviation_assessment['distance_from_route'])}m."
                    else:
                        message = f"WARNING: Train {train['train_id']} has moderately deviated from its route. Distance from route: {int(deviation_assessment['distance_from_route'])}m."
                    
                    # Use alert service to create the alert
                    alert_result = await AlertService.create_system_alert(
                        train["train_id"],
                        message,
                        deviation_assessment["location"]
                    )
                    
                    if alert_result.get("success"):
                        logger.info(f"Created deviation alert {alert_result.get('alert_id')} for train {train['train_id']}")
        
        if not deviations:
            logger.info("No route deviations detected")
            
        return deviations
    except Exception as e:
        logger.error(f"Error in route deviation monitoring task: {str(e)}")
        return []

async def monitor_train_schedules():
    """
    Monitor all active trains for schedule adherence
    
    This task:
    1. Checks if trains are running on schedule
    2. Creates alerts for trains that are significantly delayed
    3. Returns a list of train schedule statuses
    """
    from app.services.alert_service import AlertService
    
    logger.info("Starting schedule monitoring task")
    schedule_statuses = []
    
    try:
        active_trains = await TrainModel.get_active_trains()
        
        for train in active_trains:
            schedule_info = await is_train_on_schedule(train["train_id"])
            schedule_statuses.append(schedule_info)
            
            # Create alerts for trains that are significantly delayed (over 5 minutes)
            if not schedule_info["on_schedule"] and schedule_info["delay_seconds"] and schedule_info["delay_seconds"] > 300:
                delay_minutes = int(schedule_info["delay_seconds"] / 60)
                
                message = f"Schedule alert: Train {train['train_id']} is running approximately {delay_minutes} minutes behind schedule."
                
                # Use AlertService instead of direct model access
                alert_result = await AlertService.create_system_alert(
                    train["train_id"],
                    message,
                    schedule_info.get("location")
                )
                
                if alert_result.get("success"):
                    logger.info(f"Created schedule delay alert {alert_result.get('alert_id')} for train {train['train_id']}")
        
        if schedule_statuses:
            on_schedule_count = sum(1 for status in schedule_statuses if status.get("on_schedule"))
            logger.info(f"{on_schedule_count} of {len(schedule_statuses)} trains running on schedule")
        else:
            logger.info("No trains with schedule information found")
            
        return schedule_statuses
    except Exception as e:
        logger.error(f"Error in schedule monitoring task: {str(e)}")
        return []

async def clean_old_logs(days_to_keep: int = 30):
    """
    Remove logs older than the specified number of days
    
    Args:
        days_to_keep: Number of days of logs to retain
    """
    logger.info(f"Starting log cleanup task (keeping {days_to_keep} days of logs)")
    try:
        threshold_date = get_current_ist_time() - timedelta(days=days_to_keep)
        
        # Use the database directly for bulk operations
        from app.database import get_collection
        result = await get_collection(LogModel.collection).delete_many(
            {"timestamp": {"$lt": threshold_date}}
        )
        
        logger.info(f"Removed {result.deleted_count} old log entries")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error in log cleanup task: {str(e)}")
        return 0

async def generate_system_status_report():
    """
    Generate a system status report with key metrics
    
    This task:
    1. Collects statistics about trains, routes, and recent logs
    2. Checks for potential issues
    3. Returns a comprehensive status report
    """
    logger.info("Generating system status report")
    
    try:
        current_time = get_current_ist_time()
        
        # Get counts of various entities
        from app.database import get_collection
        train_count = await get_collection(TrainModel.collection).count_documents({})
        route_count = await get_collection(RouteModel.collection).count_documents({})
        active_train_count = len(await TrainModel.get_active_trains())
        
        # Get log counts for recent activity
        last_hour_logs = await get_collection(LogModel.collection).count_documents(
            {"timestamp": {"$gte": current_time - timedelta(hours=1)}}
        )
        
        last_day_logs = await get_collection(LogModel.collection).count_documents(
            {"timestamp": {"$gte": current_time - timedelta(days=1)}}
        )
        
        # Get alert counts for recent alerts
        open_alerts = await get_collection(AlertModel.collection).count_documents(
            {"timestamp": {"$gte": current_time - timedelta(days=1)}}
        )
        
        # Get active trains locations
        active_train_locations = await get_active_trains_locations()
        
        # Check for collision risks
        collision_risks = await check_all_train_collisions()
        
        report = {
            "timestamp": current_time,
            "total_trains": train_count,
            "total_routes": route_count,
            "active_trains": active_train_count,
            "logs_last_hour": last_hour_logs,
            "logs_last_day": last_day_logs,
            "open_alerts": open_alerts,
            "active_train_locations": active_train_locations,
            "collision_risks": collision_risks,
            "system_health": "normal"
        }
        
        # Determine system health based on collected metrics
        if collision_risks:
            report["system_health"] = "warning"
            
        if active_train_count > 0 and last_hour_logs == 0:
            # No recent logs despite active trains - could indicate communication issues
            report["system_health"] = "error"
            logger.warning("No recent logs despite active trains - possible communication issues")
        
        logger.info(f"System status report generated: health={report['system_health']}")
        return report
    except Exception as e:
        logger.error(f"Error generating system status report: {str(e)}")
        return {
            "timestamp": get_current_ist_time(),
            "error": str(e),
            "system_health": "unknown"
        }

async def run_all_monitoring_tasks():
    """
    Run all monitoring tasks sequentially
    """
    logger.info("Running all monitoring tasks")
    
    try:
        # Run tasks in sequence
        await monitor_train_collisions()
        await monitor_train_deviations()
        await monitor_train_schedules()
        await generate_system_status_report()
        
        # Periodically clean old logs (e.g., once a day)
        # This is commented out to prevent accidental data loss during development
        # Uncomment in production with appropriate days_to_keep value
        # current_hour = get_current_ist_time().hour
        # if current_hour == 3:  # Run at 3 AM
        #     await clean_old_logs(days_to_keep=30)
        
        logger.info("All monitoring tasks completed successfully")
    except Exception as e:
        logger.error(f"Error running monitoring tasks: {str(e)}")

# This function would be called from a background task scheduler
async def start_monitoring(interval_seconds: int = 60, stop_event=None):
    """
    Start the monitoring tasks with the specified interval
    
    Args:
        interval_seconds: Interval between monitoring runs in seconds
        stop_event: An asyncio.Event that signals when to stop monitoring
    """
    logger.info(f"Starting monitoring system with {interval_seconds}s interval")
    
    while True:
        if stop_event and stop_event.is_set():
            logger.info("Stopping monitoring system due to stop event")
            break
            
        await run_all_monitoring_tasks()
        
        # Use wait_for with timeout to allow checking the stop event more frequently
        if stop_event:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
                if stop_event.is_set():
                    logger.info("Stopping monitoring system due to stop event")
                    break
            except asyncio.TimeoutError:
                # Timeout is expected, continue with next iteration
                pass
        else:
            await asyncio.sleep(interval_seconds)
            
    logger.info("Monitoring system stopped")