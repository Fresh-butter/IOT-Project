"""
Route schema module.
Defines Pydantic models for route data validation and serialization.
"""
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from bson import ObjectId
from app.database import PyObjectId

class Checkpoint(BaseModel):
    interval: Optional[int] = Field(None, ge=0)
    rfid_tag: Optional[str] = None
    location: Optional[List[float]] = Field(None, min_items=2, max_items=2)

    @validator('location')
    def validate_location(cls, v):
        if v and len(v) != 2:
            raise ValueError("Location must contain exactly 2 coordinates")
        return [round(coord, 6) for coord in v] if v else None

class RouteBase(BaseModel):
    route_id: Optional[str] = Field(None, min_length=3)
    route_name: Optional[str] = Field(None, min_length=5)
    start_time: Optional[datetime] = None
    assigned_train_id: Optional[str] = None
    assigned_train_ref: Optional[PyObjectId] = Field(
        None,
        example="67e834b559504bb750ee24b9"  # Add example for Swagger
    )
    checkpoints: Optional[List[Checkpoint]] = None

    @validator('checkpoints')
    def validate_checkpoints(cls, v):
        if v and v[0].interval != 0:
            raise ValueError("First checkpoint must have interval 0")
        return v

class RouteCreate(RouteBase):
    route_id: str = Field(..., min_length=3)
    route_name: str = Field(..., min_length=5)
    start_time: datetime = None
    checkpoints: List[Checkpoint] = Field(..., min_items=1)

class RouteUpdate(RouteBase):
    pass

class RouteInDB(RouteBase):
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
