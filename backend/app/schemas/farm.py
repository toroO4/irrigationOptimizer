from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class FieldBase(BaseModel):
    name: str
    crop_type: str = "wheat"
    soil_type: str = "loam"
    area_hectares: float = 1.0
    irrigation_type: str = "drip"
    geometry_wkt: Optional[str] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    elevation_m: Optional[float] = None

class FieldCreate(FieldBase):
    pass

class FieldRead(FieldBase):
    id: str
    farm_id: str

    model_config = ConfigDict(from_attributes=True)


class FarmBase(BaseModel):
    name: str
    location_lat: float
    location_lon: float
    total_area_hectares: Optional[float] = None
    address: Optional[str] = None
    region: Optional[str] = None

class FarmCreate(FarmBase):
    pass

class FarmRead(FarmBase):
    id: str
    owner_id: str
    fields: List[FieldRead] = []

    model_config = ConfigDict(from_attributes=True)
