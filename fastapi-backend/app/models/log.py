"""
Log model module.
Defines the structure and operations for log data in MongoDB.
"""
from bson import ObjectId
from app.database import get_collection

class LogModel:
    collection = "logs"

    @staticmethod
    async def create(log_data: dict):
        log_data["train_ref"] = ObjectId(log_data["train_ref"])
        result = await get_collection(LogModel.collection).insert_one(log_data)
        return str(result.inserted_id)

    @staticmethod
    async def update(id: str, update_data: dict):
        if "train_ref" in update_data and update_data["train_ref"]:
            update_data["train_ref"] = ObjectId(update_data["train_ref"])
        
        result = await get_collection(LogModel.collection).update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_by_id(id: str):
        return await get_collection(LogModel.collection).find_one({"_id": ObjectId(id)})

    @staticmethod
    async def delete(id: str):
        result = await get_collection(LogModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_all():
        return await get_collection(LogModel.collection).find().to_list(1000)
