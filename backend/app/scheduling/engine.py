"""
Irrigation Scheduling — Core Engine.

Implements the core scheduling logic:
    if moisture < threshold:
        deficit = field_capacity - current_moisture
        runtime = deficit / (pump_flow_rate × efficiency)
        generate_schedule()
    else:
        no_irrigation()

With drought severity classification, urgency levels, and scheduling windows.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.config.constants import (
    DROUGHT_CLASSES,
    IRRIGATION_EFFICIENCY,
    MAD_THRESHOLD,
    URGENCY_LEVELS,
)
from app.core.logging_config import get_logger
from app.scheduling.pump_calculator import calculate_pump_runtime
from app.scheduling.water_balance import compute_crop_water_demand

logger = get_logger(__name__)


class IrrigationScheduler:
    """
    Irrigation scheduling engine.

    Takes soil moisture predictions and field parameters, then
    generates actionable irrigation schedules with pump runtime,
    water volume, and urgency classification.
    """

    def __init__(self, mad_threshold: float = MAD_THRESHOLD):
        """
        Initialize the scheduler.

        Args:
            mad_threshold: Management Allowable Depletion threshold (fraction).
                          Irrigation is triggered when moisture falls below
                          wilting_point + (1 - MAD) × AWC.
        """
        self.mad_threshold = mad_threshold
        logger.info("IrrigationScheduler initialized — MAD=%.2f", mad_threshold)

    def generate_schedule(
        self,
        current_moisture: float,
        field_capacity: float,
        wilting_point: float,
        area_hectares: float,
        crop_type: str = "wheat",
        irrigation_type: str = "drip",
        pump_flow_rate_lph: float = 5000.0,
        temperature: float = 30.0,
        humidity: float = 50.0,
        wind_speed: float = 2.0,
        rainfall_forecast: float = 0.0,
        root_depth_m: float = 0.6,
        growth_stage: str = "mid",
    ) -> Dict[str, Any]:
        """
        Generate an irrigation schedule for a field.

        Core logic:
            AWC = field_capacity - wilting_point
            threshold = wilting_point + (1 - MAD) × AWC
            if current_moisture < threshold:
                deficit = field_capacity - current_moisture
                → compute pump runtime, water volume, schedule

        Args:
            current_moisture: Current soil moisture (cm³/cm³).
            field_capacity: Field capacity (cm³/cm³).
            wilting_point: Wilting point (cm³/cm³).
            area_hectares: Field area in hectares.
            crop_type: Crop type for Kc lookup.
            irrigation_type: System type (drip, sprinkler, flood).
            pump_flow_rate_lph: Pump flow rate in liters per hour.
            temperature: Air temperature (°C).
            humidity: Relative humidity (%).
            wind_speed: Wind speed (m/s).
            rainfall_forecast: Expected rainfall in next 24h (mm).
            root_depth_m: Root zone depth (meters).
            growth_stage: Crop growth stage (initial, mid, late).

        Returns:
            Comprehensive irrigation schedule dictionary.
        """
        logger.info(
            "Generating schedule — moisture=%.3f, FC=%.3f, WP=%.3f, crop=%s",
            current_moisture, field_capacity, wilting_point, crop_type,
        )

        # Calculate Available Water Capacity
        awc = field_capacity - wilting_point

        # Calculate irrigation trigger threshold
        # Threshold = WP + (1 - MAD) × AWC
        threshold = wilting_point + (1.0 - self.mad_threshold) * awc

        # Determine urgency
        urgency = self._classify_urgency(current_moisture, field_capacity, wilting_point)

        # Classify drought severity
        drought_class = self._classify_drought(current_moisture, field_capacity, wilting_point)

        # Compute crop water demand (ETc)
        crop_demand = compute_crop_water_demand(
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            crop_type=crop_type,
            growth_stage=growth_stage,
        )

        # Check if irrigation is needed
        if current_moisture < threshold:
            # IRRIGATION NEEDED
            deficit_fraction = field_capacity - current_moisture  # cm³/cm³
            deficit_mm = deficit_fraction * root_depth_m * 1000  # Convert to mm

            # Account for forecasted rainfall
            effective_deficit_mm = max(0.0, deficit_mm - rainfall_forecast * 0.8)

            # Get system efficiency
            efficiency = IRRIGATION_EFFICIENCY.get(irrigation_type, 0.75)

            # Calculate pump runtime and water volume
            pump_result = calculate_pump_runtime(
                deficit_mm=effective_deficit_mm,
                area_hectares=area_hectares,
                pump_flow_rate_lph=pump_flow_rate_lph,
                system_efficiency=efficiency,
            )

            # Determine scheduling window
            schedule_time = self._determine_schedule_time(urgency)

            schedule = {
                "irrigation_needed": True,
                "urgency": urgency,
                "drought_class": drought_class,
                "current_moisture": round(current_moisture, 4),
                "threshold_moisture": round(threshold, 4),
                "target_moisture": round(field_capacity, 4),
                "deficit_mm": round(effective_deficit_mm, 2),
                "raw_deficit_mm": round(deficit_mm, 2),
                "rainfall_adjustment_mm": round(rainfall_forecast * 0.8, 2),
                "water_volume_liters": round(pump_result["water_volume_liters"], 1),
                "water_volume_m3": round(pump_result["water_volume_m3"], 3),
                "pump_runtime_hours": round(pump_result["pump_runtime_hours"], 2),
                "pump_runtime_minutes": round(pump_result["pump_runtime_hours"] * 60, 1),
                "irrigation_type": irrigation_type,
                "system_efficiency": efficiency,
                "scheduled_time": schedule_time.isoformat(),
                "crop_water_demand_mm": round(crop_demand["etc_mm"], 2),
                "et0_mm": round(crop_demand["et0_mm"], 2),
                "energy_estimate_kwh": round(pump_result["energy_kwh"], 2),
                "recommendation": self._generate_recommendation(urgency, effective_deficit_mm, irrigation_type),
            }
        else:
            # NO IRRIGATION NEEDED
            schedule = {
                "irrigation_needed": False,
                "urgency": "none",
                "drought_class": drought_class,
                "current_moisture": round(current_moisture, 4),
                "threshold_moisture": round(threshold, 4),
                "target_moisture": round(field_capacity, 4),
                "deficit_mm": 0.0,
                "water_volume_liters": 0.0,
                "pump_runtime_hours": 0.0,
                "irrigation_type": irrigation_type,
                "crop_water_demand_mm": round(crop_demand["etc_mm"], 2),
                "recommendation": "No irrigation needed. Soil moisture is adequate.",
            }

        logger.info(
            "Schedule generated — needed=%s, urgency=%s, deficit=%.1fmm",
            schedule["irrigation_needed"], schedule["urgency"], schedule.get("deficit_mm", 0),
        )

        return schedule

    def generate_multi_field_plan(
        self,
        fields: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate irrigation plans for multiple fields.

        Args:
            fields: List of field dictionaries with parameters.

        Returns:
            Aggregated irrigation plan with per-field schedules.
        """
        logger.info("Generating multi-field plan for %d fields", len(fields))
        schedules = []
        total_water = 0.0
        total_runtime = 0.0
        fields_needing_irrigation = 0

        for field in fields:
            schedule = self.generate_schedule(**field)
            schedule["field_name"] = field.get("field_name", f"Field-{len(schedules) + 1}")
            schedules.append(schedule)

            if schedule["irrigation_needed"]:
                fields_needing_irrigation += 1
                total_water += schedule["water_volume_liters"]
                total_runtime += schedule["pump_runtime_hours"]

        plan = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_fields": len(fields),
            "fields_needing_irrigation": fields_needing_irrigation,
            "total_water_liters": round(total_water, 1),
            "total_water_m3": round(total_water / 1000, 3),
            "total_pump_runtime_hours": round(total_runtime, 2),
            "schedules": schedules,
        }

        return plan

    def _classify_urgency(self, moisture: float, fc: float, wp: float) -> str:
        """Classify irrigation urgency based on moisture level."""
        awc = fc - wp
        if awc <= 0:
            return "none"

        # Moisture as fraction of AWC
        awc_fraction = (moisture - wp) / awc
        awc_fraction = max(0.0, min(awc_fraction, 1.0))

        for level, threshold in sorted(URGENCY_LEVELS.items(), key=lambda x: x[1]):
            if awc_fraction <= threshold:
                return level
        return "none"

    def _classify_drought(self, moisture: float, fc: float, wp: float) -> Dict[str, str]:
        """Classify drought severity based on moisture level."""
        awc = fc - wp
        if awc <= 0:
            return {"class": "none", "label": "Normal"}

        moisture_pct = ((moisture - wp) / awc) * 100
        moisture_pct = max(0.0, min(moisture_pct, 100.0))

        for code, info in sorted(DROUGHT_CLASSES.items(), key=lambda x: x[1]["moisture_pct"]):
            if moisture_pct <= info["moisture_pct"]:
                return {"class": code, "label": info["label"]}

        return {"class": "none", "label": "Normal Conditions"}

    def _determine_schedule_time(self, urgency: str) -> datetime:
        """Determine optimal scheduling time based on urgency."""
        now = datetime.now(timezone.utc)

        if urgency == "critical":
            return now  # Immediate
        elif urgency == "high":
            return now + timedelta(hours=6)
        elif urgency == "moderate":
            # Schedule for next early morning (6 AM)
            next_morning = now.replace(hour=6, minute=0, second=0)
            if next_morning <= now:
                next_morning += timedelta(days=1)
            return next_morning
        else:
            return now + timedelta(days=1)

    def _generate_recommendation(self, urgency: str, deficit_mm: float, system: str) -> str:
        """Generate a human-readable irrigation recommendation."""
        if urgency == "critical":
            return f"CRITICAL: Immediate irrigation required. Apply {deficit_mm:.1f}mm via {system} system."
        elif urgency == "high":
            return f"HIGH PRIORITY: Irrigate within 6 hours. Deficit: {deficit_mm:.1f}mm."
        elif urgency == "moderate":
            return f"Schedule irrigation within 24 hours. Deficit: {deficit_mm:.1f}mm via {system}."
        else:
            return f"Low priority irrigation. Deficit: {deficit_mm:.1f}mm. Can be deferred."
