"""
Pydantic Schemas — Irrigation.

Schemas for irrigation plan generation and schedule retrieval.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IrrigationPlanRequest(BaseModel):
    """Request to generate an irrigation plan."""
    field_id: Optional[str] = Field(None)
    current_moisture: float = Field(..., description="Current soil moisture (cm³/cm³)", ge=0, le=0.6)
    field_capacity: float = Field(0.30, ge=0, le=0.6)
    wilting_point: float = Field(0.15, ge=0, le=0.6)
    area_hectares: float = Field(1.0, gt=0)
    crop_type: str = Field("wheat")
    irrigation_type: str = Field("drip")
    pump_flow_rate_lph: float = Field(5000.0, gt=0)
    temperature: float = Field(30.0)
    humidity: float = Field(50.0, ge=0, le=100)
    wind_speed: float = Field(2.0, ge=0)
    rainfall_forecast: float = Field(0.0, ge=0)
    growth_stage: str = Field("mid")


class IrrigationPlanResponse(BaseModel):
    """Response with generated irrigation plan."""
    irrigation_needed: bool
    urgency: str
    drought_class: Dict[str, str] = Field(default_factory=dict)
    current_moisture: float
    threshold_moisture: float
    target_moisture: float
    deficit_mm: float
    water_volume_liters: float
    pump_runtime_hours: float
    irrigation_type: str
    crop_water_demand_mm: float
    recommendation: str
    scheduled_time: Optional[str] = None
    energy_estimate_kwh: Optional[float] = None


class MultiFieldPlanRequest(BaseModel):
    """Request for multi-field irrigation plan."""
    fields: List[IrrigationPlanRequest]


class MultiFieldPlanResponse(BaseModel):
    """Response with multi-field plan."""
    generated_at: str
    total_fields: int
    fields_needing_irrigation: int
    total_water_liters: float
    total_water_m3: float
    total_pump_runtime_hours: float
    schedules: List[Dict[str, Any]]


class ScheduleRecord(BaseModel):
    """A single schedule record for history/listing."""
    id: str
    field_id: str
    scheduled_time: str
    duration_hours: float
    water_volume_liters: float
    pump_runtime_hours: float
    urgency: str
    status: str
    deficit_mm: Optional[float] = None
    current_moisture: Optional[float] = None
