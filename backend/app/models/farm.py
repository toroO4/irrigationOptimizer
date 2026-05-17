"""
ORM Models — Farm and Field.

Farm: A collection of agricultural fields owned by a user.
Field: An individual plot within a farm with specific crop, soil,
       and geometry attributes. Uses PostGIS for spatial data.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.soil import SoilData
    from app.models.weather import WeatherData
    from app.models.satellite import SatelliteData
    from app.models.prediction import MoisturePrediction
    from app.models.schedule import IrrigationSchedule


class Farm(Base, UUIDMixin, TimestampMixin):
    """
    Farm model — a logical grouping of fields.

    Attributes:
        name: Farm name or identifier.
        owner_id: Foreign key to the user who owns this farm.
        location_lat: Latitude of the farm center.
        location_lon: Longitude of the farm center.
        total_area_hectares: Total farmland area in hectares.
        address: Optional human-readable address.
        region: Geographic region (e.g., Maharashtra, Karnataka).
        fields: List of fields within this farm.
    """

    __tablename__ = "farms"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc="Farm name or identifier",
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
        doc="Foreign key to the owning user",
    )
    location_lat: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Farm center latitude (WGS84)",
    )
    location_lon: Mapped[float] = mapped_column(
        Float, nullable=False,
        doc="Farm center longitude (WGS84)",
    )
    total_area_hectares: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Total farm area in hectares",
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        doc="Human-readable address",
    )
    region: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        doc="Geographic region name",
    )

    # ── Relationships ────────────────────────────────────────────────
    owner: Mapped["User"] = relationship("User", back_populates="farms")
    fields: Mapped[List["Field"]] = relationship(
        "Field", back_populates="farm", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Farm(id={self.id}, name={self.name})>"


class Field(Base, UUIDMixin, TimestampMixin):
    """
    Field model — an individual agricultural plot.

    Represents a specific area of land within a farm where a single
    crop is grown. Stores geometry, crop type, soil classification,
    and irrigation system details.

    Attributes:
        farm_id: Parent farm foreign key.
        name: Field name/number.
        crop_type: Current crop being grown.
        soil_type: USDA soil texture classification.
        area_hectares: Field area in hectares.
        irrigation_type: Irrigation system type (drip, sprinkler, flood).
        geometry_wkt: Well-Known Text representation of field boundary.
        centroid_lat: Centroid latitude.
        centroid_lon: Centroid longitude.
        elevation_m: Average elevation in meters.
    """

    __tablename__ = "fields"

    farm_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False, index=True,
        doc="Foreign key to parent farm",
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc="Field name or plot number",
    )
    crop_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="wheat",
        doc="Crop currently being cultivated",
    )
    soil_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="loam",
        doc="USDA soil texture classification",
    )
    area_hectares: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0,
        doc="Field area in hectares",
    )
    irrigation_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="drip",
        doc="Irrigation system type",
    )
    geometry_wkt: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="WKT polygon geometry of field boundary",
    )
    centroid_lat: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Centroid latitude (WGS84)",
    )
    centroid_lon: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Centroid longitude (WGS84)",
    )
    elevation_m: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        doc="Average elevation in meters above sea level",
    )
    pump_flow_rate_lph: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=5000.0,
        doc="Pump flow rate in liters per hour",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="Additional notes about the field",
    )

    # ── Relationships ────────────────────────────────────────────────
    farm: Mapped["Farm"] = relationship("Farm", back_populates="fields")
    soil_data: Mapped[List["SoilData"]] = relationship(
        "SoilData", back_populates="field", cascade="all, delete-orphan",
    )
    weather_data: Mapped[List["WeatherData"]] = relationship(
        "WeatherData", back_populates="field", cascade="all, delete-orphan",
    )
    satellite_data: Mapped[List["SatelliteData"]] = relationship(
        "SatelliteData", back_populates="field", cascade="all, delete-orphan",
    )
    moisture_predictions: Mapped[List["MoisturePrediction"]] = relationship(
        "MoisturePrediction", back_populates="field", cascade="all, delete-orphan",
    )
    irrigation_schedules: Mapped[List["IrrigationSchedule"]] = relationship(
        "IrrigationSchedule", back_populates="field", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Field(id={self.id}, name={self.name}, crop={self.crop_type})>"
