"""
ML Pipeline — Model Registry.

Factory pattern for model selection, instantiation, and loading.
Supports: random_forest, xgboost, lstm, cnn.
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Registry of available models
MODEL_REGISTRY: Dict[str, str] = {
    "random_forest": "app.ml.models.random_forest.RandomForestModel",
    "xgboost": "app.ml.models.xgboost_model.XGBoostModel",
    "lstm": "app.ml.models.lstm_model.LSTMModel",
    "cnn": "app.ml.models.cnn_model.CNNModel",
}


def get_model(model_name: Optional[str] = None, **kwargs) -> Any:
    """
    Get a model instance by name.

    Uses lazy importing to avoid loading unnecessary dependencies.

    Args:
        model_name: Name of the model to instantiate.
                    Defaults to settings.default_model.
        **kwargs: Additional arguments passed to the model constructor.

    Returns:
        An instantiated model object.

    Raises:
        ValueError: If the model name is not in the registry.
        ImportError: If the model's dependencies are not installed.
    """
    if model_name is None:
        model_name = settings.default_model

    model_name = model_name.lower().strip()

    if model_name not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model: '{model_name}'. "
            f"Available models: {list(MODEL_REGISTRY.keys())}"
        )

    logger.info("Loading model: %s", model_name)

    # Lazy import based on model name
    if model_name == "random_forest":
        from app.ml.models.random_forest import RandomForestModel
        return RandomForestModel(**kwargs)

    elif model_name == "xgboost":
        from app.ml.models.xgboost_model import XGBoostModel
        return XGBoostModel(**kwargs)

    elif model_name == "lstm":
        from app.ml.models.lstm_model import LSTMModel
        return LSTMModel(**kwargs)

    elif model_name == "cnn":
        from app.ml.models.cnn_model import CNNModel
        return CNNModel(**kwargs)


def load_trained_model(model_name: Optional[str] = None, file_path: Optional[str] = None) -> Any:
    """
    Load a pre-trained model from disk.

    Args:
        model_name: Name of the model type.
        file_path: Path to the saved model file.

    Returns:
        A loaded and ready-to-predict model instance.
    """
    model = get_model(model_name)
    model.load(file_path)
    return model


def list_available_models() -> Dict[str, bool]:
    """
    List all registered models and their availability.

    Returns:
        Dictionary mapping model names to whether they can be imported.
    """
    availability = {}
    for name in MODEL_REGISTRY:
        try:
            get_model(name)
            availability[name] = True
        except (ImportError, Exception):
            availability[name] = False
    return availability
