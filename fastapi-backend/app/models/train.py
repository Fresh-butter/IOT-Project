"""
Train model module.
Defines the structure and operations for train data in MongoDB.
"""
from bson import ObjectId
from app.database import get_collection

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
