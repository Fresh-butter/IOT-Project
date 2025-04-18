"""
Train model module.
Defines the structure and operations for train data in MongoDB.
"""
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.database import get_collection
from app.config import TRAIN_STATUS

class TrainModel:
    collection = "trains"

    @staticmethod
    async def create(train_data: dict):
        """
        Create a new train in the database
        
        Args:
            train_data: Dictionary containing train details
            
        Returns:
            str: ID of the newly created train document
        """
        # Check for duplicate train_id before creating
        if "train_id" in train_data:
            existing = await get_collection(TrainModel.collection).find_one(
                {"train_id": train_data["train_id"]}
            )
            
            if existing:
                raise ValueError(f"Train with ID '{train_data['train_id']}' already exists")
        
        # Convert route_ref string to ObjectId for MongoDB storage if it's not null
        if train_data.get("current_route_ref"):
            train_data["current_route_ref"] = ObjectId(train_data["current_route_ref"])
            
        result = await get_collection(TrainModel.collection).insert_one(train_data)
        return str(result.inserted_id)

    @staticmethod
    async def update(id: str, update_data: dict):
        """
        Update an existing train
        
        Args:
            id: Train document ID
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Check if updating train_id and if it would create a duplicate
        if "train_id" in update_data:
            existing = await get_collection(TrainModel.collection).find_one({
                "train_id": update_data["train_id"],
                "_id": {"$ne": ObjectId(id)}
            })
            
            if existing:
                raise ValueError(f"Train with ID '{update_data['train_id']}' already exists")
        
        # Handle ObjectId conversion for updates if route_ref is present
        if "current_route_ref" in update_data:
            if update_data["current_route_ref"]:
                update_data["current_route_ref"] = ObjectId(update_data["current_route_ref"])
            else:
                update_data["current_route_ref"] = None

        result = await get_collection(TrainModel.collection).update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_by_id(id: str):
        """
        Fetch a train by MongoDB ID
        
        Args:
            id: Train document ID
            
        Returns:
            dict: Train document or None if not found
        """
        return await get_collection(TrainModel.collection).find_one({"_id": ObjectId(id)})
        
    @staticmethod
    async def get_by_train_id(train_id: str):
        """
        Fetch a train by train_id field
        
        Args:
            train_id: Train identifier
            
        Returns:
            dict: Train document or None if not found
        """
        return await get_collection(TrainModel.collection).find_one({"train_id": train_id})

    @staticmethod
    async def delete(id: str):
        """
        Delete a train by ID
        
        Args:
            id: Train document ID
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        result = await get_collection(TrainModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_all(status: str = None):
        """
        Fetch all trains with optional status filtering
        
        Args:
            status: Optional status to filter trains by
            
        Returns:
            list: List of train documents
        """
        filter_query = {}
        if status:
            filter_query["current_status"] = status
            
        trains = await get_collection(TrainModel.collection).find(filter_query).to_list(1000)
        return trains
        
    @staticmethod
    async def get_active_trains():
        """
        Fetch all trains that are currently in service and running
        
        Returns:
            list: List of active train documents
        """
        trains = await get_collection(TrainModel.collection).find(
            {"current_status": TRAIN_STATUS["IN_SERVICE_RUNNING"]}
        ).to_list(1000)
        return trains
        
    @staticmethod
    async def update_status(id: str, status: str):
        """
        Update a train's status
        
        Args:
            id: Train document ID
            status: New status (must be a valid status from TRAIN_STATUS)
            
        Returns:
            bool: True if status was updated successfully, False otherwise
        """
        if status not in TRAIN_STATUS.values():
            raise ValueError(f"Invalid train status: {status}")
            
        result = await get_collection(TrainModel.collection).update_one(
            {"_id": ObjectId(id)},
            {"$set": {"current_status": status}}
        )
        return result.modified_count > 0
        
    @staticmethod
    async def assign_route(train_id: str, route_id: str, route_ref: str):
        """
        Assign a route to a train
        
        Args:
            train_id: Train document ID
            route_id: Route identifier
            route_ref: MongoDB ObjectId of the route document
            
        Returns:
            bool: True if route was assigned successfully, False otherwise
        """
        result = await get_collection(TrainModel.collection).update_one(
            {"_id": ObjectId(train_id)},
            {"$set": {
                "current_route_id": route_id,
                "current_route_ref": ObjectId(route_ref)
            }}
        )
        return result.modified_count > 0
