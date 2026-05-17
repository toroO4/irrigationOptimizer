from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db
from app.models.farm import Farm, Field
from app.schemas.farm import FarmCreate, FarmRead, FieldCreate, FieldRead
from app.core.logging_config import get_logger
import uuid

logger = get_logger(__name__)
router = APIRouter(tags=["Farms & Fields"])

# Mock User ID since auth is not fully implemented
DEFAULT_USER_ID = "mock-user-1234"

@router.get("/farms", response_model=List[FarmRead], summary="Get All Farms")
async def get_farms(db: AsyncSession = Depends(get_db)):
    """Fetch all farms for the current user."""
    result = await db.execute(
        select(Farm)
        .where(Farm.owner_id == DEFAULT_USER_ID)
        .options(selectinload(Farm.fields))
    )
    farms = result.scalars().all()
    return farms

@router.post("/farms", response_model=FarmRead, status_code=status.HTTP_201_CREATED)
async def create_farm(farm_in: FarmCreate, db: AsyncSession = Depends(get_db)):
    """Create a new farm."""
    farm = Farm(
        id=str(uuid.uuid4()),
        owner_id=DEFAULT_USER_ID,
        **farm_in.model_dump()
    )
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return farm

@router.get("/farms/{farm_id}/fields", response_model=List[FieldRead])
async def get_fields(farm_id: str, db: AsyncSession = Depends(get_db)):
    """Get all fields for a specific farm."""
    result = await db.execute(
        select(Field).where(Field.farm_id == farm_id)
    )
    return result.scalars().all()

@router.post("/farms/{farm_id}/fields", response_model=FieldRead, status_code=status.HTTP_201_CREATED)
async def create_field(farm_id: str, field_in: FieldCreate, db: AsyncSession = Depends(get_db)):
    """Add a new field to a farm."""
    # Verify farm exists
    farm_result = await db.execute(select(Farm).where(Farm.id == farm_id))
    if not farm_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Farm not found")

    field = Field(
        id=str(uuid.uuid4()),
        farm_id=farm_id,
        **field_in.model_dump()
    )
    db.add(field)
    await db.commit()
    await db.refresh(field)
    return field

@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(field_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a field."""
    result = await db.execute(select(Field).where(Field.id == field_id))
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    await db.delete(field)
    await db.commit()
    return None
