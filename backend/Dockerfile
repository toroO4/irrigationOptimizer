# ============================================================
# SAR Irrigation Scheduling System — Dockerfile
# Multi-stage build for production deployment
# ============================================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (GDAL, PostGIS client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir \
        fastapi uvicorn pydantic pydantic-settings \
        sqlalchemy asyncpg alembic \
        numpy pandas scikit-learn joblib \
        celery redis scipy \
        python-multipart aiofiles orjson \
        structlog python-dotenv \
        pytest httpx pytest-asyncio

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs ml_models datasets/uploads datasets/sample exports

# Generate synthetic dataset
RUN python scripts/generate_synthetic_data.py || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
