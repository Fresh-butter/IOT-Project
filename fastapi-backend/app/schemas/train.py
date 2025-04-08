"""
Train schema module.
Defines Pydantic models for train data validation and serialization.
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

class TrainBase(BaseModel):
    # Define train fields based on your schema
    train_id: str
    train_name: Optional[str] = None
    status: Optional[str] = None
    current_location: Optional[List[float]] = None
    current_speed: Optional[float] = None
    
class TrainCreate(TrainBase):
    pass

class TrainUpdate(BaseModel):
    train_id: Optional[str] = None
    train_name: Optional[str] = None
    status: Optional[str] = None
    current_location: Optional[List[float]] = None
    current_speed: Optional[float] = None

class TrainInDB(TrainBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }
