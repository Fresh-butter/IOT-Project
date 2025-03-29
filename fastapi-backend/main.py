from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ✅ Add CORS Middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change this later for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


# Connect to MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["train_system"]  # Database name

@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}



@app.get("/databases")
async def list_databases():
    try:
        databases = await client.list_database_names()
        return {"success": True, "databases": databases}
    except Exception as e:
        return {"success": False, "error": str(e)}
