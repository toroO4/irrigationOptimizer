"""
Utility — Geospatial Helpers.

Functions for coordinate transformations, distance calculations,
and GeoJSON operations.
"""

import math
from typing import Dict, List, Tuple


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points (km).

    Uses the Haversine formula for accuracy on a spherical Earth.

    Args:
        lat1, lon1: Coordinates of point 1 (degrees).
        lat2, lon2: Coordinates of point 2 (degrees).

    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Earth radius in km

    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def create_bounding_box(
    center_lat: float,
    center_lon: float,
    radius_km: float,
) -> Dict[str, float]:
    """
    Create a bounding box around a center point.

    Args:
        center_lat: Center latitude.
        center_lon: Center longitude.
        radius_km: Radius in kilometers.

    Returns:
        Dictionary with min_lat, max_lat, min_lon, max_lon.
    """
    lat_delta = radius_km / 111.0  # ~111 km per degree latitude
    lon_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))

    return {
        "min_lat": center_lat - lat_delta,
        "max_lat": center_lat + lat_delta,
        "min_lon": center_lon - lon_delta,
        "max_lon": center_lon + lon_delta,
    }


def point_to_geojson(lat: float, lon: float, properties: dict = None) -> dict:
    """Convert a lat/lon point to a GeoJSON Feature."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties or {},
    }


def polygon_to_wkt(coordinates: List[Tuple[float, float]]) -> str:
    """Convert a list of (lon, lat) tuples to WKT POLYGON string."""
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])  # Close the ring
    coords_str = ", ".join(f"{lon} {lat}" for lon, lat in coordinates)
    return f"POLYGON(({coords_str}))"
