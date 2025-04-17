"""
Log schema module.
Defines Pydantic models for log data validation and serialization.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import re
from enum import Enum

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v and not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v) if v else None

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string", format="object-id", nullable=True)

class AccuracyCategory(str, Enum):
    """GPS accuracy categories based on HDOP and satellite count"""
    EXCELLENT = "excellent"  # < 5 meter error
    GOOD = "good"           # 5-10 meter error
    MODERATE = "moderate"   # 10-25 meter error
    POOR = "poor"           # > 25 meter error
    INVALID = "invalid"     # No GPS fix

class LogBase(BaseModel):
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
        example=[76.8512, 28.7041]
    )
    timestamp: datetime = Field(
        ..., 
        description="Timestamp of the log entry (in IST timezone)",
        example="2025-04-10T14:23:05+05:30"
    )
    accuracy: Optional[str] = Field(
        None, 
        description="GPS accuracy category based on HDOP and satellite count",
        example="good"
    )
    is_test: bool = Field(
        ..., 
        description="Flag indicating whether this is a test record",
        example=False
    )

    @validator("timestamp", pre=True)
    def normalize_timestamp(cls, value):
        if isinstance(value, str):
            # Normalize timezone offset format (+05:30 → +0530)
            value = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", value)

            # Try parsing with different formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f%z",  # With milliseconds and timezone
                "%Y-%m-%dT%H:%M:%S%z",     # Without milliseconds, with timezone
                "%Y-%m-%dT%H:%M:%S",       # Without timezone (default to IST)
            ]
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(value, fmt)
                    # Add IST timezone if missing
                    if not parsed.tzinfo:
                        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
                    return parsed
                except ValueError:
                    continue

            raise ValueError(f"Invalid datetime format: {value}")

        elif isinstance(value, datetime):
            # Handle datetime objects directly
            if not value.tzinfo:
                value = value.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            return value

        raise ValueError("Timestamp must be a string or datetime object")

    @validator('location')
    def validate_location(cls, v):
        """Validates and rounds location coordinates to 6 decimal places"""
        if v is None:
            return v
        if len(v) != 2:
            raise ValueError("Location must contain exactly 2 coordinates")
        return [round(coord, 6) for coord in v]

    class Config:
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "train_id": "101",
                "train_ref": "67e80645e4a58df990138c2b",
                "timestamp": "2025-04-10T14:23:05+05:30",
                "rfid_tag": "RFID_101_B2",
                "location": [76.8512, 28.7041],
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
        example=[76.8512, 28.7041]
    )
    timestamp: Optional[datetime] = Field(
        None, 
        description="Timestamp of the log entry (in IST timezone)",
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
                "location": [76.8512, 28.7041],
                "accuracy": "good",
                "is_test": False
            }
        }

class LogInDB(LogBase):
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "_id": "67e80645e4a58df990138c2b",
                "train_id": "101",
                "train_ref": "67e80645e4a58df990138c2b",
                "timestamp": "2025-04-10T14:23:05+05:30",
                "rfid_tag": "RFID_101_B2",
                "location": [76.8512, 28.7041],
                "accuracy": "good",
                "is_test": False
            }
        }
