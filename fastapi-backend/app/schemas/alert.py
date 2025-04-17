"""
Alert schema module.
Defines Pydantic models for alert data validation and serialization.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from bson import ObjectId
from app.database import PyObjectId  # Use centralized PyObjectId implementation
from app.utils import normalize_timestamp, round_coordinates

class AlertBase(BaseModel):
    sender_id: PyObjectId = Field(
        ..., 
        description="ID of the train that generated the alert",
        example="67e80281e4a58df990138c24"
    )
    recipient_id: PyObjectId = Field(
        ..., 
        description="ID of the train that should receive the alert",
        example="67e802cee4a58df990138c26"
    )
    message: str = Field(
        ..., 
        description="Descriptive message about the alert",
        example="Train 202 stopped unexpectedly."
    )
    location: Optional[List[float]] = Field(
        None, 
        min_items=2, 
        max_items=2, 
        description="GPS coordinates [longitude, latitude]",
        example=[76.85125, 28.70412]
    )
    timestamp: datetime = Field(
        ..., 
        description="Time when the alert was generated (IST)",
        example="2025-04-10T14:23:05+05:30"
    )
    
    @validator('location')
    def validate_location(cls, v):
        """Validates and rounds location coordinates to 5 decimal places"""
        if v is None:
            return v
        return round_coordinates(v)  # Use the utility function

    @validator("timestamp", pre=True)
    def validate_timestamp(cls, value):
        """Validates and normalizes timestamp to IST timezone"""
        return normalize_timestamp(value)  # Use the utility function

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        schema_extra = {
            "example": {
                "sender_id": "67e80281e4a58df990138c24",
                "recipient_id": "67e802cee4a58df990138c26",
                "message": "Train 202 stopped unexpectedly.",
                "location": [76.85125, 28.70412],
                "timestamp": "2025-04-10T14:23:05+05:30"
            }
        }

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    sender_id: Optional[PyObjectId] = Field(
        None, 
        description="ID of the train that generated the alert",
        example="67e80281e4a58df990138c24"
    )
    recipient_id: Optional[PyObjectId] = Field(
        None, 
        description="ID of the train that should receive the alert",
        example="67e802cee4a58df990138c26"
    )
    message: Optional[str] = Field(
        None, 
        description="Descriptive message about the alert",
        example="Train 202 stopped unexpectedly."
    )
    location: Optional[List[float]] = Field(
        None, 
        min_items=2, 
        max_items=2, 
        description="GPS coordinates [longitude, latitude]",
        example=[76.85125, 28.70412]
    )
    timestamp: Optional[datetime] = Field(
        None, 
        description="Time when the alert was generated (IST)",
        example="2025-04-10T14:23:05+05:30"
    )

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class AlertInDB(AlertBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
