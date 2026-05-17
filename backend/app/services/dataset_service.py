"""
Service — Dataset Operations.

Handles file upload processing, validation, and storage.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from app.core.config import settings
from app.core.logging_config import get_logger
from app.ml.dataset_loader import DatasetLoader

logger = get_logger(__name__)


class DatasetService:
    """Manages dataset upload, validation, and storage."""

    def __init__(self):
        self.upload_dir = Path(settings.dataset_dir) / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.latest_upload: Optional[str] = None

    async def process_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process an uploaded dataset file.

        Saves the file, validates its structure, maps columns,
        and returns a detailed validation report.

        Args:
            file_content: Raw file bytes.
            filename: Original filename.

        Returns:
            Upload processing result dictionary.
        """
        logger.info("Processing upload: %s (%d bytes)", filename, len(file_content))

        # Validate extension
        ext = Path(filename).suffix.lower()
        if ext.lstrip(".") not in settings.allowed_extensions_list:
            raise ValueError(f"Unsupported file type: {ext}. Allowed: {settings.allowed_extensions_list}")

        # Validate size
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(file_content) > max_bytes:
            raise ValueError(f"File too large: {len(file_content)} bytes. Max: {max_bytes} bytes")

        # Save file with timestamp
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = f"{ts}_{filename}"
        file_path = self.upload_dir / safe_name
        file_path.write_bytes(file_content)
        self.latest_upload = str(file_path)

        # Validate and analyze
        try:
            df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)

            loader = DatasetLoader()
            mapped_df = loader._auto_map_columns(df.copy())

            expected_features = [
                "vv_backscatter", "vh_backscatter", "ndvi", "temperature",
                "humidity", "rainfall", "sand_pct", "clay_pct", "silt_pct",
                "soil_moisture",
            ]
            missing = [f for f in expected_features if f not in mapped_df.columns]

            result = {
                "filename": safe_name,
                "file_path": str(file_path),
                "file_size_bytes": len(file_content),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "mapped_columns": loader.column_mapping,
                "missing_features": missing,
                "validation_report": {
                    "null_counts": df.isnull().sum().to_dict(),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "sample_rows": df.head(3).to_dict(orient="records"),
                },
                "message": "Dataset uploaded and validated successfully",
            }

            if missing:
                result["message"] += f". Warning: {len(missing)} expected features not found: {missing}"

            logger.info("Upload processed: %s — %d rows, %d cols", safe_name, len(df), len(df.columns))
            return result

        except Exception as e:
            logger.error("Failed to validate uploaded file: %s", str(e))
            raise ValueError(f"Failed to process file: {str(e)}")

    def get_latest_upload_path(self) -> Optional[str]:
        """Get the path to the most recently uploaded dataset."""
        if self.latest_upload and Path(self.latest_upload).exists():
            return self.latest_upload

        # Find most recent file in uploads directory
        files = sorted(self.upload_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            self.latest_upload = str(files[0])
            return self.latest_upload
        return None


# Singleton
dataset_service = DatasetService()
