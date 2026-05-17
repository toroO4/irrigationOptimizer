"""
Irrigation Scheduling — Pump Runtime Calculator.

Computes pump runtime, water volume, and energy consumption
based on irrigation deficit, field area, and pump specifications.
"""

from typing import Dict

from app.config.constants import DEFAULT_PIPE_LOSS_FRACTION, DEFAULT_PUMP_POWER_KW
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def calculate_pump_runtime(
    deficit_mm: float,
    area_hectares: float,
    pump_flow_rate_lph: float,
    system_efficiency: float = 0.75,
    pipe_loss_fraction: float = DEFAULT_PIPE_LOSS_FRACTION,
    pump_power_kw: float = DEFAULT_PUMP_POWER_KW,
) -> Dict[str, float]:
    """
    Calculate pump runtime and water requirements.

    Formula:
        water_needed = deficit_mm × area_m² / 1000  (liters)
        gross_water = water_needed / (efficiency × (1 - pipe_loss))
        runtime = gross_water / pump_flow_rate

    Args:
        deficit_mm: Soil moisture deficit in millimeters.
        area_hectares: Field area in hectares.
        pump_flow_rate_lph: Pump capacity in liters per hour.
        system_efficiency: Irrigation system efficiency (0–1).
        pipe_loss_fraction: Conveyance loss fraction (0–1).
        pump_power_kw: Pump motor power in kilowatts.

    Returns:
        Dictionary with:
            - water_volume_liters: Total water needed (liters)
            - water_volume_m3: Total water needed (cubic meters)
            - pump_runtime_hours: Required pump runtime (hours)
            - energy_kwh: Estimated energy consumption (kWh)
            - gross_application_mm: Total water applied per unit area (mm)
    """
    if deficit_mm <= 0:
        return {
            "water_volume_liters": 0.0,
            "water_volume_m3": 0.0,
            "pump_runtime_hours": 0.0,
            "energy_kwh": 0.0,
            "gross_application_mm": 0.0,
        }

    # Convert area to square meters (1 hectare = 10,000 m²)
    area_m2 = area_hectares * 10_000

    # Net water requirement (liters)
    # 1 mm of water over 1 m² = 1 liter
    net_water_liters = deficit_mm * area_m2

    # Account for system efficiency and pipe losses
    effective_efficiency = system_efficiency * (1.0 - pipe_loss_fraction)
    effective_efficiency = max(effective_efficiency, 0.1)  # Safety floor

    # Gross water requirement
    gross_water_liters = net_water_liters / effective_efficiency

    # Pump runtime
    if pump_flow_rate_lph <= 0:
        logger.error("Invalid pump flow rate: %.1f LPH", pump_flow_rate_lph)
        pump_flow_rate_lph = 5000.0

    runtime_hours = gross_water_liters / pump_flow_rate_lph

    # Energy consumption
    energy_kwh = runtime_hours * pump_power_kw

    # Gross application rate (mm applied over the field)
    gross_application_mm = gross_water_liters / area_m2

    result = {
        "water_volume_liters": round(gross_water_liters, 1),
        "water_volume_m3": round(gross_water_liters / 1000, 3),
        "pump_runtime_hours": round(runtime_hours, 3),
        "energy_kwh": round(energy_kwh, 2),
        "gross_application_mm": round(gross_application_mm, 2),
    }

    logger.debug(
        "Pump calculation — deficit=%.1fmm, area=%.2fha, runtime=%.2fh, water=%.0fL",
        deficit_mm, area_hectares, runtime_hours, gross_water_liters,
    )

    return result


def estimate_cost(
    energy_kwh: float,
    electricity_rate: float = 5.0,
    water_rate_per_m3: float = 0.0,
) -> Dict[str, float]:
    """
    Estimate the cost of an irrigation event.

    Args:
        energy_kwh: Energy consumption in kWh.
        electricity_rate: Cost per kWh in local currency.
        water_rate_per_m3: Water cost per cubic meter (if applicable).

    Returns:
        Cost breakdown dictionary.
    """
    electricity_cost = energy_kwh * electricity_rate

    return {
        "electricity_cost": round(electricity_cost, 2),
        "total_cost": round(electricity_cost, 2),
        "currency": "INR",
    }
