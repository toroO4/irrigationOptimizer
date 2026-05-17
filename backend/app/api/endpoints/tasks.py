from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.celery_worker import celery_app
from app.schemas.tasks import TaskStatusResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Background Tasks"], prefix="/tasks")

@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get Task Status",
    description="Poll the status of a background task using its ID."
)
async def get_task_status(task_id: str):
    """Retrieve the status and result of a Celery task."""
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
            "error": None
        }

        if task_result.state == 'SUCCESS':
            response["result"] = task_result.result
        elif task_result.state == 'FAILURE':
            # task_result.result is the Exception instance
            response["error"] = str(task_result.result)

        return response
    except Exception as e:
        logger.error(f"Error retrieving task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve task status: {e}")
