from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone, timedelta
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
            # Normalize timezone offset format (+05:30 → +0530)
            value = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", value)

            # Try parsing with different formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f%z",  # With milliseconds and timezone
                "%Y-%m-%dT%H:%M:%S%z",     # Without milliseconds, with timezone
                "%Y-%m-%dT%H:%M:%S",       # Without timezone (default to IST)
            ]
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(value, fmt)
                    # Add IST timezone if missing
                    if not parsed.tzinfo:
                        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
                    return parsed
                except ValueError:
                    continue

            raise ValueError(f"Invalid datetime format: {value}")

        elif isinstance(value, datetime):
            # Handle datetime objects directly
            if not value.tzinfo:
                value = value.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            return value

        raise ValueError("Timestamp must be a string or datetime object")

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
