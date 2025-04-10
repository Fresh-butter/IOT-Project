from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

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
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            # Handle missing/invalid timezone offset
            if "+05:3" in value:
                value = value.replace("+05:3", "+05:30")
            
            # Try multiple datetime formats
            for fmt in (
                "%Y-%m-%dT%H:%M:%S%z",        # Without milliseconds
                "%Y-%m-%dT%H:%M:%S.%f%z",     # With milliseconds
                "%Y-%m-%dT%H:%M:%S+05:30",    # IST offset without ms
                "%Y-%m-%dT%H:%M:%S.%f+05:30"  # IST offset with ms
            ):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        raise ValueError("Invalid datetime format")

    class Config:
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "train_id": "101",
                "train_ref": "67e80645e4a58df990138c2b",
                "timestamp": "2025-04-10T14:23:05+05:30",
                "rfid_tag": "RFID_101_B2",
                "location": [76.8512, 28.7041],
                "accuracy": "good",
                "is_test": False
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
