"""
API Endpoint — Training Operations.

POST /train-model — Train a new ML model
POST /retrain — Retrain the model with latest data
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging_config import get_logger
from app.api.dependencies import get_db
from app.models.model_log import ModelLog
from app.schemas.dataset import RetrainRequest, TrainModelRequest
from app.schemas.tasks import TaskResponse
from app.tasks.ml_tasks import train_model_task, retrain_model_task

logger = get_logger(__name__)
router = APIRouter(tags=["Training", "Models"])


@router.post(
    "/train-model",
    response_model=TaskResponse,
    summary="Train Model",
    description="Trigger a background task to train an ML model on the uploaded dataset. "
                "Supports random_forest, xgboost, lstm, and cnn.",
)
async def train_model(request: TrainModelRequest):
    """
    Train a soil moisture prediction model.

    If no dataset has been uploaded, synthetic data will be
    generated automatically for training.
    """
    try:
        task = train_model_task.delay(
            model_name=request.model_name,
            dataset_path=request.dataset_path,
            target_column=request.target_column,
            test_size=request.test_size,
            tune_hyperparams=request.tune_hyperparams,
        )
        return TaskResponse(task_id=task.id, message=f"Model training task started for {request.model_name}")

    except Exception as e:
        logger.error("Training endpoint error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start training task: {str(e)}")


@router.post(
    "/retrain",
    response_model=TaskResponse,
    summary="Retrain Model",
    description="Trigger a background task to retrain the model using the latest available data.",
)
async def retrain_model(request: RetrainRequest):
    """Retrain the model with the latest dataset."""
    try:
        task = retrain_model_task.delay(model_name=request.model_name)
        return TaskResponse(task_id=task.id, message=f"Model retraining task started for {request.model_name}")
    except Exception as e:
        logger.error("Retrain error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start retraining task: {str(e)}")

@router.get(
    "/models",
    summary="Get Trained Models",
    description="Fetch a list of all trained ML models and their evaluation metrics.",
)
async def get_models(db: AsyncSession = Depends(get_db)):
    """Retrieve training logs for models."""
    try:
        stmt = select(ModelLog).order_by(ModelLog.training_date.desc())
        result = await db.execute(stmt)
        models = result.scalars().all()
        return {"models": models}
    except Exception as e:
        logger.error("Error fetching models: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch models.")
