"""
Analytics API module.
Provides specialized endpoints for data analysis and reporting.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from bson import ObjectId

from app.models.train import TrainModel
from app.models.log import LogModel
from app.models.route import RouteModel
from app.models.alert import AlertModel
from app.services.route_service import RouteService
from app.services.alert_service import AlertService
from app.core.tracking import get_active_trains_locations
from app.config import get_current_ist_time

router = APIRouter()

@router.get("/system-status", 
           summary="Get system status dashboard", 
           description="Returns a comprehensive overview of the system status")
async def get_system_status():
    """
    Get a comprehensive system status report including trains, routes, 
    and recent events.
    """
    # Get active trains
    active_trains = await TrainModel.get_active_trains()
    active_train_count = len(active_trains)
    
    # Get total counts
    from app.database import get_collection
    train_count = await get_collection(TrainModel.collection).count_documents({})
    route_count = await get_collection(RouteModel.collection).count_documents({})
    
    # Get recent logs and alerts
    current_time = get_current_ist_time()
    last_hour = current_time - timedelta(hours=1)
    recent_logs = await LogModel.get_logs_since(last_hour)
    recent_alerts = await AlertModel.get_recent_alerts(hours=1)
    
    # Get active trains with locations
    train_locations = await get_active_trains_locations()
    
    # Get route statistics
    route_stats = await RouteService.get_route_statistics()
    
    # Get alert summary
    alert_summary = await AlertService.get_alert_summary(hours=24)
    
    return {
        "timestamp": current_time,
        "active_trains": active_train_count,
        "total_trains": train_count,
        "total_routes": route_count,
        "recent_logs": len(recent_logs),
        "recent_alerts": len(recent_alerts),
        "train_locations": train_locations,
        "route_statistics": route_stats,
        "alert_statistics": alert_summary
    }

@router.get("/collision-risk-analysis", 
           summary="Analyze collision risks", 
           description="Provides a detailed analysis of current and potential collision risks")
async def analyze_collision_risks():
    """
    Perform a comprehensive analysis of collision risks in the system.
    """
    # Use the alert service to check for collision risks
    collision_result = await AlertService.create_collision_risk_alerts()
    
    # Get active trains
    train_locations = await get_active_trains_locations()
    
    # Compile a risk assessment
    risk_assessment = {
        "timestamp": get_current_ist_time(),
        "active_train_count": len(train_locations),
        "collision_risks": collision_result.get("collision_risks", []),
        "risk_count": len(collision_result.get("collision_risks", [])),
        "risk_level": "none",
        "train_locations": train_locations
    }
    
    # Determine overall risk level
    if risk_assessment["risk_count"] > 0:
        critical_count = sum(1 for risk in risk_assessment["collision_risks"] 
                            if risk.get("collision_risk") == "critical")
        warning_count = sum(1 for risk in risk_assessment["collision_risks"] 
                           if risk.get("collision_risk") == "warning")
        
        if critical_count > 0:
            risk_assessment["risk_level"] = "critical"
        elif warning_count > 0:
            risk_assessment["risk_level"] = "warning"
        else:
            risk_assessment["risk_level"] = "low"
    
    return risk_assessment

@router.get("/train-stats/{train_id}", 
           summary="Get train statistics", 
           description="Returns statistical analysis for a specific train")
async def get_train_statistics(train_id: str, days: int = Query(7, ge=1, le=30)):
    """
    Get statistical analysis for a specific train.
    
    Args:
        train_id: Train identifier
        days: Number of days to analyze (1-30)
    """
    # Check if train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    
    # Get logs for the specified time period
    end_date = get_current_ist_time()
    start_date = end_date - timedelta(days=days)
    
    logs = await LogModel.get_train_logs_between(train_id, start_date, end_date)
    
    if not logs:
        return {
            "train_id": train_id,
            "period_days": days,
            "log_count": 0,
            "message": "No logs found for the specified period"
        }
    
    # Extract location and timestamp data
    locations = []
    timestamps = []
    for log in logs:
        if log.get("location") and log.get("timestamp"):
            locations.append(log["location"])
            timestamps.append(log["timestamp"])
    
    # Calculate distance traveled
    total_distance = 0
    if len(locations) > 1:
        from app.utils import calculate_distance
        for i in range(1, len(locations)):
            total_distance += calculate_distance(locations[i-1], locations[i])
    
    # Calculate average speed
    avg_speed = 0
    if len(timestamps) > 1 and total_distance > 0:
        total_time_seconds = (timestamps[-1] - timestamps[0]).total_seconds()
        if total_time_seconds > 0:
            avg_speed = total_distance / total_time_seconds * 3.6  # m/s to km/h
    
    # Get delay statistics
    delay_logs = [log for log in logs if log.get("event_type") == "schedule_check" 
                 and log.get("details", {}).get("delay_seconds") is not None]
    
    avg_delay = 0
    max_delay = 0
    if delay_logs:
        delays = [log["details"]["delay_seconds"] for log in delay_logs]
        avg_delay = sum(delays) / len(delays)
        max_delay = max(delays)
    
    # Get alerts for this train
    alerts = await AlertModel.get_by_recipient(str(train["_id"]))
    recent_alerts = [a for a in alerts if a.get("timestamp") and a["timestamp"] >= start_date]
    
    # Count alerts by type
    collision_alerts = sum(1 for a in recent_alerts if "collision" in a.get("message", "").lower())
    deviation_alerts = sum(1 for a in recent_alerts if "deviat" in a.get("message", "").lower())
    schedule_alerts = sum(1 for a in recent_alerts if "schedule" in a.get("message", "").lower())
    
    # Compile statistics
    stats = {
        "train_id": train_id,
        "train_name": train.get("name"),
        "period_days": days,
        "log_count": len(logs),
        "distance_traveled_km": round(total_distance / 1000, 2),
        "average_speed_kmh": round(avg_speed, 2),
        "average_delay_seconds": round(avg_delay, 2),
        "max_delay_seconds": max_delay,
        "alert_count": len(recent_alerts),
        "alert_types": {
            "collision": collision_alerts,
            "deviation": deviation_alerts,
            "schedule": schedule_alerts,
            "other": len(recent_alerts) - collision_alerts - deviation_alerts - schedule_alerts
        },
        "first_log": timestamps[0] if timestamps else None,
        "last_log": timestamps[-1] if timestamps else None
    }
    
    return stats

@router.get("/route-analytics/{route_id}", 
           summary="Get route analytics", 
           description="Returns analytics for a specific route")
async def get_route_analytics(route_id: str):
    """
    Get analytics for a specific route.
    
    Args:
        route_id: Route identifier
    """
    # Get route data
    route = await RouteModel.get_by_route_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    
    # Get route details with related data
    route_details = await RouteService.get_route_with_related_data(route_id)
    
    # Get all logs for trains that have used this route
    logs = []
    if route.get("assigned_train_id"):
        # Get logs for the currently assigned train
        train_logs = await LogModel.get_by_train(route["assigned_train_id"])
        # Filter to logs related to this route
        route_logs = [log for log in train_logs if log.get("details", {}).get("route_id") == route_id]
        logs.extend(route_logs)
    
    # Calculate completion statistics
    completed_runs = 0
    average_completion_time = None
    completion_times = []
    
    # Find completed route runs by looking for route_completed events
    for log in logs:
        if log.get("event_type") == "route_completed" and log.get("details", {}).get("route_id") == route_id:
            completed_runs += 1
            if log.get("details", {}).get("completion_time_seconds"):
                completion_times.append(log["details"]["completion_time_seconds"])
    
    if completion_times:
        average_completion_time = sum(completion_times) / len(completion_times)
    
    # Calculate deviation statistics
    deviation_events = [log for log in logs if log.get("event_type") == "route_deviation" 
                       and log.get("details", {}).get("route_id") == route_id]
    
    avg_deviation_distance = None
    max_deviation_distance = None
    if deviation_events:
        distances = [log["details"].get("distance_meters", 0) for log in deviation_events 
                    if log.get("details", {}).get("distance_meters")]
        if distances:
            avg_deviation_distance = sum(distances) / len(distances)
            max_deviation_distance = max(distances)
    
    # Calculate most problematic segments
    problematic_segments = {}
    for log in logs:
        if (log.get("event_type") in ["route_deviation", "checkpoint_missed"] and 
            log.get("details", {}).get("segment_index") is not None):
            segment_idx = log["details"]["segment_index"]
            if segment_idx not in problematic_segments:
                problematic_segments[segment_idx] = 0
            problematic_segments[segment_idx] += 1
    
    most_problematic = None
    if problematic_segments:
        most_problematic = max(problematic_segments.items(), key=lambda x: x[1])
    
    # Compile the analytics
    analytics = {
        "route_id": route_id,
        "route_name": route.get("name"),
        "total_distance_meters": route_details.get("total_distance_meters"),
        "checkpoint_count": route_details.get("checkpoint_count"),
        "completed_runs": completed_runs,
        "average_completion_time_seconds": average_completion_time,
        "deviation_events": len(deviation_events),
        "average_deviation_meters": avg_deviation_distance,
        "max_deviation_meters": max_deviation_distance,
        "most_problematic_segment": most_problematic,
        "collision_risks": route_details.get("collision_risks"),
        "assigned_train": route.get("assigned_train_id")
    }
    
    return analytics

@router.get("/logs-analysis", 
           summary="Analyze system logs", 
           description="Get analysis of system logs for the specified time period")
async def analyze_logs(hours: int = Query(24, ge=1, le=168)):
    """
    Analyze system logs for the specified time period.
    
    Args:
        hours: Number of hours to analyze (1-168)
    """
    # Get logs for the specified time period
    end_time = get_current_ist_time()
    start_time = end_time - timedelta(hours=hours)
    
    logs = await LogModel.get_logs_since(start_time)
    
    if not logs:
        return {
            "period_hours": hours,
            "log_count": 0,
            "message": "No logs found for the specified period"
        }
    
    # Group logs by type
    log_types = {}
    for log in logs:
        event_type = log.get("event_type", "unknown")
        if event_type not in log_types:
            log_types[event_type] = 0
        log_types[event_type] += 1
    
    # Group logs by train
    train_logs = {}
    for log in logs:
        train_id = log.get("train_id")
        if train_id:
            if train_id not in train_logs:
                train_logs[train_id] = 0
            train_logs[train_id] += 1
    
    # Group logs by hour
    logs_by_hour = {}
    for log in logs:
        if log.get("timestamp"):
            hour = log["timestamp"].replace(minute=0, second=0, microsecond=0)
            if hour not in logs_by_hour:
                logs_by_hour[hour] = 0
            logs_by_hour[hour] += 1
    
    # Count GPS accuracy levels
    gps_accuracy = {}
    for log in logs:
        if log.get("accuracy"):
            accuracy = log["accuracy"]
            if accuracy not in gps_accuracy:
                gps_accuracy[accuracy] = 0
            gps_accuracy[accuracy] += 1
    
    # Find logs with RFID tags
    rfid_logs = sum(1 for log in logs if log.get("rfid_tag"))
    
    # Compile the analysis
    analysis = {
        "period_hours": hours,
        "log_count": len(logs),
        "start_time": start_time,
        "end_time": end_time,
        "log_types": log_types,
        "logs_by_train": train_logs,
        "top_trains": sorted(train_logs.items(), key=lambda x: x[1], reverse=True)[:5],
        "logs_by_hour": {str(k): v for k, v in logs_by_hour.items()},
        "gps_accuracy_distribution": gps_accuracy,
        "rfid_tag_count": rfid_logs,
        "average_logs_per_hour": len(logs) / hours
    }
    
    return analysis

@router.get("/performance-metrics", 
           summary="Get system performance metrics", 
           description="Returns performance metrics for the collision avoidance system")
async def get_performance_metrics(days: int = Query(7, ge=1, le=30)):
    """
    Get performance metrics for the collision avoidance system.
    
    Args:
        days: Number of days to analyze (1-30)
    """
    # Define time range
    end_time = get_current_ist_time()
    start_time = end_time - timedelta(days=days)
    
    # Get collision events
    from app.database import get_collection
    
    collision_alerts = await get_collection(AlertModel.collection).count_documents({
        "timestamp": {"$gte": start_time},
        "message": {"$regex": "collision", "$options": "i"}
    })
    
    # Get deviation events
    deviation_alerts = await get_collection(AlertModel.collection).count_documents({
        "timestamp": {"$gte": start_time},
        "message": {"$regex": "deviat", "$options": "i"}
    })
    
    # Get schedule delay events
    schedule_alerts = await get_collection(AlertModel.collection).count_documents({
        "timestamp": {"$gte": start_time},
        "message": {"$regex": "schedule|delay", "$options": "i"}
    })
    
    # Get total logs
    total_logs = await get_collection(LogModel.collection).count_documents({
        "timestamp": {"$gte": start_time}
    })
    
    # Get total trains active during period
    active_train_logs = await get_collection(LogModel.collection).distinct(
        "train_id", 
        {"timestamp": {"$gte": start_time}}
    )
    active_train_count = len(active_train_logs)
    
    # Calculate average logs per train
    avg_logs_per_train = 0
    if active_train_count > 0:
        avg_logs_per_train = total_logs / active_train_count
    
    # Calculate system uptime (approximation)
    total_hours = days * 24
    hours_with_logs = await get_collection(LogModel.collection).distinct(
        "timestamp", 
        {"timestamp": {"$gte": start_time}}
    )
    hours_with_logs = set(h.replace(minute=0, second=0, microsecond=0) for h in hours_with_logs)
    uptime_percent = len(hours_with_logs) / total_hours * 100 if total_hours > 0 else 0
    
    # Compile metrics
    metrics = {
        "period_days": days,
        "start_time": start_time,
        "end_time": end_time,
        "total_logs": total_logs,
        "active_trains": active_train_count,
        "alert_counts": {
            "collision": collision_alerts,
            "deviation": deviation_alerts,
            "schedule": schedule_alerts,
            "total": collision_alerts + deviation_alerts + schedule_alerts
        },
        "logs_per_train": round(avg_logs_per_train, 2),
        "uptime_percent": round(uptime_percent, 2),
        "alert_rate": round((collision_alerts + deviation_alerts + schedule_alerts) / days, 2)
    }
    
    return metrics