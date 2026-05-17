"""
Pydantic Schemas — Common Responses.

Shared response schemas used across multiple endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="1.0.0")
    timestamp: str = Field(...)
    database: str = Field(..., example="connected")
    model_loaded: bool = Field(False)


class MetricsResponse(BaseModel):
    """System metrics response."""
    model_name: str = Field(..., example="random_forest")
    model_version: str = Field(..., example="1.0.0")
    rmse: Optional[float] = Field(None)
    mae: Optional[float] = Field(None)
    r2_score: Optional[float] = Field(None)
    total_predictions: int = Field(0)
    total_schedules: int = Field(0)
    uptime_seconds: float = Field(0.0)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False
