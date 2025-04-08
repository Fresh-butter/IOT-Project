"""
Alert schema module.
Defines Pydantic models for alert data validation and serialization.
"""
from typing import Optional
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

class AlertBase(BaseModel):
    sender_id: PyObjectId
    recipient_id: PyObjectId
    message: str
    timestamp: datetime
    
class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    sender_id: Optional[PyObjectId] = None
    recipient_id: Optional[PyObjectId] = None
    message: Optional[str] = None
    timestamp: Optional[datetime] = None

class AlertInDB(AlertBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
