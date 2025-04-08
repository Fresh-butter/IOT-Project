"""
Train model module.
Defines the structure and operations for train data in MongoDB.
"""
from typing import List, Optional
from bson import ObjectId
from app.database import get_collection

class TrainModel:
    collection = "trains"
    
    @staticmethod
    async def get_all():
        """Get all trains"""
        trains = await get_collection(TrainModel.collection).find().to_list(1000)
        return trains
    
    @staticmethod
    async def get_by_id(id: str):
        """Get train by ID"""
        return await get_collection(TrainModel.collection).find_one({"_id": ObjectId(id)})
    
    @staticmethod
    async def create(train_data: dict):
        """Create a new train"""
        result = await get_collection(TrainModel.collection).insert_one(train_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def update(id: str, train_data: dict):
        """Update a train"""
        result = await get_collection(TrainModel.collection).update_one(
            {"_id": ObjectId(id)}, {"$set": train_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(id: str):
        """Delete a train"""
        result = await get_collection(TrainModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
