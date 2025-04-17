"""
Train schema module.
Defines Pydantic models for train data validation and serialization.
"""
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from app.database import PyObjectId  # Use centralized PyObjectId implementation

class TrainBase(BaseModel):
    train_id: str = Field(
        ..., 
        description="Unique identifier for the train", 
        example="101"
    )
    name: Optional[str] = Field(
        None, 
        description="Name of the train", 
        example="IIITH Express"
    )
    current_status: Optional[str] = Field(
        None, 
        description="Current operational status of the train",
        example="in_service_running"
    )
    current_route_id: Optional[str] = Field(
        None, 
        description="ID of the route currently assigned to the train", 
        example="R101"
    )
    current_route_ref: Optional[PyObjectId] = Field(
        None, 
        description="MongoDB ObjectId reference to the route document", 
        example="67e80645e4a58df990138c2b"
    )

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "train_id": "101",
                "name": "IIITH Express",
                "current_status": "in_service_running",
                "current_route_id": "R101",
                "current_route_ref": "67e80645e4a58df990138c2b"
            }
        }

class TrainCreate(TrainBase):
    pass

class TrainUpdate(BaseModel):
    train_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the train", 
        example="101"
    )
    name: Optional[str] = Field(
        None, 
        description="Name of the train", 
        example="IIITH Express"
    )
    current_status: Optional[str] = Field(
        None, 
        description="Current operational status of the train",
        example="in_service_running"
    )
    current_route_id: Optional[str] = Field(
        None, 
        description="ID of the route currently assigned to the train", 
        example="R101"
    )
    current_route_ref: Optional[PyObjectId] = Field(
        None, 
        description="MongoDB ObjectId reference to the route document", 
        example="67e80645e4a58df990138c2b"
    )

    class Config:
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "IIITH Express",
                "current_status": "in_service_running",
                "current_route_id": "R101",
                "current_route_ref": "67e80645e4a58df990138c2b"
            }
        }

class TrainInDB(TrainBase):
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "_id": "67e80645e4a58df990138c2b",
                "train_id": "101",
                "name": "IIITH Express",
                "current_status": "in_service_running",
                "current_route_id": "R101",
                "current_route_ref": "67e80645e4a58df990138c2b"
            }
        }
