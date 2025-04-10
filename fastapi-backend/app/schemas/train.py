from pydantic import BaseModel, Field, validator
from bson import ObjectId
from typing import Optional

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v is not None and not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v) if v is not None else None

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string", format="object-id", nullable=True)

class TrainBase(BaseModel):
    train_id: str = Field(..., min_length=3)
    name: Optional[str] = None
    current_status: Optional[str] = None
    current_route_id: Optional[str] = None
    current_route_ref: Optional[PyObjectId] = None

    @validator('current_status')
    def validate_status(cls, v):
        allowed_statuses = [
            "in_service_running",
            "in_service_not_running",
            "maintenance",
            "out_of_service",
            None  # Allow null values for current_status
        ]
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status. Allowed values are: {allowed_statuses}")
        return v

    class Config:
        json_encoders = {ObjectId: str}

class TrainCreate(TrainBase):
    pass

class TrainUpdate(BaseModel):
    train_id: Optional[str] = None
    name: Optional[str] = None
    current_status: Optional[str] = None
    current_route_id: Optional[str] = None
    current_route_ref: Optional[PyObjectId] = None

class TrainInDB(TrainBase):
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
