"""
ORM Model — WeatherData.

Stores meteorological observations and forecasts for each field.
Used for ET₀ computation, rainfall tracking, and crop water demand.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.farm import Field


class WeatherData(Base, UUIDMixin, TimestampMixin):
    """
    Weather observation record for a field location.

    Attributes:
        field_id: Foreign key to the field.
        timestamp: Date and time of the observation.
        temperature: Air temperature (°C).
        temperature_min: Minimum temperature (°C).
        temperature_max: Maximum temperature (°C).
        humidity: Relative humidity (%).
        rainfall: Precipitation (mm).
        wind_speed: Wind speed at 2m height (m/s).
        solar_radiation: Incoming solar radiation (MJ/m²/day).
        et0: Reference evapotranspiration (mm/day) — FAO Penman-Monteith.
        pressure: Atmospheric pressure (kPa).
        cloud_cover: Cloud cover percentage.
        source: Data source (IMD, ERA5, OpenMeteo, user_upload).
    """

    __tablename__ = "weather_data"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
        doc="Foreign key to the field",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        doc="Observation timestamp",
    )

    # ── Temperature ──────────────────────────────────────────────────
    temperature: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Air temperature (°C)",
    )
    temperature_min: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Minimum temperature (°C)",
    )
    temperature_max: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Maximum temperature (°C)",
    )

    # ── Moisture & Precipitation ─────────────────────────────────────
    humidity: Mapped[float] = mapped_column(
        Float, nullable=False, default=50.0,
        doc="Relative humidity (%)",
    )
    rainfall: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        doc="Precipitation amount (mm)",
    )

    # ── Wind ─────────────────────────────────────────────────────────
    wind_speed: Mapped[float] = mapped_column(
        Float, nullable=False, default=2.0,
        doc="Wind speed at 2m height (m/s)",
    )

    # ── Radiation & ET ───────────────────────────────────────────────
    solar_radiation: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Incoming solar radiation (MJ/m²/day)",
    )
    et0: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Reference evapotranspiration — FAO Penman-Monteith (mm/day)",
    )

    # ── Other ────────────────────────────────────────────────────────
    pressure: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Atmospheric pressure (kPa)",
    )
    cloud_cover: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Cloud cover percentage (0–100)",
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="OpenMeteo",
        doc="Data source identifier",
    )

    # ── Relationships ────────────────────────────────────────────────
    field: Mapped["Field"] = relationship("Field", back_populates="weather_data")

    def __repr__(self) -> str:
        return (
            f"<WeatherData(id={self.id}, field_id={self.field_id}, "
            f"timestamp={self.timestamp}, temp={self.temperature}°C)>"
        )
