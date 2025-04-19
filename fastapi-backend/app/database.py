"""
Database module for MongoDB connections and operations.
"""
import logging
from typing import Dict, Any, Callable, Awaitable, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError
from bson import ObjectId
from datetime import datetime, timedelta
import traceback
from fastapi import HTTPException

from app.config import MONGODB_URL, DB_NAME, get_current_utc_time

logger = logging.getLogger("app.database")
mongo_client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None

class PyObjectId(str):
    """Custom ObjectId type for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

async def connect_to_mongodb():
    """Establish connection to MongoDB"""
    global mongo_client, db
    try:
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        db = mongo_client[DB_NAME]
        logger.info(f"Connected to MongoDB database: {DB_NAME}")
    except PyMongoError as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        raise

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()
        logger.info("MongoDB connection closed")

def get_collection(collection_name: str):
    """Get a reference to a MongoDB collection"""
    global db
    if db is None:
        raise RuntimeError("Database connection not established")
    return db[collection_name]

async def safe_db_operation(operation: Callable[[], Awaitable[Any]], error_message: str) -> Any:
    """Safely execute a database operation with proper error handling"""
    try:
        return await operation()
    except DuplicateKeyError:
        logger.error(f"{error_message}: Duplicate key error")
        raise HTTPException(status_code=400, detail="An item with this identifier already exists")
    except PyMongoError as e:
        logger.error(f"{error_message}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

async def create_indexes() -> None:
    """Create MongoDB indexes for performance optimization"""
    global db
    if db is None:
        logger.error("Database connection not established, cannot create indexes")
        return
        
    try:
        # Trains collection indexes
        train_indexes = [
            IndexModel([("train_id", ASCENDING)], unique=True),
            IndexModel([("current_status", ASCENDING)]),
        ]
        await db.trains.create_indexes(train_indexes)
        
        # Routes collection indexes
        route_indexes = [
            IndexModel([("route_id", ASCENDING)], unique=True),
            IndexModel([("train_id", ASCENDING)]),
        ]
        await db.routes.create_indexes(route_indexes)
        
        # Logs collection indexes
        logs_indexes = [
            IndexModel([("train_id", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)]),  # For quick access to latest logs
            IndexModel([("train_id", ASCENDING), ("timestamp", DESCENDING)]),  # For train's recent logs
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
    """Get database statistics for monitoring"""
    global db
    if db is None:
        return {"error": "Database connection not established"}
        
    try:
        # Get collection counts
        train_count = await db.trains.count_documents({})
        route_count = await db.routes.count_documents({})
        log_count = await db.logs.count_documents({})
        alert_count = await db.alerts.count_documents({})
        
        # Get recent logs count
        recent_time = get_current_utc_time() - timedelta(hours=24)
        recent_logs = await db.logs.count_documents({"timestamp": {"$gte": recent_time}})
        
        # Get active alert count
        recent_alerts = await db.alerts.count_documents({"timestamp": {"$gte": recent_time}})
        
        return {
            "database": DB_NAME,
            "collections": {
                "trains": train_count,
                "routes": route_count,
                "logs": log_count,
                "alerts": alert_count
            },
            "recent": {
                "logs_24h": recent_logs,
                "alerts_24h": recent_alerts
            },
            "timestamp": get_current_utc_time()
        }
    except Exception as e:
        logging.error(f"Error getting database stats: {str(e)}")
        return {"error": str(e)}

def is_connected() -> bool:
    """Check if database connection is established"""
    global db
    return db is not None