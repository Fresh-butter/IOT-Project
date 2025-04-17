"""
Route schema module.
Defines Pydantic models for route data validation and serialization.
"""
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from bson import ObjectId
from app.database import PyObjectId
from app.utils import normalize_timestamp, round_coordinates

class Checkpoint(BaseModel):
    """
    Represents a checkpoint in a train route
    """
    interval: int = Field(
        ..., 
        ge=0, 
        description="Time interval in seconds from the start of the route",
        example=0
    )
    rfid_tag: Optional[str] = Field(
        None, 
        description="RFID tag identifier expected at this checkpoint",
        example="RFID_101_A1"
    )
    location: List[float] = Field(
        ..., 
        min_items=2, 
        max_items=2, 
        description="GPS coordinates as [longitude, latitude]",
        example=[77.209, 28.6139]
    )

    @validator('location')
    def validate_location(cls, v):
        """Validates and rounds location coordinates to 5 decimal places"""
        return round_coordinates(v)  # Use the utility function

    class Config:
        schema_extra = {
            "example": {
                "interval": 0,
                "rfid_tag": "RFID_101_A1", 
                "location": [77.209, 28.6139]
            }
        }

class RouteBase(BaseModel):
    """
    Base model for train routes with common attributes
    """
    route_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the route",
        example="R101"
    )
    route_name: Optional[str] = Field(
        None, 
        description="Descriptive name of the route",
        example="Delhi to Mumbai"
    )
    start_time: Optional[datetime] = Field(
        None, 
        description="Scheduled start time (in IST) for the route",
        example="2025-03-29T19:30:00+05:30"
    )
    assigned_train_id: Optional[str] = Field(
        None, 
        description="ID of the train assigned to this route",
        example="101"
    )
    assigned_train_ref: Optional[PyObjectId] = Field(
        None,
        description="MongoDB ObjectId reference to the train document",
        example="67e80645e4a58df990138c2b"
    )
    checkpoints: Optional[List[Checkpoint]] = Field(
        None, 
        description="List of checkpoints along the route"
    )

    @validator('checkpoints')
    def validate_checkpoints(cls, v):
        """Validates that the first checkpoint has interval 0"""
        if v and v[0].interval != 0:
            raise ValueError("First checkpoint must have interval 0")
        return v

    @validator("start_time", pre=True)
    def validate_start_time(cls, value):
        """Validates and normalizes start_time to IST timezone"""
        if value is None:
            return None
        return normalize_timestamp(value)

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "route_id": "R101",
                "route_name": "Delhi to Mumbai",
                "start_time": "2025-03-29T19:30:00+05:30",
                "assigned_train_id": "101",
                "assigned_train_ref": "67e80645e4a58df990138c2b",
                "checkpoints": [
                    {
                        "interval": 0,
                        "rfid_tag": "RFID_101_A1",
                        "location": [77.209, 28.6139]
                    },
                    {
                        "interval": 3600,
                        "rfid_tag": None,
                        "location": [77.1025, 28.7041]
                    },
                    {
                        "interval": 7200,
                        "rfid_tag": "RFID_101_B2",
                        "location": [76.8512, 28.7041]
                    }
                ]
            }
        }

class RouteCreate(RouteBase):
    """
    Model for creating a new route
    """
    route_id: str = Field(
        ..., 
        description="Unique identifier for the route",
        example="R101"
    )
    route_name: str = Field(
        ..., 
        description="Descriptive name of the route",
        example="Delhi to Mumbai"
    )
    checkpoints: List[Checkpoint] = Field(
        ..., 
        min_items=1, 
        description="List of checkpoints along the route"
    )

class RouteUpdate(RouteBase):
    """
    Model for updating an existing route
    """
    pass

class RouteInDB(RouteBase):
    """
    Model for route data retrieved from database
    """
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
