"""
Log schema module.
Defines Pydantic models for log data validation and serialization.
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

class LogBase(BaseModel):
    train_id: str
    train_ref: PyObjectId
    timestamp: datetime
    rfid_tag: Optional[str] = None
    location: List[float]
    
class LogCreate(LogBase):
    pass

class LogUpdate(BaseModel):
    train_id: Optional[str] = None
    train_ref: Optional[PyObjectId] = None
    timestamp: Optional[datetime] = None
    rfid_tag: Optional[str] = None
    location: Optional[List[float]] = None

class LogInDB(LogBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
