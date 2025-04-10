"""
Route model module.
Defines the structure and operations for route data in MongoDB.
"""
from bson import ObjectId
from app.database import get_collection

class RouteModel:
    collection = "routes"

    @staticmethod
    def _convert_refs(route_data: dict):
        if "assigned_train_ref" in route_data and route_data["assigned_train_ref"]:
            route_data["assigned_train_ref"] = ObjectId(route_data["assigned_train_ref"])
        return route_data

    @staticmethod
    async def create(route_data: dict):
        processed_data = RouteModel._convert_refs(route_data)
        result = await get_collection(RouteModel.collection).insert_one(processed_data)
        return str(result.inserted_id)

    @staticmethod
    async def update(id: str, update_data: dict):
        processed_data = RouteModel._convert_refs(update_data)
        result = await get_collection(RouteModel.collection).update_one(
            {"_id": ObjectId(id)},
            {"$set": processed_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def get_by_id(id: str):
        return await get_collection(RouteModel.collection).find_one({"_id": ObjectId(id)})

    @staticmethod
    async def delete(id: str):
        result = await get_collection(RouteModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_all():
        return await get_collection(RouteModel.collection).find().to_list(1000)
