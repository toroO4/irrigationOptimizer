"""
Irrigation Scheduling — Water Balance Model.

Implements FAO Penman-Monteith ET₀ calculation, crop coefficient (Kc)
lookup, effective rainfall computation, and soil water balance tracking.
"""

import math
from typing import Dict, Optional

from app.config.constants import CROP_COEFFICIENTS
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def compute_et0_penman_monteith(
    temperature: float,
    humidity: float,
    wind_speed: float,
    solar_radiation: Optional[float] = None,
    elevation: float = 500.0,
    latitude: float = 18.5,
    day_of_year: int = 180,
) -> float:
    """
    Compute reference evapotranspiration (ET₀) using FAO Penman-Monteith.

    Simplified FAO-56 equation:
        ET₀ = [0.408 × Δ(Rn - G) + γ × (900 / (T + 273)) × u2 × (es - ea)]
              / [Δ + γ(1 + 0.34 × u2)]

    When solar radiation is not available, it is estimated from
    temperature range and extraterrestrial radiation.

    Args:
        temperature: Mean air temperature (°C).
        humidity: Relative humidity (%).
        wind_speed: Wind speed at 2m height (m/s).
        solar_radiation: Incoming solar radiation (MJ/m²/day). Estimated if None.
        elevation: Station elevation (m).
        latitude: Station latitude (degrees).
        day_of_year: Julian day of year (1–365).

    Returns:
        Reference ET₀ in mm/day.
    """
    T = temperature
    RH = humidity / 100.0
    u2 = wind_speed

    # Atmospheric pressure (kPa)
    P = 101.3 * ((293.0 - 0.0065 * elevation) / 293.0) ** 5.26

    # Psychrometric constant (kPa/°C)
    gamma = 0.000665 * P

    # Saturation vapor pressure (kPa)
    es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))

    # Actual vapor pressure (kPa)
    ea = es * RH

    # Slope of saturation vapor pressure curve (kPa/°C)
    delta = (4098.0 * es) / ((T + 237.3) ** 2)

    # Solar radiation estimation if not provided
    if solar_radiation is None:
        # Estimate from Hargreaves radiation formula
        lat_rad = math.radians(latitude)
        dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
        solar_dec = 0.409 * math.sin(2.0 * math.pi * day_of_year / 365.0 - 1.39)
        ws = math.acos(-math.tan(lat_rad) * math.tan(solar_dec))

        # Extraterrestrial radiation (MJ/m²/day)
        Ra = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
            ws * math.sin(lat_rad) * math.sin(solar_dec)
            + math.cos(lat_rad) * math.cos(solar_dec) * math.sin(ws)
        )

        # Estimate solar radiation (Angstrom formula with default coefficients)
        T_range = 10.0  # Assumed daily temperature range
        Rs = 0.16 * math.sqrt(T_range) * Ra
        solar_radiation = max(Rs, 0.1)

    Rn = solar_radiation * 0.77  # Net radiation (simplified)
    G = 0.0  # Soil heat flux (negligible for daily calculations)

    # FAO Penman-Monteith equation
    numerator = (0.408 * delta * (Rn - G)
                 + gamma * (900.0 / (T + 273.0)) * u2 * (es - ea))
    denominator = delta + gamma * (1.0 + 0.34 * u2)

    et0 = numerator / denominator
    et0 = max(0.0, et0)

    logger.debug("ET₀ computed: %.2f mm/day (T=%.1f°C, RH=%.0f%%)", et0, T, humidity)
    return round(et0, 3)


def get_crop_coefficient(
    crop_type: str,
    growth_stage: str = "mid",
) -> float:
    """
    Look up crop coefficient (Kc) for a crop type and growth stage.

    Args:
        crop_type: Crop name (e.g., "wheat", "rice", "maize").
        growth_stage: Growth stage ("initial", "mid", "late").

    Returns:
        Kc value (dimensionless).
    """
    crop_lower = crop_type.lower().strip()
    coefficients = CROP_COEFFICIENTS.get(crop_lower, CROP_COEFFICIENTS["default"])

    stage_lower = growth_stage.lower().strip()
    if stage_lower not in coefficients:
        stage_lower = "mid"

    kc = coefficients[stage_lower]
    logger.debug("Kc for %s (%s): %.2f", crop_type, growth_stage, kc)
    return kc


def compute_crop_water_demand(
    temperature: float,
    humidity: float,
    wind_speed: float = 2.0,
    crop_type: str = "wheat",
    growth_stage: str = "mid",
    solar_radiation: Optional[float] = None,
) -> Dict[str, float]:
    """
    Compute crop water demand (ETc = Kc × ET₀).

    Args:
        temperature: Air temperature (°C).
        humidity: Relative humidity (%).
        wind_speed: Wind speed at 2m (m/s).
        crop_type: Crop type.
        growth_stage: Growth stage.
        solar_radiation: Solar radiation (MJ/m²/day).

    Returns:
        Dictionary with ET₀, Kc, and ETc values.
    """
    et0 = compute_et0_penman_monteith(
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        solar_radiation=solar_radiation,
    )
    kc = get_crop_coefficient(crop_type, growth_stage)
    etc = et0 * kc

    return {
        "et0_mm": round(et0, 3),
        "kc": round(kc, 3),
        "etc_mm": round(etc, 3),
        "crop_type": crop_type,
        "growth_stage": growth_stage,
    }


def compute_effective_rainfall(
    rainfall_mm: float,
    method: str = "usda",
) -> float:
    """
    Compute effective rainfall (rainfall actually usable by crops).

    Methods:
    - usda: USDA SCS method
    - fao: FAO fixed-percentage method

    Args:
        rainfall_mm: Total rainfall in mm.
        method: Calculation method.

    Returns:
        Effective rainfall in mm.
    """
    if rainfall_mm <= 0:
        return 0.0

    if method == "usda":
        # USDA SCS method
        if rainfall_mm <= 250:
            pe = rainfall_mm * (125.0 - 0.2 * rainfall_mm) / 125.0
        else:
            pe = 125.0 + 0.1 * rainfall_mm
    elif method == "fao":
        # FAO dependable rainfall (80% of total for P < 75mm)
        if rainfall_mm < 75:
            pe = 0.8 * rainfall_mm - 25.0
        else:
            pe = 0.6 * rainfall_mm - 10.0
        pe = max(0.0, pe)
    else:
        pe = rainfall_mm * 0.7  # Simple 70% effectiveness

    return round(max(0.0, pe), 2)


def soil_water_balance(
    initial_moisture: float,
    et_mm: float,
    rainfall_mm: float,
    irrigation_mm: float,
    field_capacity: float,
    wilting_point: float,
    root_depth_m: float = 0.6,
) -> Dict[str, float]:
    """
    Compute soil water balance for a single time step.

    Balance: θ_new = θ_old + (P_eff + I - ET) / (root_depth × 1000)

    Args:
        initial_moisture: Starting moisture (cm³/cm³).
        et_mm: Evapotranspiration (mm).
        rainfall_mm: Rainfall (mm).
        irrigation_mm: Applied irrigation (mm).
        field_capacity: Field capacity (cm³/cm³).
        wilting_point: Wilting point (cm³/cm³).
        root_depth_m: Root zone depth (m).

    Returns:
        Dictionary with new moisture state and balance components.
    """
    effective_rain = compute_effective_rainfall(rainfall_mm)
    depth_mm = root_depth_m * 1000.0  # Convert to mm

    # Water balance
    net_input_mm = effective_rain + irrigation_mm - et_mm
    moisture_change = net_input_mm / depth_mm

    new_moisture = initial_moisture + moisture_change
    new_moisture = max(wilting_point, min(new_moisture, field_capacity))

    # Deep percolation (excess above field capacity)
    percolation = max(0.0, (initial_moisture + moisture_change) - field_capacity) * depth_mm

    return {
        "new_moisture": round(new_moisture, 4),
        "moisture_change": round(moisture_change, 4),
        "effective_rainfall_mm": round(effective_rain, 2),
        "et_mm": round(et_mm, 2),
        "irrigation_mm": round(irrigation_mm, 2),
        "deep_percolation_mm": round(percolation, 2),
        "is_stress": new_moisture <= wilting_point + 0.02,
    }
