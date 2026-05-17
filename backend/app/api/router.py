"""
API Router — Aggregates all endpoint routers.
"""

from fastapi import APIRouter, Depends

from app.api.endpoints import dataset, health, history, irrigation, prediction, spatial, training, tasks, auth, iot, farm, weather
from app.core.security import get_current_active_user

# Create the main API router
api_router = APIRouter()

# ── Unprotected Endpoints (Auth & Health, IoT incoming webhooks) ──
api_router.include_router(health.router)
api_router.include_router(auth.router)
# In a real app, IoT endpoints might use a separate API key or device token, 
# but for simplicity we'll keep the ingest unprotected or lightly protected
api_router.include_router(iot.router)
api_router.include_router(weather.router)

# ── Protected Endpoints ──────────────────────────────────────────────
# All routes below require a valid JWT token
protected_deps = [Depends(get_current_active_user)]

api_router.include_router(farm.router, dependencies=protected_deps)

api_router.include_router(dataset.router, dependencies=protected_deps)
api_router.include_router(training.router, dependencies=protected_deps)
api_router.include_router(prediction.router, dependencies=protected_deps)
api_router.include_router(irrigation.router, dependencies=protected_deps)
api_router.include_router(history.router, dependencies=protected_deps)
api_router.include_router(spatial.router, dependencies=protected_deps)
api_router.include_router(tasks.router, dependencies=protected_deps)
