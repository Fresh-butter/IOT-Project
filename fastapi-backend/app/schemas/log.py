"""
Log schema module.
Defines Pydantic models for log data validation and serialization.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId
from enum import Enum
from app.database import PyObjectId
from app.utils import normalize_timestamp, round_coordinates, format_timestamp_ist

class AccuracyCategory(str, Enum):
    """GPS accuracy categories based on HDOP and satellite count"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    FAIR = "fair"
    POOR = "poor"

class LogBase(BaseModel):
    """
    Base model for log entries with common attributes
    """
    train_id: str = Field(
        ..., 
        description="Unique identifier for the train",
        example="101"
    )
    train_ref: PyObjectId = Field(
        ..., 
        description="MongoDB ObjectId reference to the train document",
        example="67e80645e4a58df990138c2b"
    )
    rfid_tag: Optional[str] = Field(
        None, 
        description="RFID tag identifier if detected, null otherwise",
        example="RFID_101_B2"
    )
    location: Optional[List[float]] = Field(
        None, 
        min_items=2, 
        max_items=2, 
        description="GPS coordinates as [longitude, latitude]",
        example=[76.85125, 28.70412]
    )
    timestamp: datetime = Field(
        ..., 
        description="Timestamp of the log entry (stored as UTC, returned as IST)",
        example="2025-04-10T14:23:05+05:30"
    )
    accuracy: Optional[str] = Field(
        None, 
        description="GPS accuracy category based on HDOP and satellite count",
        example="good"
    )
    is_test: bool = Field(
        False, 
        description="Flag indicating whether this is a test record",
        example=False
    )

    @validator("timestamp", pre=True)
    def validate_timestamp(cls, value):
        """Validates timestamp and normalizes to UTC for storage"""
        if isinstance(value, str):
            try:
                # Parse with timezone awareness
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return normalize_timestamp(dt)
            except ValueError:
                # For older formats or unparseable strings
                pass
        
        # If already a datetime or needs default handling
        return normalize_timestamp(value)

    @validator('location')
    def validate_location(cls, v):
        """Validates and rounds location coordinates to 5 decimal places"""
        if v is None:
            return v
        return round_coordinates(v)

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: format_timestamp_ist(dt)
        }
        schema_extra = {
            "example": {
                "train_id": "101",
                "train_ref": "67e80645e4a58df990138c2b",
                "timestamp": "2025-04-10T14:23:05+05:30",
                "rfid_tag": "RFID_101_B2",
                "location": [76.85125, 28.70412],
                "accuracy": "good",
                "is_test": False
            }
        }

class LogCreate(LogBase):
    pass

class LogUpdate(BaseModel):
    train_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the train",
        example="101"
    )
    train_ref: Optional[PyObjectId] = Field(
        None, 
        description="MongoDB ObjectId reference to the train document",
        example="67e80645e4a58df990138c2b"
    )
    rfid_tag: Optional[str] = Field(
        None, 
        description="RFID tag identifier if detected, null otherwise",
        example="RFID_101_B2"
    )
    location: Optional[List[float]] = Field(
        None, 
        min_items=2, 
        max_items=2, 
        description="GPS coordinates as [longitude, latitude]",
        example=[76.85125, 28.70412]
    )
    timestamp: Optional[datetime] = Field(
        None, 
        description="Timestamp of the log entry (stored as UTC, returned as IST)",
        example="2025-04-10T14:23:05+05:30"
    )
    accuracy: Optional[str] = Field(
        None, 
        description="GPS accuracy category based on HDOP and satellite count",
        example="good"
    )
    is_test: Optional[bool] = Field(
        None, 
        description="Flag indicating whether this is a test record",
        example=False
    )

    class Config:
        schema_extra = {
            "example": {
                "location": [76.85125, 28.70412],
                "accuracy": "good",
                "is_test": False
            }
        }

class LogInDB(LogBase):
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: format_timestamp_ist(dt)
        }
        schema_extra = {
            "example": {
                "_id": "67e80645e4a58df990138c2b",
                "train_id": "101",
                "train_ref": "67e80645e4a58df990138c2b",
                "timestamp": "2025-04-10T14:23:05+05:30",
                "rfid_tag": "RFID_101_B2",
                "location": [76.85125, 28.70412],
                "accuracy": "good",
                "is_test": False
            }
        }
