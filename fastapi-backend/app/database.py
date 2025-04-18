"""
Database connection module.
Handles connection to MongoDB Atlas and provides database access functions.
"""
import logging
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Callable, Awaitable
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
from pymongo import IndexModel, ASCENDING, DESCENDING
from fastapi import HTTPException
from app.config import MONGODB_URL, DB_NAME

# Type variable for return types
T = TypeVar('T', bound=Dict[str, Any])

# Global client and database objects
client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None

async def connect_to_mongodb() -> None:
    """
    Connect to MongoDB Atlas and initialize the database client.
    
    Raises:
        ConnectionError: If connection to MongoDB fails
    """
    global client, db
    try:
        # Configure client with a reasonable timeout
        client = AsyncIOMotorClient(
            MONGODB_URL, 
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=10,
            retryWrites=True
        )
        
        # Check connection by issuing a command
        await client.admin.command('ping')
        
        # Set the database
        db = client[DB_NAME]
        
        logging.info(f"Connected to MongoDB Atlas - Database: {DB_NAME}")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logging.error(f"MongoDB connection error: {str(e)}")
        raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

async def close_mongodb_connection() -> None:
    """Close MongoDB connection when the application shuts down."""
    global client
    if client:
        client.close()
        logging.info("Closed MongoDB connection")

def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    """
    Get a collection from the database.
    
    Args:
        collection_name: Name of the MongoDB collection
        
    Returns:
        AsyncIOMotorCollection: MongoDB collection object
        
    Raises:
        ValueError: If database connection hasn't been initialized
    """
    if db is None:
        raise ValueError("Database connection not initialized. Call connect_to_mongodb first.")
    return db[collection_name]

async def create_indexes() -> None:
    """
    Create indexes for collections to optimize query performance.
    This should be called during application startup.
    """
    try:
        # Trains collection indexes
        trains_indexes = [
            IndexModel([("train_id", ASCENDING)], unique=True),
            IndexModel([("current_status", ASCENDING)]),
        ]
        await db.trains.create_indexes(trains_indexes)
        
        # Routes collection indexes
        routes_indexes = [
            IndexModel([("route_id", ASCENDING)], unique=True),
            IndexModel([("assigned_train_id", ASCENDING)]),
            IndexModel([("start_time", ASCENDING)]),
        ]
        await db.routes.create_indexes(routes_indexes)
        
        # Logs collection indexes
        logs_indexes = [
            IndexModel([("train_id", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),  # For sorting by newest first
            IndexModel([("train_id", ASCENDING), ("timestamp", DESCENDING)]),  # For queries by train with time sorting
            IndexModel([("rfid_tag", ASCENDING)]),  # For looking up logs by RFID tag
            IndexModel([("is_test", ASCENDING)]),  # For filtering test data
        ]
        await db.logs.create_indexes(logs_indexes)
        
        # Alerts collection indexes
        alerts_indexes = [
            IndexModel([("recipient_id", ASCENDING)]),
            IndexModel([("sender_id", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),
        ]
        await db.alerts.create_indexes(alerts_indexes)
        
        logging.info("MongoDB indexes created successfully")
    except PyMongoError as e:
        logging.error(f"Error creating MongoDB indexes: {str(e)}")
        # Don't raise exception here, as the application can still function without indexes

async def get_db_stats() -> Dict[str, Any]:
    """
    Get database statistics for monitoring purposes.
    
    Returns:
        Dict: Database statistics including collection counts
    """
    if db is None:
        raise ValueError("Database connection not initialized")
    
    try:
        # Get basic database stats
        db_stats = await db.command("dbStats")
        
        # Get document counts for each collection
        collections = ["trains", "routes", "logs", "alerts"]
        collection_stats = {}
        
        for collection_name in collections:
            collection = get_collection(collection_name)
            count = await collection.count_documents({})
            collection_stats[collection_name] = count
        
        return {
            "database": DB_NAME,
            "collections": collection_stats,
            "storage_size_mb": round(db_stats.get("storageSize", 0) / (1024 * 1024), 2),
            "data_size_mb": round(db_stats.get("dataSize", 0) / (1024 * 1024), 2),
        }
    except PyMongoError as e:
        logging.error(f"Error getting database stats: {str(e)}")
        return {"error": str(e)}

class PyObjectId(str):
    """
    Custom ID class to handle ObjectId serialization/deserialization.
    This allows using string IDs in API requests/responses while storing as ObjectId in MongoDB.
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if v is None:
            return None
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId format")
        return str(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        # Add this method for OpenAPI documentation
        field_schema.update(type="string", format="object-id", example="5f50eb588287d07746b6f8d4")

async def safe_db_operation(operation: Callable[[], Awaitable[Any]], error_message: str) -> Any:
    """
    Execute a database operation safely with error handling
    
    Args:
        operation: The database operation function to execute (as a lambda or callable)
        error_message: Error message to display if operation fails
        
    Returns:
        The result of the database operation
    """
    try:
        return await operation()
    except Exception as e:
        # Optionally log the error
        logging.error(f"Database operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")