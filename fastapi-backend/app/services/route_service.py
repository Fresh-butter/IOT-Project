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
from app.core.collision import analyze_route_collision_risks
from app.config import get_current_ist_time

class RouteService:
    """Service for route-related operations"""
    
    @staticmethod
    async def get_route_with_related_data(route_id: str) -> Dict[str, Any]:
        """
        Get comprehensive route information including assigned train
        
        Args:
            route_id: Route identifier
            
        Returns:
            Dict: Route details with related information
        """
        # Get basic route info
        route = await RouteModel.get_by_route_id(route_id)
        if not route:
            return {"error": "Route not found"}
        
        # Convert MongoDB _id to string
        route["_id"] = str(route["_id"])
        
        # Get assigned train information if available
        train_info = None
        if route.get("assigned_train_id"):
            train = await TrainModel.get_by_train_id(route["assigned_train_id"])
            if train:
                train["_id"] = str(train["_id"])
                train_info = train
        
        # Calculate total distance of the route
        total_distance = 0
        if route.get("checkpoints") and len(route["checkpoints"]) > 1:
            from app.utils import calculate_distance
            checkpoints = route["checkpoints"]
            for i in range(len(checkpoints) - 1):
                if checkpoints[i].get("location") and checkpoints[i+1].get("location"):
                    segment_distance = calculate_distance(
                        checkpoints[i]["location"], 
                        checkpoints[i+1]["location"]
                    )
                    total_distance += segment_distance
        
        # Identify RFID-enabled checkpoints
        rfid_checkpoints = []
        if route.get("checkpoints"):
            for i, cp in enumerate(route["checkpoints"]):
                if cp.get("rfid_tag"):
                    rfid_checkpoints.append({
                        "index": i,
                        "name": cp.get("name"),
                        "rfid_tag": cp["rfid_tag"]
                    })
        
        # Check for potential collision risks on this route
        collision_risks = await analyze_route_collision_risks(route_id)
        
        # Combine all information
        result = {
            "route": route,
            "assigned_train": train_info,
            "total_distance_meters": round(total_distance, 2),
            "checkpoint_count": len(route.get("checkpoints", [])),
            "rfid_checkpoints": rfid_checkpoints,
            "collision_risks": collision_risks,
            "timestamp": get_current_ist_time()
        }
        
        return result
    
    @staticmethod
    async def create_route_with_checkpoints(route_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new route with checkpoints
        
        Args:
            route_data: Route information including checkpoints
            
        Returns:
            Dict: Result of the creation operation
        """
        # Ensure route has a unique route_id
        if "route_id" in route_data:
            existing = await RouteModel.get_by_route_id(route_data["route_id"])
            if existing:
                return {
                    "success": False,
                    "error": f"Route with ID {route_data['route_id']} already exists"
                }
        
        # Process and validate checkpoints
        if "checkpoints" in route_data and route_data["checkpoints"]:
            # Ensure checkpoints have required fields
            for i, checkpoint in enumerate(route_data["checkpoints"]):
                if "location" not in checkpoint:
                    return {
                        "success": False,
                        "error": f"Checkpoint at index {i} is missing location coordinates"
                    }
                
                # Set interval based on position if not provided
                if "interval" not in checkpoint:
                    # Default intervals: distance-based with 30km/h average speed
                    if i > 0:
                        from app.utils import calculate_distance
                        distance = calculate_distance(
                            route_data["checkpoints"][i-1]["location"],
                            checkpoint["location"]
                        )
                        # Convert distance to time (seconds) assuming 30km/h (8.33 m/s)
                        interval = route_data["checkpoints"][i-1].get("interval", 0) + (distance / 8.33)
                        checkpoint["interval"] = round(interval)
                    else:
                        # First checkpoint starts at 0 seconds
                        checkpoint["interval"] = 0
        else:
            return {
                "success": False,
                "error": "Route must have at least one checkpoint"
            }
        
        # Set start time if not provided
        if "start_time" not in route_data or route_data["start_time"] is None:
            route_data["start_time"] = get_current_ist_time()
        
        # Handle train assignment if specified
        if "assigned_train_id" in route_data and route_data["assigned_train_id"]:
            train = await TrainModel.get_by_train_id(route_data["assigned_train_id"])
            if not train:
                return {
                    "success": False,
                    "error": f"Train with ID {route_data['assigned_train_id']} not found"
                }
            route_data["assigned_train_ref"] = str(train["_id"])
        
        # Create the route
        try:
            route_id = await RouteModel.create(route_data)
            created_route = await RouteModel.get_by_id(route_id)
            
            # If a train was assigned, update the train as well
            if "assigned_train_id" in route_data and route_data["assigned_train_id"] and created_route:
                await TrainModel.assign_route(
                    str(train["_id"]),
                    created_route["route_id"],
                    route_id
                )
            
            return {
                "success": True,
                "route_id": created_route["route_id"],
                "id": route_id,
                "checkpoint_count": len(created_route.get("checkpoints", [])),
                "timestamp": get_current_ist_time()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create route: {str(e)}"
            }
    
    @staticmethod
    async def update_route_checkpoints(route_id: str, checkpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update the checkpoints of an existing route
        
        Args:
            route_id: Route identifier
            checkpoints: New list of checkpoints
            
        Returns:
            Dict: Result of the update operation
        """
        # Check if route exists
        route = await RouteModel.get_by_route_id(route_id)
        if not route:
            return {"success": False, "error": "Route not found"}
        
        # Process and validate checkpoints
        if not checkpoints:
            return {
                "success": False,
                "error": "Route must have at least one checkpoint"
            }
        
        # Ensure checkpoints have required fields
        for i, checkpoint in enumerate(checkpoints):
            if "location" not in checkpoint:
                return {
                    "success": False,
                    "error": f"Checkpoint at index {i} is missing location coordinates"
                }
            
            # Set interval based on position if not provided
            if "interval" not in checkpoint:
                # Default intervals: distance-based with 30km/h average speed
                if i > 0:
                    from app.utils import calculate_distance
                    distance = calculate_distance(
                        checkpoints[i-1]["location"],
                        checkpoint["location"]
                    )
                    # Convert distance to time (seconds) assuming 30km/h (8.33 m/s)
                    interval = checkpoints[i-1].get("interval", 0) + (distance / 8.33)
                    checkpoint["interval"] = round(interval)
                else:
                    # First checkpoint starts at 0 seconds
                    checkpoint["interval"] = 0
        
        # Update the route with new checkpoints
        updated = await RouteModel.update(str(route["_id"]), {"checkpoints": checkpoints})
        if not updated:
            return {"success": False, "error": "Failed to update route checkpoints"}
        
        return {
            "success": True,
            "route_id": route_id,
            "checkpoint_count": len(checkpoints),
            "timestamp": get_current_ist_time()
        }
    
    @staticmethod
    async def find_routes_by_checkpoint(location: List[float], radius_meters: float = 100) -> List[Dict[str, Any]]:
        """
        Find routes that have checkpoints near a specific location
        
        Args:
            location: Location coordinates [longitude, latitude]
            radius_meters: Search radius in meters
            
        Returns:
            List[Dict]: Routes with matching checkpoints
        """
        all_routes = await RouteModel.get_all()
        matching_routes = []
        
        for route in all_routes:
            if not route.get("checkpoints"):
                continue
                
            for i, checkpoint in enumerate(route["checkpoints"]):
                if not checkpoint.get("location"):
                    continue
                    
                # Calculate distance to checkpoint
                from app.utils import calculate_distance
                distance = calculate_distance(location, checkpoint["location"])
                
                if distance <= radius_meters:
                    route["_id"] = str(route["_id"])
                    route["matched_checkpoint"] = {
                        "index": i,
                        "name": checkpoint.get("name"),
                        "distance": round(distance, 2)
                    }
                    matching_routes.append(route)
                    break  # Only add each route once
        
        return matching_routes
    
    @staticmethod
    async def get_route_statistics() -> Dict[str, Any]:
        """
        Get statistics for all routes in the system
        
        Returns:
            Dict: Statistical information about routes
        """
        all_routes = await RouteModel.get_all()
        
        stats = {
            "total_routes": len(all_routes),
            "active_routes": 0,  # Routes with assigned trains
            "total_distance_meters": 0,
            "total_checkpoints": 0,
            "routes_with_rfid": 0,
            "longest_route": None,
            "shortest_route": None,
            "average_checkpoints_per_route": 0,
            "timestamp": get_current_ist_time()
        }
        
        if not all_routes:
            return stats
        
        # Calculate statistics
        longest_route_distance = 0
        shortest_route_distance = float('inf')
        longest_route_id = None
        shortest_route_id = None
        
        for route in all_routes:
            # Check if route is active (has an assigned train)
            if route.get("assigned_train_id"):
                stats["active_routes"] += 1
            
            # Count total checkpoints
            checkpoint_count = len(route.get("checkpoints", []))
            stats["total_checkpoints"] += checkpoint_count
            
            # Check for RFID tags
            has_rfid = False
            for cp in route.get("checkpoints", []):
                if cp.get("rfid_tag"):
                    has_rfid = True
                    break
            
            if has_rfid:
                stats["routes_with_rfid"] += 1
            
            # Calculate route distance
            if checkpoint_count > 1:
                from app.utils import calculate_distance
                route_distance = 0
                checkpoints = route["checkpoints"]
                
                for i in range(len(checkpoints) - 1):
                    if checkpoints[i].get("location") and checkpoints[i+1].get("location"):
                        segment_distance = calculate_distance(
                            checkpoints[i]["location"], 
                            checkpoints[i+1]["location"]
                        )
                        route_distance += segment_distance
                
                stats["total_distance_meters"] += route_distance
                
                # Check if this is the longest or shortest route
                if route_distance > longest_route_distance:
                    longest_route_distance = route_distance
                    longest_route_id = route["route_id"]
                
                if route_distance < shortest_route_distance:
                    shortest_route_distance = route_distance
                    shortest_route_id = route["route_id"]
        
        # Calculate averages
        if stats["total_routes"] > 0:
            stats["average_checkpoints_per_route"] = round(stats["total_checkpoints"] / stats["total_routes"], 2)
        
        # Add details about longest and shortest routes
        if longest_route_id:
            stats["longest_route"] = {
                "route_id": longest_route_id,
                "distance_meters": round(longest_route_distance, 2)
            }
        
        if shortest_route_id:
            stats["shortest_route"] = {
                "route_id": shortest_route_id,
                "distance_meters": round(shortest_route_distance, 2)
            }
        
        # Round total distance
        stats["total_distance_meters"] = round(stats["total_distance_meters"], 2)
        
        return stats