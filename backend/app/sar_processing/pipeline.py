"""
SAR Processing — Full Pipeline.

Orchestrates the complete SAR processing chain:
Raw SAR → Calibration → Speckle Filtering → Terrain Correction →
Moisture Inversion → Feature Extraction → Output Feature Vector.
"""

from typing import Any, Dict, Optional

import numpy as np

from app.core.logging_config import get_logger
from app.sar_processing.calibration import calibrate_from_db_values
from app.sar_processing.feature_extraction import (
    build_feature_vector,
    classify_vegetation_stage,
)
from app.sar_processing.moisture_inversion import (
    multi_polarization_moisture,
    water_cloud_model,
)

logger = get_logger(__name__)


class SARPipeline:
    """
    Complete SAR processing pipeline.

    Processes raw or pre-calibrated SAR data through the full chain
    and produces a feature vector ready for ML model input.

    Usage:
        pipeline = SARPipeline()
        result = pipeline.process(
            vv_db=-12.5, vh_db=-18.3, ndvi=0.65,
            temperature=28.0, humidity=55.0, rainfall=5.0,
            sand_pct=40.0, clay_pct=25.0, silt_pct=35.0,
        )
    """

    def __init__(
        self,
        use_refined_lee: bool = False,
        speckle_window: int = 7,
        moisture_method: str = "wcm",
    ):
        """
        Initialize the SAR processing pipeline.

        Args:
            use_refined_lee: Use Refined Lee filter instead of standard Lee.
            speckle_window: Speckle filter window size.
            moisture_method: Moisture inversion method ("wcm" or "change_detection").
        """
        self.use_refined_lee = use_refined_lee
        self.speckle_window = speckle_window
        self.moisture_method = moisture_method
        logger.info(
            "SAR Pipeline initialized — filter=%s, window=%d, method=%s",
            "refined_lee" if use_refined_lee else "lee",
            speckle_window,
            moisture_method,
        )

    def process(
        self,
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
        incidence_angle: float = 38.0,
    ) -> Dict[str, Any]:
        """
        Run the complete SAR processing pipeline on a single observation.

        Steps:
        1. Calibration — validate/normalize backscatter values
        2. (Speckle filtering — applied only to raster data, skipped for point values)
        3. (Terrain correction — applied only to raster data, skipped for point values)
        4. Moisture inversion — convert backscatter to soil moisture
        5. Feature extraction — build complete feature vector

        Args:
            vv_db: VV polarization backscatter (dB).
            vh_db: VH polarization backscatter (dB).
            ndvi: NDVI value.
            temperature: Air temperature (°C).
            humidity: Relative humidity (%).
            rainfall: Daily precipitation (mm).
            sand_pct: Sand percentage.
            clay_pct: Clay percentage.
            silt_pct: Silt percentage.
            elevation: Elevation (m).
            wind_speed: Wind speed (m/s).
            et0: Reference ET₀ (mm/day).
            ndwi: NDWI value.
            organic_matter: Organic matter (%).
            field_capacity: Field capacity (cm³/cm³).
            wilting_point: Wilting point (cm³/cm³).
            slope: Terrain slope (degrees).
            aspect: Terrain aspect (degrees).
            incidence_angle: SAR incidence angle (degrees).

        Returns:
            Dictionary containing:
                - features: Complete feature vector for ML model
                - moisture: Moisture estimation results
                - vegetation_stage: Classified vegetation stage
                - processing_steps: List of steps applied
                - metadata: Processing metadata
        """
        logger.info("Starting SAR pipeline processing")
        processing_steps = []

        # Step 1: Radiometric Calibration
        vv_cal, vh_cal = calibrate_from_db_values(vv_db, vh_db)
        processing_steps.append("radiometric_calibration")

        # Step 2: Speckle Filtering (for point data, just pass through)
        # In production with raster data, apply_speckle_filter() would be called
        processing_steps.append("speckle_filtering_passthrough")

        # Step 3: Terrain Correction (for point data, just pass through)
        # In production with raster data, apply_terrain_correction() would be called
        processing_steps.append("terrain_correction_passthrough")

        # Step 4: Moisture Inversion
        moisture_results = multi_polarization_moisture(
            vv_db=vv_cal,
            vh_db=vh_cal,
            ndvi=ndvi,
            method=self.moisture_method,
        )
        processing_steps.append("moisture_inversion")

        # Step 5: Feature Extraction
        features = build_feature_vector(
            vv_db=vv_cal,
            vh_db=vh_cal,
            ndvi=ndvi,
            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,
            sand_pct=sand_pct,
            clay_pct=clay_pct,
            silt_pct=silt_pct,
            elevation=elevation,
            wind_speed=wind_speed,
            et0=et0,
            ndwi=ndwi,
            organic_matter=organic_matter,
            field_capacity=field_capacity,
            wilting_point=wilting_point,
            slope=slope,
            aspect=aspect,
        )
        processing_steps.append("feature_extraction")

        # Classify vegetation stage
        veg_stage = classify_vegetation_stage(ndvi)

        result = {
            "features": features,
            "moisture": moisture_results,
            "vegetation_stage": veg_stage,
            "processing_steps": processing_steps,
            "metadata": {
                "pipeline_version": "1.0.0",
                "moisture_method": self.moisture_method,
                "incidence_angle": incidence_angle,
                "feature_count": len(features),
            },
        }

        logger.info(
            "SAR pipeline complete — moisture=%.3f, confidence=%.2f, stage=%s",
            moisture_results["moisture_combined"],
            moisture_results["confidence"],
            veg_stage,
        )

        return result

    def process_batch(
        self,
        observations: list,
    ) -> list:
        """
        Process a batch of SAR observations.

        Args:
            observations: List of dictionaries, each containing the same
                          keyword arguments as process().

        Returns:
            List of processing results.
        """
        logger.info("Processing batch of %d observations", len(observations))
        results = []
        for i, obs in enumerate(observations):
            try:
                result = self.process(**obs)
                results.append(result)
            except Exception as e:
                logger.error("Failed to process observation %d: %s", i, str(e))
                results.append({"error": str(e), "index": i})
        return results


# Module-level convenience instance
default_pipeline = SARPipeline()
