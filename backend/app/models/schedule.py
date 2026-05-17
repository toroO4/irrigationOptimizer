"""
ORM Model — IrrigationSchedule.

Stores generated irrigation schedules for each field.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.farm import Field


class IrrigationSchedule(Base, UUIDMixin, TimestampMixin):
    """Irrigation schedule record for a field."""

    __tablename__ = "irrigation_schedules"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        doc="When irrigation should start",
    )
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    water_volume_liters: Mapped[float] = mapped_column(Float, nullable=False)
    pump_runtime_hours: Mapped[float] = mapped_column(Float, nullable=False)
    deficit_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_moisture: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_moisture: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="moderate")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        doc="Status: pending, in_progress, completed, cancelled",
    )
    irrigation_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    energy_cost_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    field: Mapped["Field"] = relationship("Field", back_populates="irrigation_schedules")

    def __repr__(self) -> str:
        return f"<IrrigationSchedule(id={self.id}, status={self.status}, urgency={self.urgency})>"
