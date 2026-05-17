import asyncio
from typing import Dict, Any

from app.celery_worker import celery_app
from app.services.training_service import training_service
from app.services.prediction_service import prediction_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def _run_async(coro):
    """Run an async coroutine in a synchronous Celery task."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@celery_app.task(bind=True, name="ml_tasks.train_model")
def train_model_task(self, model_name: str, dataset_path: str = None, target_column: str = "soil_moisture", test_size: float = 0.2, tune_hyperparams: bool = False) -> Dict[str, Any]:
    """Background task to train an ML model."""
    logger.info(f"Starting background training task for {model_name}")
    try:
        # We need to run the async training service synchronously
        result = _run_async(training_service.train_model(
            model_name=model_name,
            dataset_path=dataset_path,
            target_column=target_column,
            test_size=test_size,
            tune_hyperparams=tune_hyperparams,
        ))
        logger.info(f"Background training task for {model_name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in background training task: {e}")
        self.update_state(state="FAILURE", meta={"exc_type": type(e).__name__, "exc_message": str(e)})
        raise

@celery_app.task(bind=True, name="ml_tasks.retrain_model")
def retrain_model_task(self, model_name: str) -> Dict[str, Any]:
    """Background task to retrain an ML model with latest data."""
    logger.info(f"Starting background retraining task for {model_name}")
    try:
        result = _run_async(training_service.retrain(model_name=model_name))
        logger.info(f"Background retraining task for {model_name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in background retraining task: {e}")
        self.update_state(state="FAILURE", meta={"exc_type": type(e).__name__, "exc_message": str(e)})
        raise
