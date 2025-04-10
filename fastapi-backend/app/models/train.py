from bson import ObjectId
from app.database import get_collection

class TrainModel:
    collection = "trains"

    @staticmethod
    async def create(train_data: dict):
        # Convert route_ref string to ObjectId for MongoDB storage if it's not null
        if train_data.get("current_route_ref"):
            train_data["current_route_ref"] = ObjectId(train_data["current_route_ref"])
        result = await get_collection(TrainModel.collection).insert_one(train_data)
        return str(result.inserted_id)

    @staticmethod
    async def update(id: str, update_data: dict):
        # Handle ObjectId conversion for updates if route_ref is present and not null
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
        """Fetch a train by ID"""
        return await get_collection(TrainModel.collection).find_one({"_id": ObjectId(id)})

    @staticmethod
    async def delete(id: str):
        """Delete a train by ID"""
        result = await get_collection(TrainModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_all():
        """Fetch all trains"""
        trains = await get_collection(TrainModel.collection).find().to_list(1000)
        return trains
