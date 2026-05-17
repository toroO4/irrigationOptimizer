"""
Service — Prediction Operations.

Handles soil moisture prediction using trained ML models
combined with SAR processing pipeline.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np

from app.core.config import settings
from app.core.logging_config import get_logger
from app.ml.model_registry import load_trained_model
from app.sar_processing.pipeline import SARPipeline

logger = get_logger(__name__)


class PredictionService:
    """Manages soil moisture predictions using trained models and SAR pipeline."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.pipeline = SARPipeline()
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load a pre-trained model and scaler."""
        model_dir = Path(settings.model_dir)
        model_file = model_dir / "random_forest.joblib"
        scaler_file = model_dir / "scaler.joblib"

        if model_file.exists():
            try:
                self.model = load_trained_model("random_forest", str(model_file))
                logger.info("Pre-trained model loaded")
            except Exception as e:
                logger.warning("Failed to load model: %s", str(e))

        if scaler_file.exists():
            try:
                self.scaler = joblib.load(str(scaler_file))
                logger.info("Scaler loaded")
            except Exception as e:
                logger.warning("Failed to load scaler: %s", str(e))

    async def predict(
        self,
        vv_backscatter: float,
        vh_backscatter: float,
        ndvi: float,
        temperature: float,
        humidity: float,
        rainfall: float = 0.0,
        wind_speed: float = 2.0,
        sand_pct: float = 40.0,
        clay_pct: float = 25.0,
        silt_pct: float = 35.0,
        elevation: float = 500.0,
        organic_matter: float = 2.5,
        field_capacity: float = 0.30,
        wilting_point: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Predict soil moisture for given input features.

        Runs the SAR processing pipeline and then applies the
        trained ML model for prediction.

        Returns:
            Prediction result dictionary.
        """
        # Run SAR pipeline
        pipeline_result = self.pipeline.process(
            vv_db=vv_backscatter, vh_db=vh_backscatter, ndvi=ndvi,
            temperature=temperature, humidity=humidity, rainfall=rainfall,
            sand_pct=sand_pct, clay_pct=clay_pct, silt_pct=silt_pct,
            elevation=elevation, wind_speed=wind_speed,
            organic_matter=organic_matter, field_capacity=field_capacity,
            wilting_point=wilting_point,
        )

        features = pipeline_result["features"]
        sar_moisture = pipeline_result["moisture"]

        # Use ML model if available, otherwise use SAR-derived moisture
        if self.model is not None:
            feature_array = np.array([list(features.values())])
            if self.scaler is not None:
                feature_array = self.scaler.transform(feature_array)
            predictions, confidence = self.model.predict_with_confidence(feature_array)
            predicted_moisture = float(predictions[0])
            pred_confidence = float(confidence[0])
            model_name = settings.default_model
        else:
            predicted_moisture = sar_moisture["moisture_combined"]
            pred_confidence = sar_moisture["confidence"]
            model_name = "sar_pipeline_only"

        return {
            "predicted_moisture": round(predicted_moisture, 4),
            "confidence": round(pred_confidence, 3),
            "model_name": model_name,
            "sar_moisture": sar_moisture,
            "vegetation_stage": pipeline_result["vegetation_stage"],
            "features_used": len(features),
            "processing_steps": pipeline_result["processing_steps"],
        }

    def is_model_loaded(self) -> bool:
        """Check if a trained model is loaded."""
        return self.model is not None

    def reload_model(self) -> None:
        """Reload the model from disk (after retraining)."""
        self._load_model()


# Singleton
prediction_service = PredictionService()
