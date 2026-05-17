"""
Pydantic Schemas — IoT Sensors.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SensorDataCreate(BaseModel):
    field_id: str = Field(..., description="UUID of the field")
    moisture_level: float = Field(..., ge=0.0, le=1.0, description="Volumetric water content")
    temperature: Optional[float] = Field(None, description="Soil temperature in Celsius")


class SensorDataResponse(SensorDataCreate):
    id: str
    recorded_at: datetime

    class Config:
        from_attributes = True
