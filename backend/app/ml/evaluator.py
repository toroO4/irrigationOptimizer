"""
ML Pipeline — Model Evaluator.

Computes comprehensive evaluation metrics for trained models:
RMSE, MAE, R², MAPE, and feature importance ranking.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
)

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    dataset_name: str = "test",
) -> Dict[str, float]:
    """
    Evaluate a trained regression model on a test dataset.

    Computes:
    - RMSE
    - MAE
    - R²

    Args:
        model: Trained model with a predict() method.
        X_test: Test feature matrix.
        y_test: True target values.
        dataset_name: Label for logging (e.g., "test", "validation").

    Returns:
        Dictionary of evaluation metrics.
    """
    predictions = model.predict(X_test)

    mse = mean_squared_error(y_test, predictions)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_test, predictions))
    r2 = float(r2_score(y_test, predictions))

    metrics = {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2_score": round(r2, 4),
        "n_samples": len(y_test),
    }

    logger.info(
        "%s evaluation — RMSE=%.4f, MAE=%.4f, R²=%.4f",
        dataset_name, rmse, mae, r2,
    )

    return metrics


def compute_prediction_statistics(
    predictions: np.ndarray,
    actuals: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Compute statistical summary of predictions.

    Args:
        predictions: Array of predicted values.
        actuals: Optional array of actual values for comparison.

    Returns:
        Dictionary of prediction statistics.
    """
    stats = {
        "pred_mean": round(float(np.mean(predictions)), 4),
        "pred_std": round(float(np.std(predictions)), 4),
        "pred_min": round(float(np.min(predictions)), 4),
        "pred_max": round(float(np.max(predictions)), 4),
        "pred_median": round(float(np.median(predictions)), 4),
    }

    if actuals is not None:
        stats.update({
            "actual_mean": round(float(np.mean(actuals)), 4),
            "actual_std": round(float(np.std(actuals)), 4),
            "correlation": round(float(np.corrcoef(predictions, actuals)[0, 1]), 4),
        })

    return stats


def generate_evaluation_report(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive evaluation report.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test targets.
        feature_names: Feature name list.

    Returns:
        Full evaluation report dictionary.
    """
    metrics = evaluate_model(model, X_test, y_test)
    predictions = model.predict(X_test)
    pred_stats = compute_prediction_statistics(predictions, y_test)

    residuals = y_test - predictions
    residual_stats = {
        "mean_residual": round(float(np.mean(residuals)), 4),
        "std_residual": round(float(np.std(residuals)), 4),
        "max_error": round(float(np.max(np.abs(residuals))), 4),
    }

    # Feature importance
    importance = []
    if hasattr(model, "get_feature_importance"):
        importance = model.get_feature_importance(top_n=15)

    report = {
        "metrics": metrics,
        "prediction_statistics": pred_stats,
        "residual_analysis": residual_stats,
        "feature_importance": importance,
        "sample_predictions": [
            {"actual": round(float(y_test[i]), 4), "predicted": round(float(predictions[i]), 4)}
            for i in range(min(10, len(y_test)))
        ],
    }

    logger.info("Evaluation report generated — %d metrics computed", len(metrics))
    return report


def _compute_skewness(data: np.ndarray) -> float:
    """Compute the skewness of an array."""
    n = len(data)
    if n < 3:
        return 0.0
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    if std == 0:
        return 0.0
    return float((n / ((n - 1) * (n - 2))) * np.sum(((data - mean) / std) ** 3))
