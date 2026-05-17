"""
Pydantic Schemas — Prediction.

Schemas for soil moisture prediction requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Request for soil moisture prediction."""
    field_id: Optional[str] = Field(None, description="Field UUID")
    vv_backscatter: float = Field(..., description="VV polarization (dB)", ge=-30, le=5)
    vh_backscatter: float = Field(..., description="VH polarization (dB)", ge=-40, le=0)
    ndvi: float = Field(..., description="NDVI value", ge=-1, le=1)
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Relative humidity (%)", ge=0, le=100)
    rainfall: float = Field(0.0, description="Rainfall (mm)", ge=0)
    wind_speed: float = Field(2.0, description="Wind speed (m/s)", ge=0)
    sand_pct: float = Field(40.0, description="Sand %", ge=0, le=100)
    clay_pct: float = Field(25.0, description="Clay %", ge=0, le=100)
    silt_pct: float = Field(35.0, description="Silt %", ge=0, le=100)
    elevation: float = Field(500.0, description="Elevation (m)")
    organic_matter: float = Field(2.5, description="Organic matter (%)")
    field_capacity: float = Field(0.30, description="Field capacity (cm³/cm³)")
    wilting_point: float = Field(0.15, description="Wilting point (cm³/cm³)")


class PredictResponse(BaseModel):
    """Response with moisture prediction results."""
    predicted_moisture: float = Field(..., description="Predicted soil moisture (cm³/cm³)")
    confidence: float = Field(..., description="Prediction confidence (0–1)")
    model_name: str = Field(...)
    sar_moisture: Dict[str, float] = Field(default_factory=dict)
    vegetation_stage: str = Field("")
    features_used: int = Field(0)
    processing_steps: List[str] = Field(default_factory=list)


class BatchPredictRequest(BaseModel):
    """Request for batch predictions."""
    observations: List[PredictRequest]


class BatchPredictResponse(BaseModel):
    """Response with batch predictions."""
    predictions: List[PredictResponse]
    total: int
    average_moisture: float
    average_confidence: float
