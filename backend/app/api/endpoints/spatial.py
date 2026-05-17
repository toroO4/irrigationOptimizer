"""
API Endpoint — Spatial / GeoJSON.

GET /soil-map — GeoJSON soil moisture map
"""

from fastapi import APIRouter

from app.core.logging_config import get_logger
from app.services.export_service import export_service

logger = get_logger(__name__)
router = APIRouter(tags=["Spatial"])

# Sample field data for demonstration
SAMPLE_FIELDS = [
    {"name": "Field A", "centroid_lat": 18.52, "centroid_lon": 73.86, "crop_type": "wheat", "soil_type": "loam", "area_hectares": 2.5},
    {"name": "Field B", "centroid_lat": 18.53, "centroid_lon": 73.87, "crop_type": "rice", "soil_type": "clay_loam", "area_hectares": 3.0},
    {"name": "Field C", "centroid_lat": 18.51, "centroid_lon": 73.85, "crop_type": "maize", "soil_type": "sandy_loam", "area_hectares": 1.8},
    {"name": "Field D", "centroid_lat": 18.54, "centroid_lon": 73.88, "crop_type": "cotton", "soil_type": "silt_loam", "area_hectares": 4.0},
]

SAMPLE_PREDICTIONS = [
    {"predicted_moisture": 0.22, "confidence": 0.85},
    {"predicted_moisture": 0.35, "confidence": 0.90},
    {"predicted_moisture": 0.18, "confidence": 0.78},
    {"predicted_moisture": 0.28, "confidence": 0.82},
]


@router.get(
    "/soil-map",
    summary="Get Soil Moisture Map",
    description="Returns a GeoJSON FeatureCollection with field locations "
                "and their latest soil moisture predictions.",
)
async def get_soil_map():
    """
    Generate a GeoJSON soil moisture map.

    Returns field locations with their latest moisture predictions
    and properties as a GeoJSON FeatureCollection.
    """
    geojson = export_service.export_geojson(
        fields=SAMPLE_FIELDS,
        predictions=SAMPLE_PREDICTIONS,
    )
    return geojson
