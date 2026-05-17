"""
Pydantic Schemas — Spatial/GeoJSON.

Schemas for GeoJSON export and soil map responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature object."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class GeoJSONResponse(BaseModel):
    """GeoJSON FeatureCollection response."""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SoilMapRequest(BaseModel):
    """Request parameters for soil map generation."""
    field_ids: Optional[List[str]] = None
    include_predictions: bool = Field(True)
    include_schedules: bool = Field(True)
