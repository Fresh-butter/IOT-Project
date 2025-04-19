"""
Route service module.
Provides high-level operations for route management, combining models and business logic.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from bson import ObjectId

from app.models.route import RouteModel
from app.models.train import TrainModel
from app.models.log import LogModel
from app.config import get_current_utc_time
from app.utils import format_timestamp_ist, normalize_timestamp, calculate_distance

class RouteService:
    """Service for route-related operations"""
    
    @staticmethod
    async def get_route_details(route_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a route
        
        Args:
            route_id: Route identifier
            
        Returns:
            Dict: Route details and associated information
        """
        route = await RouteModel.get_by_route_id(route_id)
        if not route:
            return {"error": f"Route {route_id} not found"}
        
        # Get assigned train details if any
        train_details = None
        if route.get("assigned_train_id"):
            train = await TrainModel.get_by_train_id(route["assigned_train_id"])
            if train:
                train_details = {
                    "train_id": train["train_id"],
                    "train_name": train.get("train_name"),
                    "current_status": train.get("current_status")
                }
        
        # Construct the detailed response
        result = {
            "route_id": route["route_id"],
            "route_name": route.get("route_name"),
            "start_time": route.get("start_time"),
            "formatted_start_time": format_timestamp_ist(route.get("start_time")),
            "assigned_train": train_details,
            "checkpoint_count": len(route.get("checkpoints", [])),
            "total_distance_km": await RouteService.calculate_route_distance(route),
            "details": route
        }
        
        return result
    
    @staticmethod
    async def calculate_route_distance(route: Dict[str, Any]) -> float:
        """
        Calculate the total distance of a route in kilometers
        
        Args:
            route: Route document with checkpoints
            
        Returns:
            float: Distance in kilometers
        """
        if not route or not route.get("checkpoints") or len(route.get("checkpoints", [])) < 2:
            return 0.0
        
        checkpoints = route["checkpoints"]
        total_distance = 0.0
        
        for i in range(len(checkpoints) - 1):
            if not checkpoints[i].get("location") or not checkpoints[i+1].get("location"):
                continue
                
            distance = calculate_distance(
                checkpoints[i]["location"],
                checkpoints[i+1]["location"]
            )
            total_distance += distance
        
        # Convert from meters to kilometers
        return round(total_distance / 1000, 2)
    
    @staticmethod
    async def get_checkpoint_status(train_id: str) -> Dict[str, Any]:
        """
        Get a train's current checkpoint status
        
        Args:
            train_id: Train identifier
            
        Returns:
            Dict: Checkpoint status information
        """
        train = await TrainModel.get_by_train_id(train_id)
        if not train or not train.get("active_route_id"):
            return {
                "train_id": train_id,
                "has_route": False,
                "message": "No active route assigned"
            }
        
        # Get the route
        route = await RouteModel.get_by_route_id(train["active_route_id"])
        if not route or not route.get("checkpoints") or len(route.get("checkpoints", [])) == 0:
            return {
                "train_id": train_id,
                "has_route": True,
                "route_id": train["active_route_id"],
                "message": "Route has no checkpoints defined"
            }
        
        # Get latest train position
        latest_log = await LogModel.get_latest_by_train(train_id)
        if not latest_log or not latest_log.get("location"):
            return {
                "train_id": train_id,
                "has_route": True,
                "route_id": train["active_route_id"],
                "message": "No location data available"
            }
        
        # Calculate distances to all checkpoints
        checkpoints = route["checkpoints"]
        current_location = latest_log["location"]
        
        checkpoint_distances = []
        for i, checkpoint in enumerate(checkpoints):
            if not checkpoint.get("location"):
                continue
                
            distance = calculate_distance(current_location, checkpoint["location"])
            checkpoint_info = {
                "index": i,
                "name": checkpoint.get("name", f"Checkpoint {i+1}"),
                "distance": distance,  # meters
                "interval": checkpoint.get("interval"),  # seconds
                "location": checkpoint["location"]
            }
            checkpoint_distances.append(checkpoint_info)
        
        # Sort by distance
        checkpoint_distances.sort(key=lambda x: x["distance"])
        
        # Find the next checkpoint by schedule (the first one with interval > current time)
        start_time = route.get("start_time")
        next_scheduled = None
        
        if start_time:
            # Calculate the route's elapsed time in seconds
            current_time = get_current_utc_time()  # Changed from IST to UTC
            elapsed_seconds = (current_time - start_time).total_seconds()
            
            # Find the next checkpoint by schedule
            for checkpoint in sorted(checkpoints, key=lambda x: x.get("interval", 0)):
                if checkpoint.get("interval", 0) > elapsed_seconds:
                    distance = None
                    for cd in checkpoint_distances:
                        if cd["index"] == checkpoints.index(checkpoint):
                            distance = cd["distance"]
                            break
                            
                    next_scheduled = {
                        "name": checkpoint.get("name", f"Checkpoint {checkpoints.index(checkpoint)+1}"),
                        "interval": checkpoint.get("interval"),  # seconds
                        "time_remaining": checkpoint.get("interval") - elapsed_seconds,  # seconds
                        "location": checkpoint.get("location"),
                        "distance": distance  # meters
                    }
                    break
        
        return {
            "train_id": train_id,
            "has_route": True,
            "route_id": train["active_route_id"],
            "route_name": route.get("route_name"),
            "current_location": current_location,
            "nearest_checkpoint": checkpoint_distances[0] if checkpoint_distances else None,
            "next_scheduled_checkpoint": next_scheduled,
            "all_checkpoints": checkpoint_distances,
            "timestamp": latest_log.get("timestamp"),
            "formatted_timestamp": format_timestamp_ist(latest_log.get("timestamp"))
        }
    
    @staticmethod
    async def find_routes_by_checkpoint(location: List[float], radius_meters: float = 100) -> List[Dict[str, Any]]:
        """
        Find routes that have checkpoints near the specified location
        
        Args:
            location: [longitude, latitude] coordinates
            radius_meters: Search radius in meters
            
        Returns:
            List[Dict]: Routes with matching checkpoints
        """
        all_routes = await RouteModel.get_all()
        matching_routes = []
        
        for route in all_routes:
            if not route.get("checkpoints"):
                continue
                
            for checkpoint in route["checkpoints"]:
                checkpoint_location = checkpoint.get("location")
                if not checkpoint_location:
                    continue
                    
                distance = calculate_distance(location, checkpoint_location)
                if distance <= radius_meters:
                    route = {
                        "route_id": route["route_id"],
                        "route_name": route.get("route_name"),
                        "checkpoint_name": checkpoint.get("name", "Unnamed checkpoint"),
                        "distance": round(distance, 2)
                    }
                    matching_routes.append(route)
                    break  # Only add each route once
        
        return matching_routes