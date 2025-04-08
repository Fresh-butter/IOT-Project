"""
Route model module.
Defines the structure and operations for route data in MongoDB.
"""
from typing import List, Optional
from bson import ObjectId
from app.database import get_collection

class RouteModel:
    collection = "routes"
    
    @staticmethod
    async def get_all():
        """Get all routes"""
        routes = await get_collection(RouteModel.collection).find().to_list(1000)
        return routes
    
    @staticmethod
    async def get_by_id(id: str):
        """Get route by ID"""
        return await get_collection(RouteModel.collection).find_one({"_id": ObjectId(id)})
    
    @staticmethod
    async def get_by_train_id(train_id: str):
        """Get route by train ID"""
        return await get_collection(RouteModel.collection).find_one({"assigned_train_id": train_id})
    
    @staticmethod
    async def create(route_data: dict):
        """Create a new route"""
        result = await get_collection(RouteModel.collection).insert_one(route_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def update(id: str, route_data: dict):
        """Update a route"""
        result = await get_collection(RouteModel.collection).update_one(
            {"_id": ObjectId(id)}, {"$set": route_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(id: str):
        """Delete a route"""
        result = await get_collection(RouteModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
