"""
ORM Model — SatelliteData.

Stores satellite-derived observations from Sentinel-1 (SAR)
and Sentinel-2 (optical) for each field.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.farm import Field


class SatelliteData(Base, UUIDMixin, TimestampMixin):
    """
    Satellite observation record for a field.

    Stores both SAR backscatter values (Sentinel-1) and optical
    indices (Sentinel-2) along with derived metrics.

    Attributes:
        field_id: Foreign key to the field.
        timestamp: Acquisition date of the satellite pass.
        source: Satellite source (Sentinel-1, Sentinel-2).
        orbit_direction: Ascending or descending pass.
        vv_backscatter: VV polarization backscatter coefficient (dB).
        vh_backscatter: VH polarization backscatter coefficient (dB).
        vh_vv_ratio: VH/VV ratio (linear or dB).
        incidence_angle: Local incidence angle (degrees).
        ndvi: Normalized Difference Vegetation Index (-1 to 1).
        ndwi: Normalized Difference Water Index (-1 to 1).
        sar_moisture: SAR-derived soil moisture (cm³/cm³).
        processing_level: Processing level applied.
        scene_id: Original scene/product identifier.
    """

    __tablename__ = "satellite_data"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
        doc="Foreign key to the field",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        doc="Satellite acquisition timestamp",
    )

    # ── Source Information ────────────────────────────────────────────
    source: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Sentinel-1",
        doc="Satellite source: Sentinel-1, Sentinel-2, Landsat",
    )
    orbit_direction: Mapped[Optional[str]] = mapped_column(
        String(15), nullable=True,
        doc="Orbit direction: ascending or descending",
    )

    # ── SAR Backscatter (Sentinel-1) ─────────────────────────────────
    vv_backscatter: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="VV polarization backscatter (dB)",
    )
    vh_backscatter: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="VH polarization backscatter (dB)",
    )
    vh_vv_ratio: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="VH/VV backscatter ratio",
    )
    incidence_angle: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Local incidence angle (degrees)",
    )

    # ── Optical Indices (Sentinel-2) ─────────────────────────────────
    ndvi: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="NDVI — Normalized Difference Vegetation Index",
    )
    ndwi: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="NDWI — Normalized Difference Water Index",
    )

    # ── Derived Moisture ─────────────────────────────────────────────
    sar_moisture: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="SAR-derived volumetric soil moisture (cm³/cm³)",
    )

    # ── Metadata ─────────────────────────────────────────────────────
    processing_level: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        doc="Processing level: raw, calibrated, filtered, corrected",
    )
    scene_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        doc="Original satellite scene/product ID",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="Processing notes or quality flags",
    )

    # ── Relationships ────────────────────────────────────────────────
    field: Mapped["Field"] = relationship("Field", back_populates="satellite_data")

    def __repr__(self) -> str:
        return (
            f"<SatelliteData(id={self.id}, source={self.source}, "
            f"timestamp={self.timestamp})>"
        )
