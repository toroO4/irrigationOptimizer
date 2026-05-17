"""
API Endpoint — Moisture Prediction.

GET /predict-moisture — Predict soil moisture for given inputs
"""

from fastapi import APIRouter, HTTPException, Query

from app.core.logging_config import get_logger
from app.schemas.prediction import PredictResponse
from app.services.prediction_service import prediction_service

logger = get_logger(__name__)
router = APIRouter(tags=["Prediction"])


@router.get(
    "/predict-moisture",
    response_model=PredictResponse,
    summary="Predict Soil Moisture",
    description="Predict soil moisture using SAR backscatter, weather, and soil parameters. "
                "Runs the full SAR processing pipeline and ML model.",
)
async def predict_moisture(
    vv_backscatter: float = Query(..., description="VV polarization (dB)", ge=-30, le=5),
    vh_backscatter: float = Query(..., description="VH polarization (dB)", ge=-40, le=0),
    ndvi: float = Query(..., description="NDVI value", ge=-1, le=1),
    temperature: float = Query(..., description="Temperature (°C)"),
    humidity: float = Query(..., description="Relative humidity (%)", ge=0, le=100),
    rainfall: float = Query(0.0, description="Rainfall (mm)", ge=0),
    wind_speed: float = Query(2.0, description="Wind speed (m/s)", ge=0),
    sand_pct: float = Query(40.0, description="Sand %", ge=0, le=100),
    clay_pct: float = Query(25.0, description="Clay %", ge=0, le=100),
    silt_pct: float = Query(35.0, description="Silt %", ge=0, le=100),
    elevation: float = Query(500.0, description="Elevation (m)"),
    organic_matter: float = Query(2.5, description="Organic matter (%)"),
    field_capacity: float = Query(0.30, description="Field capacity"),
    wilting_point: float = Query(0.15, description="Wilting point"),
):
    """
    Predict soil moisture from input parameters.

    The endpoint runs the complete SAR processing pipeline:
    1. Radiometric calibration of backscatter values
    2. Moisture inversion using Water Cloud Model
    3. Feature extraction
    4. ML model prediction (if model is trained)
    5. Returns predicted moisture with confidence score
    """
    try:
        result = await prediction_service.predict(
            vv_backscatter=vv_backscatter,
            vh_backscatter=vh_backscatter,
            ndvi=ndvi,
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            wind_speed=wind_speed,
            sand_pct=sand_pct,
            clay_pct=clay_pct,
            silt_pct=silt_pct,
            elevation=elevation,
            organic_matter=organic_matter,
            field_capacity=field_capacity,
            wilting_point=wilting_point,
        )
        return PredictResponse(**result)

    except Exception as e:
        logger.error("Prediction error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
