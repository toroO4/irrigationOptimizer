"""
ORM Model — Sensor Data.

Stores telemetry data from ground IoT sensors (soil moisture, temperature).
"""

from sqlalchemy import Float, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import datetime

from app.database.base import Base, UUIDMixin


class SensorData(Base, UUIDMixin):
    """
    IoT Sensor Telemetry Data.
    """
    __tablename__ = "sensor_data"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
        doc="Foreign key to the field this sensor belongs to",
    )
    moisture_level: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Volumetric soil moisture content from sensor",
    )
    temperature: Mapped[float] = mapped_column(
        Float, nullable=True,
        doc="Soil or ambient temperature at sensor location",
    )
    recorded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        index=True, doc="Timestamp of the reading",
    )

    def __repr__(self) -> str:
        return f"<SensorData(id={self.id}, field_id={self.field_id}, moisture={self.moisture_level})>"
