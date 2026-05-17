"""
Service — Training Operations.

Orchestrates model training from API requests.
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging_config import get_logger
from app.ml.trainer import Trainer
from app.services.dataset_service import dataset_service

logger = get_logger(__name__)


class TrainingService:
    """Manages model training lifecycle from API layer."""

    def __init__(self):
        self.last_training_result: Optional[Dict[str, Any]] = None
        self.is_training = False

    async def train_model(
        self,
        model_name: str = "random_forest",
        dataset_path: Optional[str] = None,
        target_column: str = "soil_moisture",
        test_size: float = 0.15,
        tune_hyperparams: bool = False,
    ) -> Dict[str, Any]:
        """
        Train a model from a dataset file.

        Args:
            model_name: Model type to train.
            dataset_path: Path to dataset. Uses latest upload if None.
            target_column: Target variable column name.
            test_size: Test set fraction.
            tune_hyperparams: Enable hyperparameter tuning.

        Returns:
            Training results dictionary.
        """
        if self.is_training:
            raise RuntimeError("A training job is already in progress")

        # Resolve dataset path
        if dataset_path is None:
            dataset_path = dataset_service.get_latest_upload_path()
            if dataset_path is None:
                # Use synthetic data
                from scripts.generate_synthetic_data import generate_and_save
                dataset_path = generate_and_save()
                logger.info("No dataset found — using generated synthetic data: %s", dataset_path)

        self.is_training = True
        try:
            trainer = Trainer(
                model_name=model_name,
                target_column=target_column,
                test_size=test_size,
                tune_hyperparams=tune_hyperparams,
            )
            result = trainer.train_from_file(dataset_path)
            result["message"] = f"Model '{model_name}' trained successfully"
            self.last_training_result = result
            return result

        except Exception as e:
            logger.error("Training failed: %s", str(e))
            raise
        finally:
            self.is_training = False

    async def retrain(self, model_name: str = "random_forest") -> Dict[str, Any]:
        """Retrain with the latest dataset."""
        return await self.train_model(model_name=model_name)

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """Get the results from the last training run."""
        return self.last_training_result


# Singleton
training_service = TrainingService()
