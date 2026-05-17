"""
API Endpoint — Dataset Operations.

POST /upload-dataset — Upload and validate a dataset file
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.logging_config import get_logger
from app.schemas.dataset import DatasetUploadResponse
from app.services.dataset_service import dataset_service

logger = get_logger(__name__)
router = APIRouter(tags=["Dataset"])


@router.post(
    "/upload-dataset",
    response_model=DatasetUploadResponse,
    summary="Upload Dataset",
    description="Upload a CSV or Excel dataset for model training. "
                "The dataset will be automatically validated, cleaned, and mapped to model features.",
)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload and process a dataset file.

    Accepts CSV and Excel files. The endpoint will:
    1. Validate file type and size
    2. Save the file to the datasets directory
    3. Auto-map columns to expected feature names
    4. Generate a validation report

    The uploaded dataset will be used as the primary data source
    for subsequent model training.
    """
    try:
        content = await file.read()
        result = await dataset_service.process_upload(content, file.filename)
        return DatasetUploadResponse(**result)

    except ValueError as e:
        logger.error("Upload validation failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Upload failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")
