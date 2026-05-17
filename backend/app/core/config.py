"""
SAR Irrigation Scheduling System — Application Configuration.

Centralizes all configuration using pydantic-settings.
Values are loaded from environment variables and .env file.
"""

import socket
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Base directory (project root)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings have sensible defaults for local development.
    Override via .env file or environment variables in production.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "SAR Irrigation Scheduling System"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ── Server ───────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = True

    # ── Database ─────────────────────────────────────────────────────────
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "sar_irrigation"
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_url: Optional[str] = None
    database_sync_url: Optional[str] = None

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v, info):
        """Build async database URL if not explicitly provided, with SQLite fallback."""
        if v:
            return v
        data = info.data
        
        host = data.get('database_host', 'localhost')
        port = int(data.get('database_port', 5432))
        
        # Test if Postgres is reachable
        postgres_available = False
        try:
            with socket.create_connection((host, port), timeout=1.0):
                postgres_available = True
        except (OSError, socket.timeout):
            pass
            
        if postgres_available:
            return (
                f"postgresql+asyncpg://{data.get('database_user', 'postgres')}:"
                f"{data.get('database_password', 'postgres')}@"
                f"{host}:{port}/"
                f"{data.get('database_name', 'sar_irrigation')}"
            )
        else:
            print(f"⚠️  PostgreSQL at {host}:{port} is unreachable. Falling back to SQLite.")
            sqlite_db = BASE_DIR / "local_db.sqlite3"
            return f"sqlite+aiosqlite:///{sqlite_db}"

    @field_validator("database_sync_url", mode="before")
    @classmethod
    def assemble_sync_db_url(cls, v, info):
        """Build synchronous database URL for Alembic migrations."""
        if v:
            return v
        data = info.data
        
        host = data.get('database_host', 'localhost')
        port = int(data.get('database_port', 5432))
        
        postgres_available = False
        try:
            with socket.create_connection((host, port), timeout=1.0):
                postgres_available = True
        except (OSError, socket.timeout):
            pass
            
        if postgres_available:
            return (
                f"postgresql://{data.get('database_user', 'postgres')}:"
                f"{data.get('database_password', 'postgres')}@"
                f"{host}:{port}/"
                f"{data.get('database_name', 'sar_irrigation')}"
            )
        else:
            sqlite_db = BASE_DIR / "local_db.sqlite3"
            return f"sqlite:///{sqlite_db}"

    # ── Redis ────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── ML Model ─────────────────────────────────────────────────────────
    model_dir: str = str(BASE_DIR / "ml_models")
    default_model: str = "random_forest"
    model_version: str = "1.0.0"

    # ── SAR Processing ───────────────────────────────────────────────────
    sar_data_dir: str = str(BASE_DIR / "sar_data")
    snap_gpt_path: str = "/usr/local/snap/bin/gpt"
    use_snap: bool = False

    # ── Google Earth Engine ──────────────────────────────────────────────
    gee_enabled: bool = False
    gee_service_account: str = ""
    gee_key_file: str = ""

    # ── Dataset ──────────────────────────────────────────────────────────
    dataset_dir: str = str(BASE_DIR / "datasets")
    max_upload_size_mb: int = 100
    allowed_extensions: str = "csv,xlsx,json,geojson"

    # ── API Security ─────────────────────────────────────────────────────
    api_key_enabled: bool = False
    api_key: str = "change-me-in-production"
    secret_key: str = "super-secret-jwt-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── File Paths ───────────────────────────────────────────────────────
    logs_dir: str = str(BASE_DIR / "logs")
    exports_dir: str = str(BASE_DIR / "exports")

    # ── Convenience Properties ───────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env.lower() == "production"

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions into a list."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]


# ---------------------------------------------------------------------------
# Singleton settings instance
# ---------------------------------------------------------------------------
settings = Settings()
