"""
ML Model — XGBoost.

Modular XGBoost implementation with the same interface as RandomForestModel.
Drop-in replacement for ensemble gradient boosting.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not installed — XGBoostModel will not be available")


class XGBoostModel:
    """
    XGBoost classifier for irrigation prediction.

    Provides the same interface as RandomForestModel for seamless
    swapping via the model registry.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 8,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
    ):
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is not installed. Run: pip install xgboost")

        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            n_jobs=-1,
            verbosity=0,
        )
        self.is_trained = False
        self.feature_importances: Dict[str, float] = {}
        self.feature_names: List[str] = []
        self.best_params: Dict[str, Any] = {}
        logger.info("XGBoost model initialized — n_estimators=%d, lr=%.3f", n_estimators, learning_rate)

    def train(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: Optional[List[str]] = None) -> Dict[str, float]:
        """Train the XGBoost model."""
        logger.info("Training XGBoost — samples=%d, features=%d", X_train.shape[0], X_train.shape[1])
        self.model.fit(X_train, y_train)
        self.is_trained = True

        if feature_names:
            self.feature_names = feature_names
            self.feature_importances = dict(zip(feature_names, self.model.feature_importances_))

        metrics = {"train_accuracy": float(self.model.score(X_train, y_train))}
        logger.info("XGBoost training complete — Accuracy=%.4f", metrics["train_accuracy"])
        return metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before predictions")
        predictions = self.model.predict(X)
        return predictions

    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with estimated confidence (based on prediction variance)."""
        predictions = self.predict(X)
        probabilities = self.model.predict_proba(X)
        confidence = np.max(probabilities, axis=1)
        return predictions, confidence

    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get top feature importances."""
        if not self.feature_importances:
            return []
        sorted_features = sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)
        return sorted_features[:top_n]

    def save(self, file_path: Optional[str] = None) -> str:
        """Save model to disk."""
        if file_path is None:
            model_dir = Path(settings.model_dir)
            model_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(model_dir / "xgboost.joblib")
        joblib.dump({"model": self.model, "feature_names": self.feature_names, "feature_importances": self.feature_importances}, file_path)
        logger.info("XGBoost model saved to: %s", file_path)
        return file_path

    def load(self, file_path: Optional[str] = None) -> None:
        """Load model from disk."""
        if file_path is None:
            file_path = str(Path(settings.model_dir) / "xgboost.joblib")
        data = joblib.load(file_path)
        self.model = data["model"]
        self.feature_names = data.get("feature_names", [])
        self.feature_importances = data.get("feature_importances", {})
        self.is_trained = True
        logger.info("XGBoost model loaded from: %s", file_path)
