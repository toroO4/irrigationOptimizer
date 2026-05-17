"""
SAR Processing — Soil Moisture Inversion.

Implements the Water Cloud Model (WCM) to separate vegetation
contribution from soil backscatter and invert SAR σ⁰ to
volumetric soil moisture content.

Also provides a Change Detection approach as an alternative method.
"""

import math
from typing import Dict, Optional, Tuple

import numpy as np

from app.config.constants import WCM_DEFAULT_PARAMS
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def water_cloud_model(
    vv_db: float,
    vh_db: float,
    ndvi: float,
    incidence_angle: float = 38.0,
    params: Optional[Dict[str, float]] = None,
) -> float:
    """
    Apply the Water Cloud Model to estimate soil moisture.

    The WCM separates the total SAR backscatter into vegetation
    and soil contributions:

        σ⁰_total = σ⁰_veg + τ² × σ⁰_soil

    Where:
        σ⁰_veg = A × V1 × cos(θ) × (1 - τ²)
        τ² = exp(-2 × B × V2 / cos(θ))
        σ⁰_soil = C × mv + D

    V1, V2 = vegetation descriptors (NDVI used as proxy)
    mv = volumetric soil moisture
    A, B, C, D = empirical coefficients

    Args:
        vv_db: VV polarization backscatter (dB).
        vh_db: VH polarization backscatter (dB).
        ndvi: Normalized Difference Vegetation Index (0–1).
        incidence_angle: Incidence angle in degrees.
        params: Optional WCM empirical parameters dict with keys A, B, C, D.

    Returns:
        Estimated volumetric soil moisture (cm³/cm³), clamped to [0, 0.6].
    """
    if params is None:
        params = WCM_DEFAULT_PARAMS

    A = params["A"]
    B = params["B"]
    C = params["C"]
    D = params["D"]

    theta = math.radians(incidence_angle)
    cos_theta = math.cos(theta)

    # Use NDVI as vegetation descriptor (V1 = V2 = NDVI)
    ndvi_safe = max(ndvi, 0.01)  # Avoid zero NDVI

    # Two-way vegetation transmissivity
    tau_squared = math.exp(-2.0 * B * ndvi_safe / cos_theta)

    # Vegetation contribution to backscatter
    sigma_veg_linear = A * ndvi_safe * cos_theta * (1.0 - tau_squared)

    # Convert observed VV from dB to linear
    sigma_total_linear = 10.0 ** (vv_db / 10.0)

    # Isolate soil backscatter
    sigma_soil_linear = (sigma_total_linear - sigma_veg_linear) / (tau_squared + 1e-10)

    # Invert soil backscatter to moisture
    # σ⁰_soil = C × mv + D  →  mv = (σ⁰_soil_dB - D) / C
    sigma_soil_db = 10.0 * math.log10(max(sigma_soil_linear, 1e-30))
    moisture = (sigma_soil_db - D) / (C + 1e-10)

    # Clamp to physical range [0, 0.6] cm³/cm³
    moisture = max(0.0, min(moisture, 0.60))

    logger.debug(
        "WCM inversion: VV=%.2f dB, NDVI=%.2f → moisture=%.3f cm³/cm³",
        vv_db, ndvi, moisture,
    )

    return moisture


def change_detection_moisture(
    current_vv_db: float,
    dry_reference_db: float = -18.0,
    wet_reference_db: float = -8.0,
    saturation_moisture: float = 0.50,
    residual_moisture: float = 0.05,
) -> float:
    """
    Estimate soil moisture using the Change Detection method.

    Scales the current backscatter between known dry and wet
    references to estimate relative soil moisture.

        mv = residual + (saturation - residual) ×
             (σ⁰_current - σ⁰_dry) / (σ⁰_wet - σ⁰_dry)

    This method does not require vegetation correction but assumes
    consistent surface roughness and vegetation conditions between
    the reference and current images.

    Args:
        current_vv_db: Current VV backscatter in dB.
        dry_reference_db: Driest observed backscatter (dB).
        wet_reference_db: Wettest observed backscatter (dB).
        saturation_moisture: Saturation moisture content (cm³/cm³).
        residual_moisture: Minimum residual moisture (cm³/cm³).

    Returns:
        Estimated volumetric soil moisture (cm³/cm³).
    """
    # Normalize current backscatter between dry and wet references
    range_db = wet_reference_db - dry_reference_db
    if abs(range_db) < 0.1:
        logger.warning("Dry/wet reference range too small: %.2f dB", range_db)
        return (saturation_moisture + residual_moisture) / 2.0

    normalized = (current_vv_db - dry_reference_db) / range_db
    normalized = max(0.0, min(normalized, 1.0))

    moisture = residual_moisture + (saturation_moisture - residual_moisture) * normalized
    moisture = max(0.0, min(moisture, 0.60))

    logger.debug(
        "Change detection: VV=%.2f dB → moisture=%.3f cm³/cm³",
        current_vv_db, moisture,
    )

    return moisture


def multi_polarization_moisture(
    vv_db: float,
    vh_db: float,
    ndvi: float = 0.5,
    method: str = "wcm",
) -> Dict[str, float]:
    """
    Estimate soil moisture using multiple polarization channels.

    Combines VV and VH backscatter information with NDVI to
    provide a more robust moisture estimate. Returns estimates
    from multiple approaches for comparison.

    Args:
        vv_db: VV backscatter (dB).
        vh_db: VH backscatter (dB).
        ndvi: NDVI value.
        method: Primary method ("wcm" or "change_detection").

    Returns:
        Dictionary with moisture estimates and metadata:
            - moisture_wcm: WCM-derived moisture
            - moisture_cd: Change Detection moisture
            - moisture_combined: Weighted average
            - vh_vv_ratio: Cross-polarization ratio
            - confidence: Estimation confidence (0–1)
    """
    # WCM estimate (uses VV + NDVI)
    moisture_wcm = water_cloud_model(vv_db, vh_db, ndvi)

    # Change Detection estimate
    moisture_cd = change_detection_moisture(vv_db)

    # VH/VV ratio (useful as vegetation indicator)
    vh_vv_ratio = vh_db - vv_db  # In dB domain, ratio = difference

    # Combined estimate (weighted by NDVI-based confidence)
    # Lower NDVI → more confidence in WCM (less vegetation attenuation)
    wcm_weight = max(0.3, 1.0 - ndvi)
    cd_weight = 1.0 - wcm_weight
    moisture_combined = wcm_weight * moisture_wcm + cd_weight * moisture_cd

    # Confidence: higher when both methods agree
    agreement = 1.0 - abs(moisture_wcm - moisture_cd) / 0.30
    confidence = max(0.1, min(agreement, 1.0))

    return {
        "moisture_wcm": round(moisture_wcm, 4),
        "moisture_cd": round(moisture_cd, 4),
        "moisture_combined": round(moisture_combined, 4),
        "vh_vv_ratio": round(vh_vv_ratio, 2),
        "confidence": round(confidence, 3),
    }
