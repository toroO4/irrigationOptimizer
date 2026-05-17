"""
ML Pipeline — Feature Engineering.

Transforms raw features into optimized model inputs through:
- Temporal feature extraction
- Interaction terms
- Rolling statistics
- Polynomial features
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.core.logging_config import get_logger

logger = get_logger(__name__)


def add_temporal_features(df: pd.DataFrame, date_column: str = "timestamp") -> pd.DataFrame:
    """
    Extract temporal features from a date/timestamp column.

    Adds: day_of_year, month, week_of_year, season, is_monsoon.

    Args:
        df: Input DataFrame.
        date_column: Name of the date column.

    Returns:
        DataFrame with added temporal features.
    """
    if date_column not in df.columns:
        logger.warning("Date column '%s' not found — skipping temporal features", date_column)
        return df

    df = df.copy()
    dt = pd.to_datetime(df[date_column])

    df["day_of_year"] = dt.dt.dayofyear
    df["month"] = dt.dt.month
    df["week_of_year"] = dt.dt.isocalendar().week.astype(int)

    # Season encoding (Indian agricultural seasons)
    df["season"] = df["month"].map(lambda m: _get_season(m))

    # Monsoon flag (June–September for Indian subcontinent)
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)

    logger.info("Temporal features added: day_of_year, month, week_of_year, season, is_monsoon")
    return df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create interaction features between key variables.

    Adds:
    - moisture_temperature: soil_moisture × temperature
    - ndvi_rainfall: ndvi × rainfall
    - vv_ndvi: vv_backscatter × ndvi
    - deficit_indicator: field_capacity - soil_moisture
    """
    df = df.copy()

    if "soil_moisture" in df.columns and "temperature" in df.columns:
        df["moisture_temperature"] = df["soil_moisture"] * df["temperature"]

    if "ndvi" in df.columns and "rainfall" in df.columns:
        df["ndvi_rainfall"] = df["ndvi"] * df["rainfall"]

    if "vv_backscatter" in df.columns and "ndvi" in df.columns:
        df["vv_ndvi"] = df["vv_backscatter"] * df["ndvi"]

    if "field_capacity" in df.columns and "soil_moisture" in df.columns:
        df["deficit_indicator"] = df["field_capacity"] - df["soil_moisture"]

    logger.info("Interaction features added")
    return df


def add_rolling_statistics(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    windows: List[int] = [3, 7],
) -> pd.DataFrame:
    """
    Compute rolling mean and standard deviation for specified columns.

    Args:
        df: Input DataFrame (assumed sorted by time).
        columns: Columns to compute rolling stats for. Default uses
                 soil_moisture and rainfall if available.
        windows: Window sizes for rolling computation.

    Returns:
        DataFrame with added rolling statistic columns.
    """
    df = df.copy()

    if columns is None:
        columns = [c for c in ["soil_moisture", "rainfall", "temperature"] if c in df.columns]

    for col in columns:
        for w in windows:
            df[f"{col}_rolling_mean_{w}"] = df[col].rolling(window=w, min_periods=1).mean()
            df[f"{col}_rolling_std_{w}"] = df[col].rolling(window=w, min_periods=1).std().fillna(0)

    logger.info("Rolling statistics added for columns: %s, windows: %s", columns, windows)
    return df


def add_lag_features(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    lags: List[int] = [1, 3, 7],
) -> pd.DataFrame:
    """
    Add lagged versions of specified columns.

    Args:
        df: Input DataFrame (assumed sorted by time).
        columns: Columns to create lags for.
        lags: Number of time steps to lag.

    Returns:
        DataFrame with lag features.
    """
    df = df.copy()

    if columns is None:
        columns = [c for c in ["soil_moisture", "rainfall"] if c in df.columns]

    for col in columns:
        for lag in lags:
            df[f"{col}_lag_{lag}"] = df[col].shift(lag)

    # Fill NaN values from lag operations
    df = df.fillna(method="bfill").fillna(method="ffill")

    logger.info("Lag features added for columns: %s, lags: %s", columns, lags)
    return df


def compute_moisture_anomaly(
    current_moisture: float,
    historical_mean: float,
    historical_std: float,
) -> Dict[str, float]:
    """
    Compute moisture anomaly relative to historical baseline.

    Args:
        current_moisture: Current soil moisture (cm³/cm³).
        historical_mean: Historical mean moisture.
        historical_std: Historical standard deviation.

    Returns:
        Dictionary with anomaly score and classification.
    """
    if historical_std < 0.001:
        z_score = 0.0
    else:
        z_score = (current_moisture - historical_mean) / historical_std

    # Classify anomaly
    if z_score < -2.0:
        classification = "extremely_dry"
    elif z_score < -1.0:
        classification = "below_normal"
    elif z_score < 1.0:
        classification = "normal"
    elif z_score < 2.0:
        classification = "above_normal"
    else:
        classification = "extremely_wet"

    return {
        "z_score": round(z_score, 3),
        "anomaly_pct": round((current_moisture - historical_mean) / max(historical_mean, 0.01) * 100, 2),
        "classification": classification,
    }


def _get_season(month: int) -> int:
    """Map month to Indian agricultural season (encoded)."""
    if month in (11, 12, 1, 2):
        return 0  # Rabi (winter crops)
    elif month in (6, 7, 8, 9):
        return 1  # Kharif (monsoon crops)
    elif month in (3, 4, 5):
        return 2  # Zaid (summer crops)
    else:
        return 3  # Transition
