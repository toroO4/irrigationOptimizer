"""
ML Pipeline — Training Orchestrator.

Manages the complete training lifecycle:
dataset loading → preprocessing → model training → evaluation → saving.
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from app.core.config import settings
from app.core.logging_config import get_logger
from app.ml.dataset_loader import DatasetLoader
from app.ml.evaluator import evaluate_model
from app.ml.model_registry import get_model

logger = get_logger(__name__)


class Trainer:
    """
    Model training orchestrator.

    Handles the full pipeline from raw data to a saved, evaluated model.

    Usage:
        trainer = Trainer(model_name="random_forest")
        result = trainer.train_from_file("datasets/soil_moisture.csv")
    """

    def __init__(
        self,
        model_name: str = "random_forest",
        target_column: str = "soil_moisture",
        scaler_type: str = "standard",
        test_size: float = 0.15,
        val_size: float = 0.15,
        tune_hyperparams: bool = False,
    ):
        self.model_name = model_name
        self.target_column = target_column
        self.scaler_type = scaler_type
        self.test_size = test_size
        self.val_size = val_size
        self.tune_hyperparams = tune_hyperparams
        self.model = None
        self.loader = DatasetLoader(
            target_column=target_column,
            test_size=test_size,
            val_size=val_size,
            scaler_type=scaler_type,
        )
        logger.info("Trainer initialized — model=%s, target=%s", model_name, target_column)

    def train_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Train a model from a dataset file.

        Args:
            file_path: Path to the CSV/Excel/JSON dataset.

        Returns:
            Dictionary containing training results, metrics, and file paths.
        """
        start_time = time.time()
        logger.info("Starting training pipeline from file: %s", file_path)

        # Step 1: Load and prepare data
        data = self.loader.load_and_prepare(file_path)
        X_train, X_val, X_test, y_train, y_val, y_test = data["splits"]
        feature_names = data["feature_names"]

        # Step 2: Initialize model
        self.model = get_model(self.model_name)

        # Step 3: Train
        if self.tune_hyperparams and hasattr(self.model, "train_with_tuning"):
            train_metrics = self.model.train_with_tuning(X_train, y_train, feature_names)
        else:
            train_metrics = self.model.train(X_train, y_train, feature_names)

        # Step 4: Evaluate on validation and test sets
        val_metrics = evaluate_model(self.model, X_val, y_val, dataset_name="validation")
        test_metrics = evaluate_model(self.model, X_test, y_test, dataset_name="test")

        # Step 5: Save model
        model_path = self.model.save()

        # Step 6: Save scaler
        scaler_path = self._save_scaler(data["scaler"])

        duration = time.time() - start_time

        result = {
            "model_name": self.model_name,
            "model_path": model_path,
            "scaler_path": scaler_path,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "training_duration_seconds": round(duration, 2),
            "dataset_info": {
                "file": file_path,
                "total_samples": len(y_train) + len(y_val) + len(y_test),
                "train_samples": len(y_train),
                "val_samples": len(y_val),
                "test_samples": len(y_test),
                "features": len(feature_names),
            },
            "train_metrics": train_metrics,
            "validation_metrics": val_metrics,
            "test_metrics": test_metrics,
            "feature_importance": self.model.get_feature_importance(top_n=10),
            "validation_report": data["validation_report"],
        }

        logger.info(
            "Training pipeline complete — duration=%.1fs, test_RMSE=%.4f",
            duration, test_metrics.get("rmse", 0),
        )

        return result

    def train_from_arrays(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Train from pre-prepared numpy arrays.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_val: Validation features.
            y_val: Validation targets.
            feature_names: Feature name list.

        Returns:
            Training result dictionary.
        """
        start_time = time.time()
        self.model = get_model(self.model_name)
        train_metrics = self.model.train(X_train, y_train, feature_names)
        val_metrics = evaluate_model(self.model, X_val, y_val, dataset_name="validation")
        model_path = self.model.save()
        duration = time.time() - start_time

        return {
            "model_name": self.model_name,
            "model_path": model_path,
            "training_duration_seconds": round(duration, 2),
            "train_metrics": train_metrics,
            "validation_metrics": val_metrics,
            "feature_importance": self.model.get_feature_importance(),
        }

    def _save_scaler(self, scaler) -> str:
        """Save the fitted scaler to disk."""
        import joblib
        model_dir = Path(settings.model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        scaler_path = str(model_dir / "scaler.joblib")
        joblib.dump(scaler, scaler_path)
        logger.info("Scaler saved to: %s", scaler_path)
        return scaler_path
