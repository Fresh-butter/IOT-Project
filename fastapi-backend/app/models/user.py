"""
User model module.
Defines the structure and operations for user data in MongoDB.
"""
from typing import Optional
from bson import ObjectId
from app.database import get_collection
from app.utils import get_password_hash, verify_password

class UserModel:
    collection = "users"
    
    @staticmethod
    async def get_all():
        """Get all users"""
        users = await get_collection(UserModel.collection).find().to_list(1000)
        return users
    
    @staticmethod
    async def get_by_id(id: str):
        """Get user by ID"""
        return await get_collection(UserModel.collection).find_one({"_id": ObjectId(id)})
    
    @staticmethod
    async def get_by_username(username: str):
        """Get user by username"""
        return await get_collection(UserModel.collection).find_one({"username": username})
    
    @staticmethod
    async def create(user_data: dict):
        """Create a new user"""
        # Hash the password
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        result = await get_collection(UserModel.collection).insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def update(id: str, user_data: dict):
        """Update a user"""
        # If password is being updated, hash it
        if "password" in user_data:
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
            
        result = await get_collection(UserModel.collection).update_one(
            {"_id": ObjectId(id)}, {"$set": user_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete(id: str):
        """Delete a user"""
        result = await get_collection(UserModel.collection).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    @staticmethod
    async def authenticate(username: str, password: str):
        """Authenticate a user"""
        user = await UserModel.get_by_username(username)
        if not user:
            return False
        if not verify_password(password, user["hashed_password"]):
            return False
        return user
