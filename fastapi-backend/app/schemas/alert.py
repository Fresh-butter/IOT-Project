"""
Alert schema module.
Defines Pydantic models for alert data validation and serialization.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator
from datetime import datetime
from bson import ObjectId
from app.database import PyObjectId
from app.utils import format_timestamp_ist, normalize_timestamp

class AlertBase(BaseModel):
    sender_ref: str = Field(..., description="Reference to the sender")
    recipient_ref: str = Field(..., description="Reference to the recipient")
    message: str = Field(..., description="Alert message content")
    location: List[float] = Field(..., description="Geographic coordinates [longitude, latitude]")
    timestamp: datetime = Field(..., description="Time when the alert was created")

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: format_timestamp_ist(dt)
        }

    @validator("timestamp", pre=True)
    def validate_timestamp(cls, value):
        """Validates timestamp and normalizes to UTC for storage"""
        return normalize_timestamp(value)

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    message: Optional[str] = None
    location: Optional[List[float]] = None

    class Config:
        populate_by_name = True

class AlertInDB(AlertBase):
    id: PyObjectId = Field(alias="_id")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: format_timestamp_ist(dt)
        }

class AlertResponse(AlertBase):
    id: str
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: format_timestamp_ist(dt)
        }

class AlertSummary(BaseModel):
    total_alerts: int
    collision_alerts: int
    deviation_alerts: int
    schedule_alerts: int
    system_alerts: int
    train_to_train_alerts: int
    other_alerts: int
    by_severity: dict
    by_recipient: dict
    recent_critical: List[dict] = []
    timestamp: datetime
    period_hours: int
    
    class Config:
        json_encoders = {
            datetime: lambda dt: format_timestamp_ist(dt)
        }
