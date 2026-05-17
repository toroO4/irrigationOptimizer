"""
SAR Irrigation Scheduling System — FastAPI Application.

Main entry point for the backend server. Configures:
- CORS middleware
- API routing
- Startup/shutdown lifecycle events
- Swagger documentation
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.utils.file_utils import ensure_directories
from app.api.exception_handlers import add_exception_handlers

# Initialize logging before anything else
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.

    Handles startup and shutdown events:
    - Startup: create directories, initialize database, load models
    - Shutdown: close database connections, cleanup resources
    """
    # ── Startup ──────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Environment: %s", settings.app_env)
    logger.info("=" * 60)

    # Create required directories
    ensure_directories()

    # Initialize database
    try:
        from app.database.session import async_engine
        # We don't need init_db since we use Alembic now
        # Just ensure connection can be established
        async with async_engine.begin() as conn:
            pass
        logger.info("Database connection established")
    except Exception as e:
        logger.warning("Database connection failed: %s", str(e))

    logger.info("Application startup complete")
    logger.info("Swagger docs available at: http://%s:%d/docs", settings.host, settings.port)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Shutting down application...")
    try:
        from app.database.session import async_engine
        await async_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning("Database cleanup error: %s", str(e))
    logger.info("Application shutdown complete")


# =====================================================================
# FastAPI Application Instance
# =====================================================================
app = FastAPI(
    title=settings.app_name,
    description=(
        "Intelligent irrigation scheduling system powered by SAR-derived "
        "soil moisture data. Uses Sentinel-1 SAR backscatter analysis, "
        "Machine Learning prediction, and agronomic scheduling logic to "
        "optimize water usage at the farm level.\n\n"
        "## Architecture Layers\n"
        "1. **Data Ingestion** — Sentinel-1 SAR, Sentinel-2 NDVI, Weather, Soil\n"
        "2. **SAR Processing** — Calibration, Speckle Filtering, Moisture Inversion\n"
        "3. **ML Prediction** — Random Forest / LSTM / XGBoost / CNN\n"
        "4. **Scheduling Engine** — Deficit calculation, Pump runtime, Urgency\n"
        "5. **API Outputs** — JSON, CSV, GeoJSON exports"
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# =====================================================================
# CORS Middleware
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Include API Routes
# =====================================================================
app.include_router(api_router, prefix="")

# =====================================================================
# Register Exception Handlers
# =====================================================================
add_exception_handlers(app)


# =====================================================================
# Root Endpoint
# =====================================================================
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — returns API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "POST /upload-dataset",
            "POST /train-model",
            "GET  /predict-moisture",
            "POST /generate-irrigation-plan",
            "GET  /schedule",
            "GET  /history",
            "GET  /soil-map",
            "GET  /health",
            "GET  /metrics",
            "POST /retrain",
        ],
    }
