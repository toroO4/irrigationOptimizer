"""
SAR Processing — Feature Extraction.

Extracts all SAR and auxiliary features required by the ML model:
VV, VH, VH/VV ratio, cross-pol ratio, NDVI, rainfall, elevation, soil properties.
"""

from typing import Dict, List, Optional

import numpy as np

from app.config.constants import ALL_FEATURES, NDVI_THRESHOLDS
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def extract_sar_features(
    vv_db: float,
    vh_db: float,
) -> Dict[str, float]:
    """
    Extract SAR-derived features from backscatter values.

    Computes VV, VH, VH/VV ratio, and cross-polarization ratio.

    Args:
        vv_db: VV polarization backscatter (dB).
        vh_db: VH polarization backscatter (dB).

    Returns:
        Dictionary of SAR features.
    """
    vh_vv_ratio = vh_db - vv_db  # dB domain ratio
    cross_pol_ratio = 10.0 ** ((vh_db - vv_db) / 10.0)  # Linear domain

    return {
        "vv_backscatter": round(vv_db, 4),
        "vh_backscatter": round(vh_db, 4),
        "vh_vv_ratio": round(vh_vv_ratio, 4),
        "cross_pol_ratio": round(cross_pol_ratio, 6),
    }


def extract_spectral_features(
    ndvi: float,
    ndwi: Optional[float] = None,
) -> Dict[str, float]:
    """
    Extract optical spectral index features.

    Args:
        ndvi: Normalized Difference Vegetation Index.
        ndwi: Normalized Difference Water Index (optional).

    Returns:
        Dictionary of spectral features.
    """
    features = {
        "ndvi": round(ndvi, 4),
        "ndwi": round(ndwi, 4) if ndwi is not None else 0.0,
    }
    return features


def extract_weather_features(
    temperature: float,
    humidity: float,
    rainfall: float,
    wind_speed: float = 2.0,
    et0: Optional[float] = None,
) -> Dict[str, float]:
    """
    Extract weather features for the ML model.

    If ET₀ is not provided, it is estimated using a simplified
    Hargreaves equation.

    Args:
        temperature: Air temperature (°C).
        humidity: Relative humidity (%).
        rainfall: Daily precipitation (mm).
        wind_speed: Wind speed at 2m (m/s).
        et0: Reference evapotranspiration (mm/day). Computed if None.

    Returns:
        Dictionary of weather features.
    """
    if et0 is None:
        # Simplified Hargreaves ET₀ estimation
        # ET₀ = 0.0023 × (T_mean + 17.8) × (T_max - T_min)^0.5 × Ra
        # Using approximation with T_range ≈ 10°C, Ra ≈ 15 MJ/m²/day
        t_range = 10.0
        ra = 15.0  # MJ/m²/day approximation
        et0 = 0.0023 * (temperature + 17.8) * (t_range ** 0.5) * ra * 0.408
        et0 = max(0.0, et0)

    return {
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "rainfall": round(rainfall, 2),
        "wind_speed": round(wind_speed, 2),
        "et0": round(et0, 3),
    }


def extract_soil_features(
    sand_pct: float,
    clay_pct: float,
    silt_pct: float,
    organic_matter: float = 2.5,
    field_capacity: float = 0.30,
    wilting_point: float = 0.15,
) -> Dict[str, float]:
    """
    Extract soil property features.

    Args:
        sand_pct: Sand percentage (0–100).
        clay_pct: Clay percentage (0–100).
        silt_pct: Silt percentage (0–100).
        organic_matter: Organic matter percentage.
        field_capacity: Field capacity (cm³/cm³).
        wilting_point: Wilting point (cm³/cm³).

    Returns:
        Dictionary of soil features.
    """
    return {
        "sand_pct": round(sand_pct, 2),
        "clay_pct": round(clay_pct, 2),
        "silt_pct": round(silt_pct, 2),
        "organic_matter": round(organic_matter, 2),
        "field_capacity": round(field_capacity, 4),
        "wilting_point": round(wilting_point, 4),
    }


def extract_terrain_features(
    elevation: float = 500.0,
    slope: float = 0.0,
    aspect: float = 0.0,
) -> Dict[str, float]:
    """
    Extract terrain features from DEM data.

    Args:
        elevation: Elevation in meters above sea level.
        slope: Terrain slope in degrees.
        aspect: Terrain aspect in degrees from north.

    Returns:
        Dictionary of terrain features.
    """
    return {
        "elevation": round(elevation, 2),
        "slope": round(slope, 2),
        "aspect": round(aspect, 2),
    }


def build_feature_vector(
    vv_db: float,
    vh_db: float,
    ndvi: float,
    temperature: float,
    humidity: float,
    rainfall: float,
    sand_pct: float,
    clay_pct: float,
    silt_pct: float,
    elevation: float = 500.0,
    wind_speed: float = 2.0,
    et0: Optional[float] = None,
    ndwi: Optional[float] = None,
    organic_matter: float = 2.5,
    field_capacity: float = 0.30,
    wilting_point: float = 0.15,
    slope: float = 0.0,
    aspect: float = 0.0,
) -> Dict[str, float]:
    """
    Build a complete feature vector for the ML model.

    Combines all feature categories (SAR, spectral, weather, soil,
    terrain) into a single ordered dictionary matching ALL_FEATURES.

    Args:
        vv_db: VV backscatter (dB).
        vh_db: VH backscatter (dB).
        ndvi: NDVI value.
        temperature: Temperature (°C).
        humidity: Relative humidity (%).
        rainfall: Daily rainfall (mm).
        sand_pct: Sand percentage.
        clay_pct: Clay percentage.
        silt_pct: Silt percentage.
        elevation: Elevation (m).
        wind_speed: Wind speed (m/s).
        et0: Reference ET (mm/day).
        ndwi: NDWI value.
        organic_matter: Organic matter (%).
        field_capacity: Field capacity (cm³/cm³).
        wilting_point: Wilting point (cm³/cm³).
        slope: Terrain slope (degrees).
        aspect: Terrain aspect (degrees).

    Returns:
        Ordered dictionary of all features matching ALL_FEATURES order.
    """
    features = {}
    features.update(extract_sar_features(vv_db, vh_db))
    features.update(extract_spectral_features(ndvi, ndwi))
    features.update(extract_weather_features(temperature, humidity, rainfall, wind_speed, et0))
    features.update(extract_soil_features(sand_pct, clay_pct, silt_pct, organic_matter, field_capacity, wilting_point))
    features.update(extract_terrain_features(elevation, slope, aspect))

    logger.debug("Feature vector built with %d features", len(features))
    return features


def classify_vegetation_stage(ndvi: float) -> str:
    """
    Classify vegetation growth stage based on NDVI value.

    Args:
        ndvi: NDVI value (-1 to 1).

    Returns:
        Vegetation stage classification string.
    """
    if ndvi < NDVI_THRESHOLDS["bare_soil"]:
        return "bare_soil"
    elif ndvi < NDVI_THRESHOLDS["sparse_vegetation"]:
        return "sparse_vegetation"
    elif ndvi < NDVI_THRESHOLDS["moderate_vegetation"]:
        return "moderate_vegetation"
    elif ndvi < NDVI_THRESHOLDS["dense_vegetation"]:
        return "dense_vegetation"
    else:
        return "peak_vegetation"
