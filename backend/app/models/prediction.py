"""
ORM Model — MoisturePrediction.

Stores ML model predictions of soil moisture for each field.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.farm import Field


class MoisturePrediction(Base, UUIDMixin, TimestampMixin):
    """Soil moisture prediction record from the ML model."""

    __tablename__ = "moisture_predictions"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    predicted_moisture: Mapped[float] = mapped_column(Float, nullable=False)
    actual_moisture: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False, default="random_forest")
    model_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    features_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prediction_horizon_hours: Mapped[Optional[int]] = mapped_column(nullable=True, default=0)

    field: Mapped["Field"] = relationship("Field", back_populates="moisture_predictions")

    def __repr__(self) -> str:
        return f"<MoisturePrediction(id={self.id}, predicted={self.predicted_moisture:.3f})>"
