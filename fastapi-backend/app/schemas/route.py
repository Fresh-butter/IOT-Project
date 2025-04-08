"""
Route schema module.
Defines Pydantic models for route data validation and serialization.
"""
from typing import Optional, List, Dict, Any
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

class Checkpoint(BaseModel):
    timestamp: datetime
    rfid_tag: Optional[str] = None
    location: List[float]

class RouteBase(BaseModel):
    route_id: str
    route_name: str
    assigned_train_id: str
    assigned_train_ref: PyObjectId
    checkpoints: List[Checkpoint]
    
class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    route_id: Optional[str] = None
    route_name: Optional[str] = None
    assigned_train_id: Optional[str] = None
    assigned_train_ref: Optional[PyObjectId] = None
    checkpoints: Optional[List[Checkpoint]] = None

class RouteInDB(RouteBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
