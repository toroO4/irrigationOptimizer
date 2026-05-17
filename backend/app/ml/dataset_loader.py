"""
ML Pipeline — Dataset Loader.

Handles:
- CSV/Excel file loading and auto-detection
- Column mapping to model features
- Missing value handling (interpolation, imputation)
- Outlier detection and removal (IQR-based)
- Feature scaling (StandardScaler, MinMaxScaler)
- Categorical encoding (LabelEncoder)
- Feature extraction (VH/VV ratio, cross-pol index)
- Train/test/validation split
- Validation report generation
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler

from app.config.constants import ALL_FEATURES, VALID_RANGES
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Column name aliases for auto-mapping user datasets
COLUMN_ALIASES = {
    "soil_type": ["soil_type", "Soil_Type"],
    "soil_ph": ["soil_ph", "Soil_pH", "ph", "pH"],
    "soil_moisture": ["soil_moisture", "Soil_Moisture", "moisture"],
    "organic_carbon": ["organic_carbon", "Organic_Carbon", "oc"],
    "electrical_conductivity": ["electrical_conductivity", "Electrical_Conductivity", "ec"],
    "temperature_c": ["temperature_c", "Temperature_C", "temperature", "temp"],
    "humidity": ["humidity", "Humidity"],
    "rainfall_mm": ["rainfall_mm", "Rainfall_mm", "rainfall", "rain"],
    "sunlight_hours": ["sunlight_hours", "Sunlight_Hours", "sunlight"],
    "wind_speed_kmh": ["wind_speed_kmh", "Wind_Speed_kmh", "wind_speed"],
    "crop_type": ["crop_type", "Crop_Type"],
    "crop_growth_stage": ["crop_growth_stage", "Crop_Growth_Stage"],
    "season": ["season", "Season"],
    "irrigation_type": ["irrigation_type", "Irrigation_Type"],
    "water_source": ["water_source", "Water_Source"],
    "field_area_hectare": ["field_area_hectare", "Field_Area_hectare", "field_area"],
    "mulching_used": ["mulching_used", "Mulching_Used"],
    "previous_irrigation_mm": ["previous_irrigation_mm", "Previous_Irrigation_mm"],
    "region": ["region", "Region"],
    "irrigation_need": ["irrigation_need", "Irrigation_Need", "target"],
}


class DatasetLoader:
    """
    Comprehensive dataset loading and preprocessing pipeline.

    Handles the full lifecycle of data preparation:
    loading → validation → cleaning → encoding → scaling → splitting.

    Usage:
        loader = DatasetLoader()
        result = loader.load_and_prepare("path/to/dataset.csv")
        X_train, X_test, y_train, y_test = result["splits"]
    """

    def __init__(
        self,
        target_column: str = "irrigation_need",
        test_size: float = 0.15,
        val_size: float = 0.15,
        scaler_type: str = "standard",
        random_state: int = 42,
    ):
        """
        Initialize the DatasetLoader.

        Args:
            target_column: Name of the target variable column.
            test_size: Fraction of data for test set.
            val_size: Fraction of data for validation set.
            scaler_type: Scaler type ("standard" or "minmax").
            random_state: Random seed for reproducibility.
        """
        self.target_column = target_column
        self.test_size = test_size
        self.val_size = val_size
        self.scaler_type = scaler_type
        self.random_state = random_state
        self.scaler = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.column_mapping: Dict[str, str] = {}
        self.validation_report: Dict[str, Any] = {}

    def load_and_prepare(
        self,
        file_path: str,
        target_column: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Load, validate, clean, and prepare a dataset for ML training.

        This is the main entry point that runs the full pipeline:
        1. Load file (CSV, Excel, JSON)
        2. Auto-map columns to expected feature names
        3. Handle missing values
        4. Detect and remove outliers
        5. Encode categorical features
        6. Extract derived features
        7. Scale numeric features
        8. Split into train/val/test sets
        9. Generate validation report

        Args:
            file_path: Path to the dataset file.
            target_column: Override for the target column name.

        Returns:
            Dictionary containing:
                - splits: (X_train, X_val, X_test, y_train, y_val, y_test)
                - scaler: Fitted scaler object
                - label_encoders: Fitted label encoders
                - column_mapping: Applied column mapping
                - validation_report: Data quality report
                - feature_names: List of feature names used
                - dataframe: Cleaned dataframe
        """
        if target_column:
            self.target_column = target_column

        logger.info("Loading dataset from: %s", file_path)

        # Step 1: Load the file
        df = self._load_file(file_path)
        original_shape = df.shape
        logger.info("Dataset loaded — shape=%s, columns=%s", df.shape, list(df.columns))

        # Step 2: Auto-map columns
        df = self._auto_map_columns(df)

        # Step 3: Handle missing values
        df = self._handle_missing_values(df)

        # Step 4: Detect and remove outliers
        df, outliers_removed = self._remove_outliers(df)

        # Step 5: Encode categorical features
        df = self._encode_categoricals(df)

        # Step 6: Extract derived features (lags)
        df = self._extract_derived_features(df)

        # Step 7: Identify features and target
        feature_cols = [col for col in df.columns if col != self.target_column]
        if self.target_column not in df.columns:
            raise ValueError(
                f"Target column '{self.target_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )

        X = df[feature_cols].values.astype(np.float64)
        
        # Labels are already encoded by LabelEncoder in _encode_categoricals 
        # because the target column is typically strings like "Low", "Medium", "High"
        if df[self.target_column].dtype in ("float64", "int64", "float32", "int32"):
            y = df[self.target_column].values.astype(np.int64)
        else:
            # If target column was somehow not encoded
            le = LabelEncoder()
            y = le.fit_transform(df[self.target_column].values)
            self.label_encoders[self.target_column] = le
            df[self.target_column] = y

        # Step 8: Scale features
        X_scaled = self._scale_features(X)

        # Step 9: Train/val/test split
        X_train, X_temp, y_train, y_temp = train_test_split(
            X_scaled, y,
            test_size=self.test_size + self.val_size,
            random_state=self.random_state,
        )
        relative_val = self.val_size / (self.test_size + self.val_size)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp,
            test_size=1.0 - relative_val,
            random_state=self.random_state,
        )

        # Step 10: Generate validation report
        self.validation_report = self._generate_report(
            df, original_shape, outliers_removed, feature_cols,
            X_train, X_val, X_test,
        )

        logger.info(
            "Dataset prepared — train=%d, val=%d, test=%d, features=%d",
            len(X_train), len(X_val), len(X_test), X_train.shape[1],
        )

        return {
            "splits": (X_train, X_val, X_test, y_train, y_val, y_test),
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "column_mapping": self.column_mapping,
            "validation_report": self.validation_report,
            "feature_names": feature_cols,
            "dataframe": df,
        }

    def _load_file(self, file_path: str) -> pd.DataFrame:
        """Load dataset from CSV, Excel, or JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return df

    def _auto_map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Auto-detect and rename columns to match expected feature names.

        Uses the COLUMN_ALIASES dictionary to find matches.
        """
        logger.info("Auto-mapping columns...")
        rename_map = {}

        for standard_name, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in df.columns and standard_name not in df.columns:
                    rename_map[alias] = standard_name
                    break
            # Also check case-insensitive match
            if standard_name not in rename_map.values():
                for col in df.columns:
                    if col.lower().strip() == standard_name.lower():
                        rename_map[col] = standard_name
                        break

        if rename_map:
            df = df.rename(columns=rename_map)
            self.column_mapping = rename_map
            logger.info("Columns renamed: %s", rename_map)

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values using domain-appropriate strategies.

        Strategy by column type:
        - Numeric: forward fill → backward fill → median imputation
        - Categorical: fill with mode or "unknown"
        """
        missing_before = df.isnull().sum().sum()
        logger.info("Missing values before handling: %d", missing_before)

        for col in df.columns:
            if df[col].isnull().sum() == 0:
                continue

            if df[col].dtype in ("float64", "int64", "float32", "int32"):
                # Numeric: interpolate → forward fill → median
                df[col] = df[col].interpolate(method="linear", limit_direction="both")
                df[col] = df[col].fillna(df[col].median())
            else:
                # Categorical: fill with mode
                mode_val = df[col].mode()
                fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
                df[col] = df[col].fillna(fill_val)

        missing_after = df.isnull().sum().sum()
        logger.info("Missing values after handling: %d (removed %d)", missing_after, missing_before - missing_after)

        # Drop any remaining rows with NaN
        df = df.dropna()
        return df

    def _remove_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Detect and remove outliers using IQR method.

        For columns with known valid ranges, use range-based filtering.
        For others, use 1.5×IQR rule.
        """
        original_len = len(df)

        # Range-based filtering for known columns
        for col, (low, high) in VALID_RANGES.items():
            if col in df.columns:
                mask = (df[col] >= low) & (df[col] <= high)
                df = df[mask]

        # IQR-based filtering for numeric columns without known ranges
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in VALID_RANGES:
                continue  # Already handled
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            df = df[(df[col] >= lower) & (df[col] <= upper)]

        outliers_removed = original_len - len(df)
        logger.info("Outliers removed: %d rows (%.1f%%)", outliers_removed, 100.0 * outliers_removed / max(original_len, 1))
        return df, outliers_removed

    def _encode_categoricals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical columns using LabelEncoder."""
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in categorical_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le
            logger.info("Encoded categorical column: %s (%d classes)", col, len(le.classes_))
        return df

    def _extract_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute derived features from raw columns, specifically lag features for time series."""
        logger.info("Extracting time-series lag features...")
        
        # FYP Dataset lag logic
        moisture_col = "sar_corrected_moisture" if "sar_corrected_moisture" in df.columns else "soil_moisture"
        window = 7
        
        # Check if required columns exist before shifting
        required_cols = [moisture_col]
        if "rainfall" in df.columns:
            required_cols.append("rainfall")
        elif "rainfall_mm" in df.columns:
            df = df.rename(columns={"rainfall_mm": "rainfall"})
            required_cols.append("rainfall")
            
        if "temperature" in df.columns:
            required_cols.append("temperature")
        elif "temperature_c" in df.columns:
            df = df.rename(columns={"temperature_c": "temperature"})
            required_cols.append("temperature")

        # Create lag features
        for lag in range(1, window + 1):
            for col in required_cols:
                df[f"{col}_lag_{lag}"] = df[col].shift(lag)
        
        # Create target
        df["target_soil_moisture_next_day"] = df[moisture_col].shift(-1)
        self.target_column = "target_soil_moisture_next_day"
        
        # Drop rows with NaN from shifting
        df = df.dropna().reset_index(drop=True)
        return df

    def _scale_features(self, X: np.ndarray) -> np.ndarray:
        """Apply feature scaling."""
        if self.scaler_type == "standard":
            self.scaler = StandardScaler()
        elif self.scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaler type: {self.scaler_type}")

        X_scaled = self.scaler.fit_transform(X)
        logger.info("Features scaled using %s", self.scaler_type)
        return X_scaled

    def _generate_report(
        self,
        df: pd.DataFrame,
        original_shape: tuple,
        outliers_removed: int,
        feature_cols: List[str],
        X_train: np.ndarray,
        X_val: np.ndarray,
        X_test: np.ndarray,
    ) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        report = {
            "original_shape": list(original_shape),
            "final_shape": list(df.shape),
            "outliers_removed": outliers_removed,
            "feature_count": len(feature_cols),
            "features": feature_cols,
            "target_column": self.target_column,
            "split_sizes": {
                "train": len(X_train),
                "validation": len(X_val),
                "test": len(X_test),
            },
            "scaler_type": self.scaler_type,
            "column_mapping": self.column_mapping,
            "encoded_columns": list(self.label_encoders.keys()),
            "target_statistics": {
                "mean": float(df[self.target_column].mean()),
                "std": float(df[self.target_column].std()),
                "min": float(df[self.target_column].min()),
                "max": float(df[self.target_column].max()),
                "median": float(df[self.target_column].median()),
            },
            "feature_statistics": {},
        }

        for col in feature_cols[:10]:  # Top 10 features
            if col in df.columns and df[col].dtype in ("float64", "int64"):
                report["feature_statistics"][col] = {
                    "mean": round(float(df[col].mean()), 4),
                    "std": round(float(df[col].std()), 4),
                    "min": round(float(df[col].min()), 4),
                    "max": round(float(df[col].max()), 4),
                }

        logger.info("Validation report generated")
        return report

    def save_report(self, output_path: str) -> None:
        """Save the validation report to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.validation_report, f, indent=2)
        logger.info("Validation report saved to: %s", output_path)
