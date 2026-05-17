"""
API Dependencies — Dependency injection for FastAPI endpoints.
"""

from app.database.session import get_db  # noqa: F401
from app.core.security import verify_api_key  # noqa: F401
