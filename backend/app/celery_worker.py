import os
import logging

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    from celery.schedules import crontab
    from app.core.config import settings

    # Initialize Celery
    celery_app = Celery(
        "sar_irrigation",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks.ml_tasks", "app.tasks.satellite_tasks"]
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )

    # Configure Celery Beat Schedule
    celery_app.conf.beat_schedule = {
        "fetch-daily-satellite-data": {
            "task": "fetch_satellite_data_task",
            "schedule": crontab(hour=0, minute=0),
        },
    }

    CELERY_AVAILABLE = True

except Exception as e:
    logger.warning("Celery is unavailable (Redis/broker offline): %s. Task queue features disabled.", e)
    CELERY_AVAILABLE = False

    # Create a stub celery_app so imports don't break
    class _StubCelery:
        """Stub Celery app that lets imports succeed when Redis is offline."""
        class task:
            """Decorator stub that returns the function unchanged."""
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, fn):
                fn.delay = lambda *a, **kw: (_ for _ in ()).throw(
                    RuntimeError("Celery broker is not available. Start Redis first.")
                )
                return fn

        def start(self):
            raise RuntimeError("Celery broker is not available.")

    celery_app = _StubCelery()


if __name__ == "__main__":
    celery_app.start()
