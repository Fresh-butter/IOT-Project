"""
Route model module.
Defines the structure and operations for route data in MongoDB.
"""
from bson import ObjectId
from app.database import get_collection
from app.utils import round_coordinates

class RouteModel:
    collection = "routes"

    @staticmethod
    async def create(route_data: dict):
        """
        Create a new route in the database
        
        Args:
            route_data: Dictionary containing route details
            
        Returns:
            str: ID of the newly created route document
        """
        # Check for duplicate route_id before creating
        if "route_id" in route_data:
            existing = await get_collection(RouteModel.collection).find_one(
                {"route_id": route_data["route_id"]}
            )
            
            if existing:
                raise ValueError(f"Route with ID '{route_data['route_id']}' already exists")
        
        # Convert ObjectId references
        if "assigned_train_ref" in route_data and route_data["assigned_train_ref"]:
            route_data["assigned_train_ref"] = ObjectId(route_data["assigned_train_ref"])
        
        # Round coordinates if location is present
        if "location" in route_data and route_data["location"]:
            route_data["location"] = round_coordinates(route_data["location"])
        
        # Round coordinates in all checkpoints
        if "checkpoints" in route_data and route_data["checkpoints"]:
            for checkpoint in route_data["checkpoints"]:
                if "location" in checkpoint and checkpoint["location"]:
                    checkpoint["location"] = round_coordinates(checkpoint["location"])
            
        result = await get_collection(RouteModel.collection).insert_one(route_data)
        return str(result.inserted_id)

    @staticmethod
    async def update(id: str, update_data: dict):
        """
        Update an existing route
        
        Args:
            id: Route document ID
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Check if updating route_id and if it would create a duplicate
        if "route_id" in update_data:
            existing = await get_collection(RouteModel.collection).find_one({
                "route_id": update_data["route_id"],
                "_id": {"$ne": ObjectId(id)}
            })
            
            if existing:
                raise ValueError(f"Route with ID '{update_data['route_id']}' already exists")
        
        # Handle ObjectId conversion for updates
        if "assigned_train_ref" in update_data:
            if update_data["assigned_train_ref"]:
                update_data["assigned_train_ref"] = ObjectId(update_data["assigned_train_ref"])
            else:
                update_data["assigned_train_ref"] = None

        # Round coordinates if location is present
        if "location" in update_data and update_data["location"]:
            update_data["location"] = round_coordinates(update_data["location"])

        # Round coordinates in all checkpoints
        if "checkpoints" in update_data and update_data["checkpoints"]:
            for checkpoint in update_data["checkpoints"]:
                if "location" in checkpoint and checkpoint["location"]:
                    checkpoint["location"] = round_coordinates(checkpoint["location"])

        result = await get_collection(RouteModel.collection).update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_by_id(id: str):
        """
        Fetch a route by MongoDB ID
        
        Args:
            id: Route document ID
            
        Returns:
            dict: Route document or None if not found
        """
        return await get_collection(RouteModel.collection).find_one({"_id": ObjectId(id)})
        
    @staticmethod
    async def get_by_route_id(route_id: str):
        """
        Fetch a route by route_id field
        
        Args:
            route_id: Route identifier
            
        Returns:
            dict: Route document or None if not found
        """
        return await get_collection(RouteModel.collection).find_one({"route_id": route_id})

    @staticmethod
    async def get_by_train_id(train_id: str):
        """
        Fetch a route by the assigned train ID
        
        Args:
            train_id: Train identifier
            
        Returns:
            dict: Route document or None if not found
        """
        return await get_collection(RouteModel.collection).find_one({"assigned_train_id": train_id})

    @staticmethod
    async def delete(id: str):
        """
        Delete a route by ID
        
        Args:
            id: Route document ID
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        result = await get_collection(RouteModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_all(limit: int = 1000, skip: int = 0, filter_param=None):
        """
        Fetch all routes with optional filtering, sorting, and pagination
        
        Args:
            limit: Maximum number of routes to fetch
            skip: Number of routes to skip
            filter_param: Optional filter parameter
            
        Returns:
            list: List of route documents
        """
        filter_query = {}
        if filter_param is not None:
            filter_query["field_name"] = filter_param
            
        results = await get_collection(RouteModel.collection).find(filter_query).sort(
            "timestamp", -1
        ).skip(skip).limit(limit).to_list(limit)
        return results
