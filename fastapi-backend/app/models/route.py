"""
Route model module.
Defines the structure and operations for route data in MongoDB.
"""
from bson import ObjectId
from app.database import get_collection
from app.utils import round_coordinates, normalize_timestamp
from typing import List, Optional, Dict, Any

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
        
        # Ensure start_time is normalized to UTC if present
        if "start_time" in route_data and route_data["start_time"]:
            route_data["start_time"] = normalize_timestamp(route_data["start_time"])
        
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

        # Ensure start_time is normalized to UTC if being updated
        if "start_time" in update_data and update_data["start_time"]:
            update_data["start_time"] = normalize_timestamp(update_data["start_time"])

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
    async def get_all(limit: int = 1000, skip: int = 0):
        """
        Fetch all routes with optional pagination
        
        Args:
            limit: Maximum number of routes to fetch
            skip: Number of routes to skip
            
        Returns:
            list: List of route documents
        """
        results = await get_collection(RouteModel.collection).find({}).skip(skip).limit(limit).to_list(limit)
        return results

    @staticmethod
    async def find_routes_with_rfid_tag(rfid_tag: str):
        """
        Find routes that contain a specific RFID tag in one of their checkpoints
        
        Args:
            rfid_tag: RFID tag identifier
            
        Returns:
            list: List of route documents containing the specified RFID tag
        """
        pipeline = [
            {
                "$match": {
                    "checkpoints": {
                        "$elemMatch": {
                            "rfid_tag": rfid_tag
                        }
                    }
                }
            }
        ]
        
        routes = await get_collection(RouteModel.collection).aggregate(pipeline).to_list(1000)
        return routes

    @staticmethod
    async def assign_train(route_id: str, train_id: str, train_ref: str):
        """
        Assign a train to a route
        
        Args:
            route_id: Route identifier (like "R301")
            train_id: Train identifier
            train_ref: MongoDB ObjectId of the train document
            
        Returns:
            bool: True if train was assigned successfully, False otherwise
        """
        result = await get_collection(RouteModel.collection).update_one(
            {"route_id": route_id},  # Query by route_id field, not _id
            {
                "$set": {
                    "assigned_train_id": train_id,
                    "assigned_train_ref": ObjectId(train_ref)
                }
            }
        )
        return result.modified_count > 0
