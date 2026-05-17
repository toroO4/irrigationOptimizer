"""
API Endpoint — History.

GET /history — Historical predictions and schedules
"""

from fastapi import APIRouter, Query

from app.services.irrigation_service import irrigation_service

router = APIRouter(tags=["History"])


@router.get(
    "/history",
    summary="Get History",
    description="Retrieve historical irrigation schedules and prediction records.",
)
async def get_history(
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    record_type: str = Query("all", description="Type: all, schedules, predictions"),
):
    """
    Get historical records of irrigation schedules and predictions.

    Returns the most recent records in reverse chronological order.
    """
    history = irrigation_service.get_history(limit=limit)
    return {
        "total": len(history),
        "record_type": record_type,
        "records": history,
    }
