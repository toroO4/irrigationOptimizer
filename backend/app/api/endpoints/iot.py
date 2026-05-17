"""
API Endpoints — IoT Sensor Webhooks.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging_config import get_logger
from app.database.session import get_db
from app.models.sensor import SensorData
from app.schemas.sensor import SensorDataCreate, SensorDataResponse
from app.core.security import get_current_active_user

logger = get_logger(__name__)
router = APIRouter(prefix="/iot", tags=["IoT Sensors"])


@router.post("/sensor-data", response_model=SensorDataResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor_reading(
    data_in: SensorDataCreate,
    db: AsyncSession = Depends(get_db),
    # Optional: You could require a specific IoT service account or just use current_user
    # current_user = Depends(get_current_active_user)
) -> Any:
    """
    Ingest a new telemetry reading from an IoT soil moisture sensor.
    """
    db_sensor = SensorData(
        field_id=data_in.field_id,
        moisture_level=data_in.moisture_level,
        temperature=data_in.temperature,
    )
    db.add(db_sensor)
    await db.commit()
    await db.refresh(db_sensor)
    
    logger.info(f"Received sensor data for field {data_in.field_id}: moisture={data_in.moisture_level}")
    return db_sensor


@router.get("/sensor-data/{field_id}", response_model=List[SensorDataResponse])
async def get_sensor_readings(
    field_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> Any:
    """
    Get recent sensor readings for a specific field.
    """
    stmt = select(SensorData).where(SensorData.field_id == field_id).order_by(SensorData.recorded_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
