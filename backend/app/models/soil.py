"""
ORM Model — SoilData.

Stores soil physical and chemical properties for each field.
Used for pedotransfer functions, field capacity estimation,
and irrigation deficit calculations.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.farm import Field


class SoilData(Base, UUIDMixin, TimestampMixin):
    """
    Soil properties record for a field.

    Attributes:
        field_id: Foreign key to the field.
        sand_pct: Sand percentage (0–100).
        clay_pct: Clay percentage (0–100).
        silt_pct: Silt percentage (0–100).
        organic_matter: Organic matter percentage.
        field_capacity: Volumetric water content at field capacity (cm³/cm³).
        wilting_point: Volumetric water content at permanent wilting point.
        saturation: Volumetric water content at saturation.
        bulk_density: Soil bulk density (g/cm³).
        ph: Soil pH value.
        texture_class: USDA texture classification string.
        ksat: Saturated hydraulic conductivity (mm/hr).
        depth_cm: Soil sampling depth in centimeters.
        source: Where this data came from (lab, OpenLandMap, user_upload).
    """

    __tablename__ = "soil_data"

    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False, index=True,
        doc="Foreign key to the field",
    )

    # ── Particle size distribution ───────────────────────────────────
    sand_pct: Mapped[float] = mapped_column(
        Float, nullable=False, default=40.0,
        doc="Sand content as percentage (0–100)",
    )
    clay_pct: Mapped[float] = mapped_column(
        Float, nullable=False, default=25.0,
        doc="Clay content as percentage (0–100)",
    )
    silt_pct: Mapped[float] = mapped_column(
        Float, nullable=False, default=35.0,
        doc="Silt content as percentage (0–100)",
    )

    # ── Hydraulic properties ─────────────────────────────────────────
    organic_matter: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=2.5,
        doc="Organic matter percentage",
    )
    field_capacity: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.30,
        doc="Volumetric water content at field capacity (cm³/cm³)",
    )
    wilting_point: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.15,
        doc="Volumetric water content at permanent wilting point (cm³/cm³)",
    )
    saturation: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=0.48,
        doc="Volumetric water content at saturation (cm³/cm³)",
    )
    bulk_density: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=1.35,
        doc="Soil bulk density (g/cm³)",
    )

    # ── Chemical properties ──────────────────────────────────────────
    ph: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Soil pH value",
    )

    # ── Classification ───────────────────────────────────────────────
    texture_class: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True,
        doc="USDA texture triangle classification",
    )
    ksat: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Saturated hydraulic conductivity (mm/hr)",
    )
    depth_cm: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=30.0,
        doc="Soil sampling depth (cm)",
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="user_upload",
        doc="Data source: lab, OpenLandMap, user_upload",
    )

    # ── Relationships ────────────────────────────────────────────────
    field: Mapped["Field"] = relationship("Field", back_populates="soil_data")

    def __repr__(self) -> str:
        return (
            f"<SoilData(id={self.id}, field_id={self.field_id}, "
            f"texture={self.texture_class})>"
        )

    @property
    def available_water_capacity(self) -> float:
        """
        Calculate available water capacity (AWC).

        AWC = Field Capacity - Wilting Point (cm³/cm³).
        This is the range of moisture available to plants.

        Returns:
            Available water capacity in cm³/cm³.
        """
        return self.field_capacity - self.wilting_point
