"""
API Endpoint — Health & Metrics.

GET /health — System health check
GET /metrics — Model performance metrics
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse, MetricsResponse
from app.services.prediction_service import prediction_service
from app.services.training_service import training_service

router = APIRouter(tags=["System"])

# Track application start time
APP_START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Returns the current health status of the application, database, and ML model.",
)
async def health_check():
    """Check system health status."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database="configured",
        model_loaded=prediction_service.is_model_loaded(),
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Model Metrics",
    description="Returns the performance metrics of the currently loaded ML model.",
)
async def get_metrics():
    """Get model performance metrics."""
    last_result = training_service.get_last_result()
    test_metrics = last_result.get("test_metrics", {}) if last_result else {}

    return MetricsResponse(
        model_name=settings.default_model,
        model_version=settings.model_version,
        rmse=test_metrics.get("rmse"),
        mae=test_metrics.get("mae"),
        r2_score=test_metrics.get("r2"),
        total_predictions=0,
        total_schedules=0,
        uptime_seconds=round(time.time() - APP_START_TIME, 1),
    )
