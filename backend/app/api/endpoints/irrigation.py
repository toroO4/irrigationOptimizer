"""
API Endpoint — Irrigation Operations.

POST /generate-irrigation-plan — Generate irrigation schedule
GET /schedule — Get current schedules
"""

from fastapi import APIRouter, HTTPException

from app.core.logging_config import get_logger
from app.schemas.irrigation import (
    IrrigationPlanRequest,
    IrrigationPlanResponse,
    MultiFieldPlanRequest,
    MultiFieldPlanResponse,
)
from app.services.irrigation_service import irrigation_service

logger = get_logger(__name__)
router = APIRouter(tags=["Irrigation"])


@router.post(
    "/generate-irrigation-plan",
    response_model=IrrigationPlanResponse,
    summary="Generate Irrigation Plan",
    description="Generate an irrigation plan for a field based on current moisture, "
                "soil properties, crop type, and weather conditions.",
)
async def generate_irrigation_plan(request: IrrigationPlanRequest):
    """
    Generate an irrigation schedule for a single field.

    Uses the core scheduling logic:
        if moisture < threshold:
            deficit = field_capacity - current_moisture
            runtime = deficit / (pump_flow_rate × efficiency)
            generate_schedule()
    """
    try:
        params = request.model_dump(exclude={"field_id"})
        result = await irrigation_service.generate_plan(params)
        return IrrigationPlanResponse(**result)

    except Exception as e:
        logger.error("Irrigation plan error: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/schedule",
    summary="Get Schedules",
    description="Retrieve current and upcoming irrigation schedules.",
)
async def get_schedules(limit: int = 50):
    """Get the list of generated irrigation schedules."""
    schedules = irrigation_service.get_schedules(limit=limit)
    return {
        "total": len(schedules),
        "schedules": schedules,
    }
