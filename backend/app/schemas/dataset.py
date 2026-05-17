"""
Pydantic Schemas — Dataset Operations.

Request/response schemas for dataset upload, validation, and training.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetUploadResponse(BaseModel):
    """Response after dataset upload and validation."""
    filename: str
    file_size_bytes: int
    rows: int
    columns: int
    column_names: List[str]
    mapped_columns: Dict[str, str] = Field(default_factory=dict)
    missing_features: List[str] = Field(default_factory=list)
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    message: str


class TrainModelRequest(BaseModel):
    """Request to train a model."""
    model_name: str = Field("random_forest", description="Model type: random_forest, xgboost, lstm, cnn")
    dataset_path: Optional[str] = Field(None, description="Path to dataset file. Uses latest upload if not specified.")
    target_column: str = Field("soil_moisture", description="Name of the target variable column")
    test_size: float = Field(0.15, ge=0.05, le=0.5)
    tune_hyperparams: bool = Field(False, description="Enable hyperparameter tuning")


class TrainModelResponse(BaseModel):
    """Response after model training."""
    model_name: str
    model_path: str
    training_duration_seconds: float
    dataset_info: Dict[str, Any]
    train_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    feature_importance: List[Any]
    message: str


class RetrainRequest(BaseModel):
    """Request to retrain model with new data."""
    model_name: str = Field("random_forest")
    include_new_data: bool = Field(True)
