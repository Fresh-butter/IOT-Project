"""
Alert schema module.
Defines Pydantic models for alert data validation and serialization.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string", format="object-id")

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
        example=[76.8512, 28.7041]
    )
    timestamp: datetime = Field(
        ..., 
        description="Time when the alert was generated (IST)",
        example="2025-04-10T14:23:05+05:30"
    )
    
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
                "location": [76.8512, 28.7041],
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
        example=[76.8512, 28.7041]
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
