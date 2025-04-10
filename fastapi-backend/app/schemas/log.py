from pydantic import BaseModel, Field
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
    def __get_pydantic_json_schema__(cls, schema, handler):
        json_schema = handler(schema)
        json_schema.update(type="string", format="object-id", nullable=True)
        return json_schema

class LogBase(BaseModel):
    train_id: str = Field(..., min_length=1)
    train_ref: PyObjectId = Field(..., description="MongoDB ObjectId reference for the train")
    rfid_tag: Optional[str] = Field(None, description="RFID tag detected by the device")
    location: Optional[List[float]] = Field(
        None,
        min_items=2,
        max_items=2,
        description="Geographical coordinates [longitude, latitude]"
    )
    timestamp: datetime = Field(..., description="Timestamp in ISO8601 format with timezone offset")
    accuracy: Optional[str] = Field(
        None,
        description="Accuracy category (e.g., excellent, good, moderate, poor, invalid)"
    )
    is_test: bool = Field(..., description="Flag to indicate if the log is test data")

    class Config:
        json_schema_extra = {
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
        populate_by_name = True  # Updated for Pydantic v2 compatibility
