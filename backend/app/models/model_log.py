"""
ORM Model — ModelLog.

Tracks ML model training runs, hyperparameters, and performance metrics.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class ModelLog(Base, UUIDMixin, TimestampMixin):
    """ML model training log record."""

    __tablename__ = "model_logs"

    model_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dataset_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dataset_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    train_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    test_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Performance metrics
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    r2_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Configuration
    hyperparameters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    features_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    training_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_file_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ModelLog(name={self.model_name}, version={self.model_version}, rmse={self.rmse})>"
