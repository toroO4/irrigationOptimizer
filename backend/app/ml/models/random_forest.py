"""
ML Model — Random Forest.

Primary model implementation for soil moisture prediction.
Uses scikit-learn's RandomForestRegressor with hyperparameter
tuning via GridSearchCV.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RandomForestModel:
    """
    Random Forest model for soil moisture prediction.

    Provides training, prediction, evaluation, and persistence
    with optional hyperparameter tuning.

    Attributes:
        model: The underlying sklearn RandomForestClassifier.
        is_trained: Whether the model has been trained.
        feature_importances: Feature importance scores after training.
        best_params: Best hyperparameters from grid search.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: Optional[int] = 15,
        min_samples_split: int = 5,
        min_samples_leaf: int = 2,
        max_features: str = "sqrt",
        random_state: int = 42,
        n_jobs: int = -1,
    ):
        """
        Initialize the Random Forest model.

        Args:
            n_estimators: Number of trees in the forest.
            max_depth: Maximum depth of each tree (None = unlimited).
            min_samples_split: Minimum samples to split a node.
            min_samples_leaf: Minimum samples at a leaf node.
            max_features: Feature selection strategy per split.
            random_state: Random seed for reproducibility.
            n_jobs: Number of parallel jobs (-1 = all cores).
        """
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            random_state=random_state,
            n_jobs=n_jobs,
            verbose=0,
        )
        self.is_trained = False
        self.feature_importances: Dict[str, float] = {}
        self.best_params: Dict[str, Any] = {}
        self.feature_names: List[str] = []
        logger.info("RandomForest model initialized — n_estimators=%d, max_depth=%s", n_estimators, max_depth)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Train the Random Forest model.

        Args:
            X_train: Training feature matrix.
            y_train: Training target values.
            feature_names: Optional list of feature names for importance tracking.

        Returns:
            Dictionary with training metrics (Accuracy).
        """
        logger.info("Training Random Forest — samples=%d, features=%d", X_train.shape[0], X_train.shape[1])

        self.model.fit(X_train, y_train)
        self.is_trained = True

        if feature_names:
            self.feature_names = feature_names
            self.feature_importances = dict(
                zip(feature_names, self.model.feature_importances_)
            )

        # Cross-validation score (RMSE)
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring="neg_mean_squared_error")
        rmse_scores = np.sqrt(-cv_scores)

        preds = self.model.predict(X_train)
        
        metrics = {
            "train_rmse": float(np.sqrt(mean_squared_error(y_train, preds))),
            "cv_rmse_mean": float(rmse_scores.mean()),
            "cv_rmse_std": float(rmse_scores.std()),
        }

        logger.info("Training complete — RMSE=%.4f, CV_RMSE=%.4f±%.4f", metrics["train_rmse"], metrics["cv_rmse_mean"], metrics["cv_rmse_std"])
        return metrics

    def train_with_tuning(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Train with hyperparameter tuning via GridSearchCV.

        Args:
            X_train: Training feature matrix.
            y_train: Training target values.
            feature_names: Optional feature names.

        Returns:
            Dictionary with best parameters and metrics.
        """
        logger.info("Starting hyperparameter tuning...")

        param_grid = {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 15, 20, None],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
        }

        grid_search = GridSearchCV(
            estimator=self.model,
            param_grid=param_grid,
            cv=5,
            scoring="neg_mean_squared_error",
            n_jobs=-1,
            verbose=0,
        )
        grid_search.fit(X_train, y_train)

        self.model = grid_search.best_estimator_
        self.best_params = grid_search.best_params_
        self.is_trained = True

        if feature_names:
            self.feature_names = feature_names
            self.feature_importances = dict(
                zip(feature_names, self.model.feature_importances_)
            )

        logger.info("Tuning complete — best_params=%s, best_rmse=%.4f", self.best_params, np.sqrt(-grid_search.best_score_))

        return {
            "best_params": self.best_params,
            "best_rmse": float(np.sqrt(-grid_search.best_score_)),
            "cv_results_mean": float(np.mean(np.sqrt(-grid_search.cv_results_["mean_test_score"]))),
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: Feature matrix for prediction.

        Returns:
            Array of predicted classes.

        Raises:
            RuntimeError: If the model has not been trained.
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before making predictions")

        predictions = self.model.predict(X)
        return predictions

    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions with confidence intervals.

        Uses individual tree predictions to estimate uncertainty.

        Args:
            X: Feature matrix.

        Returns:
            Tuple of (predictions, confidence_scores).
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before making predictions")

        predictions = self.model.predict(X)
        
        # For regressors, confidence could be derived from standard deviation of individual tree predictions
        all_tree_preds = np.stack([tree.predict(X) for tree in self.model.estimators_])
        std_devs = np.std(all_tree_preds, axis=0)
        
        # Max moisture is typically 100, so we can convert std to a rough confidence %
        # Assuming higher std = lower confidence
        confidence = 100.0 - (std_devs * 100.0 / 30.0) # 30 is roughly max expected error
        confidence = np.clip(confidence, 0, 100)

        return predictions, confidence

    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top-N most important features.

        Args:
            top_n: Number of top features to return.

        Returns:
            List of (feature_name, importance) tuples sorted by importance.
        """
        if not self.feature_importances:
            return []

        sorted_features = sorted(
            self.feature_importances.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_features[:top_n]

    def save(self, file_path: Optional[str] = None) -> str:
        """
        Save the trained model to disk.

        Args:
            file_path: Optional path. Defaults to model_dir/random_forest.joblib.

        Returns:
            Path where the model was saved.
        """
        if file_path is None:
            model_dir = Path(settings.model_dir)
            model_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(model_dir / "random_forest.joblib")

        joblib.dump(
            {
                "model": self.model,
                "feature_names": self.feature_names,
                "feature_importances": self.feature_importances,
                "best_params": self.best_params,
            },
            file_path,
        )
        logger.info("Model saved to: %s", file_path)
        return file_path

    def load(self, file_path: Optional[str] = None) -> None:
        """
        Load a trained model from disk.

        Args:
            file_path: Optional path. Defaults to model_dir/random_forest.joblib.
        """
        if file_path is None:
            file_path = str(Path(settings.model_dir) / "random_forest.joblib")

        data = joblib.load(file_path)
        self.model = data["model"]
        self.feature_names = data.get("feature_names", [])
        self.feature_importances = data.get("feature_importances", {})
        self.best_params = data.get("best_params", {})
        self.is_trained = True
        logger.info("Model loaded from: %s", file_path)
