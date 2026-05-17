"""
Utility — File Operations.

Helper functions for file I/O, path management, and directory setup.
"""

from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    directories = [
        settings.logs_dir,
        settings.model_dir,
        settings.dataset_dir,
        settings.exports_dir,
        str(Path(settings.dataset_dir) / "uploads"),
        str(Path(settings.dataset_dir) / "sample"),
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    logger.info("Required directories created/verified")


def get_dataset_files() -> List[str]:
    """List all dataset files in the uploads directory."""
    upload_dir = Path(settings.dataset_dir) / "uploads"
    if not upload_dir.exists():
        return []
    extensions = settings.allowed_extensions_list
    files = []
    for ext in extensions:
        files.extend(upload_dir.glob(f"*.{ext}"))
    return [str(f) for f in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)]


def get_model_files() -> List[str]:
    """List all saved model files."""
    model_dir = Path(settings.model_dir)
    if not model_dir.exists():
        return []
    files = list(model_dir.glob("*.*"))
    return [str(f) for f in files]
