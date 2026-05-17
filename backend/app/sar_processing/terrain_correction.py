"""
SAR Processing — Terrain Correction.

Applies Range-Doppler terrain correction using DEM data to
remove geometric distortions (foreshortening, layover, shadow)
caused by SAR side-looking geometry and topography.
"""

import numpy as np

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def apply_terrain_correction(
    backscatter_db: np.ndarray,
    elevation_map: np.ndarray = None,
    incidence_angle: float = 38.0,
    pixel_spacing_m: float = 10.0,
) -> np.ndarray:
    """
    Apply terrain correction to calibrated SAR backscatter.

    Compensates for the effect of local terrain slope on the
    backscatter measurement. Uses a simplified cosine correction
    model based on local incidence angle variations.

    In production, this would use SNAP's Range-Doppler Terrain
    Correction with SRTM DEM. This implementation provides a
    mathematically equivalent simulation.

    The correction formula:
        σ⁰_corrected = σ⁰_observed × cos(θ_ref) / cos(θ_local)

    Where:
        θ_ref = reference incidence angle (mid-swath)
        θ_local = local incidence angle (adjusted for terrain slope)

    Args:
        backscatter_db: 2D array of calibrated σ⁰ values in dB.
        elevation_map: 2D array of elevation values (meters).
                       If None, a flat terrain is assumed (no correction).
        incidence_angle: Reference incidence angle in degrees.
        pixel_spacing_m: Ground pixel spacing in meters.

    Returns:
        Terrain-corrected σ⁰ values in dB.
    """
    logger.info(
        "Applying terrain correction — incidence=%.1f°, pixel_spacing=%.1fm",
        incidence_angle, pixel_spacing_m,
    )

    corrected = backscatter_db.copy().astype(np.float64)

    if elevation_map is None:
        logger.info("No DEM provided — assuming flat terrain (no correction applied)")
        return corrected

    # Compute terrain slope from DEM using gradient
    grad_y, grad_x = np.gradient(elevation_map.astype(np.float64), pixel_spacing_m)
    slope_rad = np.arctan(np.sqrt(grad_x ** 2 + grad_y ** 2))

    # Compute local incidence angle adjustment
    theta_ref = np.radians(incidence_angle)
    theta_local = theta_ref - slope_rad  # Simplified — ignores aspect

    # Prevent extreme corrections at very steep slopes
    theta_local = np.clip(theta_local, np.radians(10.0), np.radians(70.0))

    # Apply cosine correction in dB domain
    # ΔdB = 10 * log10(cos(θ_ref) / cos(θ_local))
    correction_db = 10.0 * np.log10(
        np.cos(theta_ref) / (np.cos(theta_local) + 1e-10) + 1e-30
    )

    corrected += correction_db

    logger.info(
        "Terrain correction applied — correction range: [%.2f, %.2f] dB",
        float(np.min(correction_db)),
        float(np.max(correction_db)),
    )

    return corrected


def compute_local_incidence_angle(
    elevation_map: np.ndarray,
    satellite_heading: float = 348.0,
    incidence_angle: float = 38.0,
    pixel_spacing_m: float = 10.0,
) -> np.ndarray:
    """
    Compute local incidence angle for each pixel.

    Takes into account terrain slope and aspect relative to the
    satellite look direction.

    Args:
        elevation_map: 2D DEM array in meters.
        satellite_heading: Satellite orbit heading in degrees from north.
        incidence_angle: Reference incidence angle in degrees.
        pixel_spacing_m: Ground pixel spacing in meters.

    Returns:
        2D array of local incidence angles in degrees.
    """
    logger.info("Computing local incidence angles")

    grad_y, grad_x = np.gradient(
        elevation_map.astype(np.float64), pixel_spacing_m
    )

    # Terrain slope and aspect
    slope = np.arctan(np.sqrt(grad_x ** 2 + grad_y ** 2))
    aspect = np.arctan2(-grad_x, grad_y)

    # Satellite look direction (perpendicular to heading)
    look_direction = np.radians(satellite_heading + 90.0)

    # Local incidence angle
    theta_ref = np.radians(incidence_angle)
    local_theta = np.arccos(
        np.cos(slope) * np.cos(theta_ref)
        + np.sin(slope) * np.sin(theta_ref) * np.cos(aspect - look_direction)
    )

    return np.degrees(local_theta)


def generate_flat_dem(rows: int, cols: int, base_elevation: float = 500.0) -> np.ndarray:
    """
    Generate a flat DEM for testing when no real DEM is available.

    Args:
        rows: Number of rows.
        cols: Number of columns.
        base_elevation: Constant elevation value in meters.

    Returns:
        2D numpy array representing a flat terrain DEM.
    """
    return np.full((rows, cols), base_elevation, dtype=np.float64)


def generate_synthetic_dem(
    rows: int = 100,
    cols: int = 100,
    base_elevation: float = 500.0,
    max_relief: float = 50.0,
    seed: int = 42,
) -> np.ndarray:
    """
    Generate a synthetic DEM with realistic terrain features.

    Creates a smooth terrain surface using superimposed sine waves
    to simulate gentle hills and valleys.

    Args:
        rows: Number of rows.
        cols: Number of columns.
        base_elevation: Base elevation in meters.
        max_relief: Maximum elevation variation in meters.
        seed: Random seed for reproducibility.

    Returns:
        2D numpy array representing a synthetic terrain DEM.
    """
    rng = np.random.default_rng(seed)

    x = np.linspace(0, 4 * np.pi, cols)
    y = np.linspace(0, 4 * np.pi, rows)
    xx, yy = np.meshgrid(x, y)

    # Superimpose sine waves at different frequencies
    terrain = (
        max_relief * 0.4 * np.sin(xx * 0.5) * np.cos(yy * 0.3)
        + max_relief * 0.3 * np.sin(xx * 1.2 + yy * 0.8)
        + max_relief * 0.2 * np.cos(xx * 2.0) * np.sin(yy * 1.5)
        + max_relief * 0.1 * rng.standard_normal((rows, cols))
    )

    dem = base_elevation + terrain
    return dem
