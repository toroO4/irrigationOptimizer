"""
Utility — Data Validators.

Input validation functions for API requests and data processing.
"""

from typing import List, Optional

from app.config.constants import VALID_RANGES


def validate_backscatter(vv_db: float, vh_db: float) -> List[str]:
    """Validate SAR backscatter values. Returns list of warnings."""
    warnings = []
    vv_min, vv_max = VALID_RANGES["vv_backscatter"]
    vh_min, vh_max = VALID_RANGES["vh_backscatter"]

    if not (vv_min <= vv_db <= vv_max):
        warnings.append(f"VV backscatter {vv_db} dB is outside expected range [{vv_min}, {vv_max}]")
    if not (vh_min <= vh_db <= vh_max):
        warnings.append(f"VH backscatter {vh_db} dB is outside expected range [{vh_min}, {vh_max}]")
    if vh_db > vv_db:
        warnings.append("VH > VV is unusual for Sentinel-1 C-band")

    return warnings


def validate_soil_texture(sand: float, clay: float, silt: float) -> bool:
    """Check that soil texture percentages sum to ~100%."""
    total = sand + clay + silt
    return 95.0 <= total <= 105.0


def validate_moisture_range(moisture: float) -> bool:
    """Check that moisture is within physical bounds."""
    return 0.0 <= moisture <= 0.60


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate geographic coordinates."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
