from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import re

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v and not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v) if v else None

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string", format="object-id", nullable=True)

class LogBase(BaseModel):
    train_id: str = Field(..., min_length=1)
    train_ref: PyObjectId = Field(...)
    rfid_tag: Optional[str] = None
    location: Optional[List[float]] = Field(None, min_items=2, max_items=2)
    timestamp: datetime = Field(...)
    accuracy: Optional[str] = None
    is_test: bool = Field(...)

    @validator("timestamp", pre=True)
    def normalize_timestamp(cls, value):
        if isinstance(value, str):
            # Fix common formatting issues
            value = re.sub(r"(\+\d{1,2}):(\d{1})$", r"\1\230", value)  # Fix +05:3 → +05:30
            value = value.replace(" IST", "+05:30")  # Handle old format
            
            # Try multiple valid formats
            formats = [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S+05:30",
                "%Y-%m-%dT%H:%M:%S.%f+05:30"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        raise ValueError(f"Invalid datetime format: {value}")

    class Config:
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "train_id": "201",
                "train_ref": "67f72f93481176d59dec04a6",
                "timestamp": "2025-04-10T14:23:05+05:30",
                "rfid_tag": "a1b2c3d4",
                "location": [17.447528, 78.348740],
                "accuracy": "good",
                "is_test": True
            }
        }

class LogCreate(LogBase):
    pass

class LogUpdate(BaseModel):
    train_id: Optional[str] = None
    train_ref: Optional[PyObjectId] = None
    rfid_tag: Optional[str] = None
    location: Optional[List[float]] = None
    timestamp: Optional[datetime] = None
    accuracy: Optional[str] = None
    is_test: Optional[bool] = None

class LogInDB(LogBase):
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
