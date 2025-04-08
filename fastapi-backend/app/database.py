
"""
Database connection module.
Handles connection to MongoDB Atlas and provides database access functions.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URL, DB_NAME

client = None
db = None

async def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    print("Connected to MongoDB Atlas")

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")

def get_collection(collection_name):
    """Get a collection from the database"""
    return db[collection_name]
