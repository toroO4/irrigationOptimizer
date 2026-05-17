"""
SAR Processing — Radiometric Calibration.

Converts raw Sentinel-1 GRD digital numbers (DN) to calibrated
sigma-nought (σ⁰) backscatter coefficients in decibels (dB).

In production, this would use SNAP's Calibration operator or GDAL.
This implementation provides the mathematical equivalent for
environments without SNAP/GDAL installed.
"""

import math
from typing import Dict, Optional, Tuple

import numpy as np

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def calibrate_sentinel1(
    dn_values: np.ndarray,
    calibration_lut: Optional[np.ndarray] = None,
    polarization: str = "VV",
) -> np.ndarray:
    """
    Apply radiometric calibration to Sentinel-1 GRD data.

    Converts raw digital number (DN) values to sigma-nought (σ⁰)
    backscatter coefficient in decibels (dB).

    The calibration formula is:
        σ⁰ = DN² / A_i²

    Where A_i is the calibration Look-Up Table (LUT) value for pixel i.
    If no LUT is provided, a default calibration constant is used.

    Args:
        dn_values: 2D numpy array of raw DN pixel values.
        calibration_lut: Optional calibration LUT array (same shape as dn_values).
        polarization: Polarization channel ("VV" or "VH").

    Returns:
        2D numpy array of calibrated σ⁰ values in dB.
    """
    logger.info(
        "Starting radiometric calibration — polarization=%s, shape=%s",
        polarization, dn_values.shape,
    )

    # Avoid division by zero and log of zero
    dn_safe = np.where(dn_values > 0, dn_values.astype(np.float64), 1e-10)

    if calibration_lut is not None:
        # Use provided LUT for calibration
        lut_safe = np.where(calibration_lut > 0, calibration_lut.astype(np.float64), 1.0)
        sigma0_linear = (dn_safe ** 2) / (lut_safe ** 2)
    else:
        # Default calibration: assume DN is already in amplitude format
        # Apply standard calibration constant for Sentinel-1 GRD
        # Reference: Sentinel-1 Product Specification (ESA)
        calibration_constant = 1.0  # Normalized for pre-calibrated data
        sigma0_linear = (dn_safe ** 2) / calibration_constant

    # Convert to decibels
    sigma0_db = 10.0 * np.log10(sigma0_linear + 1e-30)

    # Clip extreme values (valid SAR range is approximately -35 to +5 dB)
    sigma0_db = np.clip(sigma0_db, -35.0, 5.0)

    logger.info(
        "Calibration complete — min=%.2f dB, max=%.2f dB, mean=%.2f dB",
        float(np.min(sigma0_db)),
        float(np.max(sigma0_db)),
        float(np.mean(sigma0_db)),
    )

    return sigma0_db


def calibrate_from_db_values(
    vv_db: float,
    vh_db: float,
) -> Tuple[float, float]:
    """
    Validate and normalize pre-calibrated backscatter values.

    When backscatter values are already in dB (e.g., from GEE or
    pre-processed datasets), this function validates the range and
    applies any necessary corrections.

    Args:
        vv_db: VV polarization backscatter in dB.
        vh_db: VH polarization backscatter in dB.

    Returns:
        Tuple of (calibrated_vv_db, calibrated_vh_db).
    """
    # Validate ranges
    vv_calibrated = max(min(vv_db, 5.0), -30.0)
    vh_calibrated = max(min(vh_db, 0.0), -35.0)

    return vv_calibrated, vh_calibrated


def compute_backscatter_statistics(
    sigma0_db: np.ndarray,
) -> Dict[str, float]:
    """
    Compute statistical summary of calibrated backscatter data.

    Args:
        sigma0_db: 2D array of calibrated σ⁰ values in dB.

    Returns:
        Dictionary with min, max, mean, std, and median statistics.
    """
    return {
        "min_db": float(np.min(sigma0_db)),
        "max_db": float(np.max(sigma0_db)),
        "mean_db": float(np.mean(sigma0_db)),
        "std_db": float(np.std(sigma0_db)),
        "median_db": float(np.median(sigma0_db)),
    }


def db_to_linear(db_value: float) -> float:
    """Convert decibel value to linear scale."""
    return 10.0 ** (db_value / 10.0)


def linear_to_db(linear_value: float) -> float:
    """Convert linear scale value to decibels."""
    return 10.0 * math.log10(max(linear_value, 1e-30))
